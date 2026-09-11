# -*- coding: utf-8 -*-
"""Router de modelos con cascada para el Radar: UNA sola puerta de salida a los LLM.

Todas las llamadas del pipeline pasan por `llm(tarea, prompt, esquema=None)`, que resuelve tres cosas
que antes estaban desparramadas: que modelo le toca a esa tarea, EN QUE FORMATO DE API hablarle, y a
quien caer si falla.

Los tres formatos (RADAR.md 11bis, verificado en opencode.ai/docs/go). OpenCode Go NO expone una sola
API: expone tres, y cambiar de Luna a Kimi no es cambiar un nombre, es cambiar la forma del request.
  responses -> /zen/go/v1/responses          gpt-5.6-luna, grok-4.6
  chat      -> /zen/go/v1/chat/completions   glm-5.3-flash, glm-5.3, kimi-k3, deepseek-v4-*
  messages  -> /zen/go/v1/messages           qwen3.8-flash, minimax-*
El fallback "claude" habla el formato messages de Anthropic, pero por el sdk `anthropic`, no por HTTP.
Los tres adaptadores viven en ADAPTADORES: agregar un modelo es agregar una fila en FORMATO, no un if.

POR QUE 'masivas' NO TIENE RED A CLAUDE. Es la regla mas importante del modulo y la que se rompe en
silencio si se toca. La etapa masiva son ~100 extracciones por dia. Cien llamadas diarias escalando al
plan de Claude es exactamente como se va la cuenta sin que nadie lo note: no falla nada, no avisa nadie,
y la factura aparece a fin de mes. Por eso RUTAS['masivas'] termina en los dos Flash y, si los dos se
agotan, este modulo levanta CuotaAgotada. El llamador DEGRADA: procesa solo los N eventos mas
importantes y marca el resto como pendientes. Un dia con menos eventos analizados es mucho mejor que
una factura sorpresa. El guardarrail es doble: la ruta no tiene a Claude, y ademas SIN_RED_CLAUDE hace
que, si alguien agrega ('claude', None) a esa ruta, el proveedor se saltee igual.

Cuando baja de modelo: 429, cuota agotada, timeout, 5xx, credencial rechazada, respuesta vacia, o
agotar los reintentos de validacion contra el esquema. Entre reintentos de esquema espera creciente
(ESPERA_BASE * 2**intento) y le mete el error de validacion adentro del prompt.

Trazabilidad: `ultimo_modelo()` devuelve 'proveedor/modelo' del que sirvio la ultima llamada, y
`ultimo_detalle()` el dict completo (intentos, caidas, ms) para que el llamador lo deje en run_log.
Sin eso no hay forma de darse cuenta de que hace tres semanas todo viene saliendo por la red de
emergencia.

Claves por entorno: OPENCODE_API_KEY y ANTHROPIC_API_KEY. Si faltan, el error es AL LLAMAR
(FaltaClave), nunca al importar: importar este modulo no toca la red ni el entorno.

Dependencias: stdlib + httpx + jsonschema + anthropic (este ultimo se importa tarde, solo si hace
falta caer en la red de emergencia). Ninguna dependencia nueva.

Autotest: `python radar/llm.py --autotest` (o `python -m radar.llm --autotest`). No gasta un centavo
ni pide claves: reemplaza el transporte HTTP y la llamada a Claude por dobles de prueba.
"""
import json, os, re, sys, time

import httpx
import jsonschema

# ---------------------------------------------------------------- tablas (todo es dato, no codigo)

BASE_OPENCODE = "https://opencode.ai/zen/go/v1"

# Cualquier proveedor compatible con OpenAI entra como UNA FILA de esta tabla. No hace falta
# tocar codigo: el adaptador "chat" ya sabe hablar ese dialecto.
# `clave_env` es la variable de entorno donde vive la credencial; si falta, ese proveedor se
# saltea y la cascada sigue al siguiente. Asi se puede tener tres configurados y usar el que haya.
PROVEEDORES = {
    "openrouter": {"base": "https://openrouter.ai/api/v1", "clave_env": "OPENROUTER_API_KEY",
                   "formato": "chat",
                   "cabeceras": {"HTTP-Referer": "https://github.com/agusoler000/paper-trail-geo",
                                 "X-Title": "Paper Trail"}},
    "gemini":     {"base": "https://generativelanguage.googleapis.com/v1beta/openai",
                   "clave_env": "GEMINI_API_KEY", "formato": "chat", "cabeceras": {}},
    "groq":       {"base": "https://api.groq.com/openai/v1", "clave_env": "GROQ_API_KEY",
                   "formato": "chat", "cabeceras": {}},
    "cerebras":   {"base": "https://api.cerebras.ai/v1", "clave_env": "CEREBRAS_API_KEY",
                   "formato": "chat", "cabeceras": {}},
    "together":   {"base": "https://api.together.xyz/v1", "clave_env": "TOGETHER_API_KEY",
                   "formato": "chat", "cabeceras": {}},
    "mistral":    {"base": "https://api.mistral.ai/v1", "clave_env": "MISTRAL_API_KEY",
                   "formato": "chat", "cabeceras": {}},
    "local":      {"base": os.environ.get("LOCAL_BASE_URL", "http://127.0.0.1:11434/v1"),
                   "clave_env": None, "formato": "chat", "cabeceras": {}},
}

RUTAS = {
    # Investigado y verificado el 2026-09-11 (RADAR.md 11ter). El orden NO es por calidad: es por
    # que se agota primero. OpenCode va primero porque ya esta pago; despues lo gratis de verdad.
    #
    # PRIVACIDAD, que decide el orden de "guion": tanto el tier gratis de Gemini como el free mode
    # de Mistral ENTRENAN con lo que les mandas. Mistral deja desactivarlo (Admin Console >
    # Privacy); el tier gratis de Google NO, y sus terminos dicen que revisores humanos pueden leer
    # la entrada y la salida. La etapa "guion" es la unica que manda ESTILO.md e IDEOLOGIA.md, asi
    # que ahi va Mistral primero. Las otras etapas solo mandan titulares publicos: da igual.
    "masivas":       [("opencode", "glm-5.3-flash"),
                      ("opencode", "deepseek-v4-flash"),
                      ("gemini", "gemini-3.8-flash"),
                      ("mistral", "mistral-small-2603"),
                      ("openrouter", "nex-agi/nex-n2.5-mini:free")],          # SIN red a Claude
    "analisis":      [("opencode", "kimi-k3"),
                      ("opencode", "glm-5.3"),
                      ("gemini", "gemini-3.8-flash"),
                      ("mistral", "mistral-small-2603"),
                      ("claude", None)],
    "guion":         [("opencode", "gpt-5.6-luna"),
                      ("opencode", "kimi-k3"),
                      ("mistral", "mistral-medium"),
                      ("gemini", "gemini-3.8-flash"),
                      ("claude", None)],
    "investigacion": [("opencode", "grok-4.6"),
                      ("gemini", "gemini-3.8-flash"),
                      ("claude", None)],
}

# OpenRouter necesita esto o el router te manda a un endpoint que no soporta el esquema y la
# llamada FALLA (no degrada). Solo 5 de sus 19 modelos gratis soportan structured_outputs.
EXTRA_CUERPO = {
    "openrouter": {"provider": {"require_parameters": True}},
}

FORMATO = {  # tres formas de API distintas, verificado en opencode.ai/docs/go
    "gpt-5.6-luna": "responses", "grok-4.6": "responses",
    "glm-5.3-flash": "chat", "glm-5.3": "chat", "kimi-k3": "chat",
    "deepseek-v4-flash": "chat", "deepseek-v4-pro": "chat",
    "qwen3.8-flash": "messages", "minimax-m2": "messages",
    # proveedores compatibles con OpenAI: todos hablan "chat"
    "gemini-3.8-flash": "chat", "gemini-3.5-flash": "chat", "gemini-3.5-flash-lite": "chat",
    "mistral-small-2603": "chat", "mistral-medium": "chat", "mistral-large-2425-12": "chat",
    "nex-agi/nex-n2.5-mini:free": "chat", "nex-agi/nex-n2.5-pro:free": "chat",
    "nvidia/nemotron-3-super-120b-a12b:free": "chat",
}

# Tareas que NUNCA escalan a Claude, pase lo que pase con RUTAS (ver docstring).
SIN_RED_CLAUDE = {"masivas"}

CLAVE = {"opencode": "OPENCODE_API_KEY", "claude": "ANTHROPIC_API_KEY"}


def clave_de(proveedor):
    """Que variable de entorno necesita cada proveedor. None = ninguna (el modelo local)."""
    if proveedor in CLAVE:
        return CLAVE[proveedor]
    return (PROVEEDORES.get(proveedor) or {}).get("clave_env")

MODELO_CLAUDE = "claude-opus-5"   # el fallback del VPS; ('claude', None) en RUTAS usa este
MAX_TOKENS = 16000
TIMEOUT = 90.0
ESPERA_BASE = 1.5                 # segundos; el reintento n espera ESPERA_BASE * 2**n


class CuotaAgotada(RuntimeError):
    """Se agoto la cascada entera de la tarea. En 'masivas' significa DEGRADAR, no reintentar."""


class FaltaClave(RuntimeError):
    """No hay ninguna clave de entorno util para esta tarea. Se levanta al llamar, no al importar."""


class _Bajar(Exception):
    """Interna: este modelo no sirvio (red, cuota, 5xx, credencial). El router pasa al siguiente."""


# ---------------------------------------------------------------- adaptadores de los tres formatos

def _armar_responses(modelo, sistema, prompt, esquema):
    """POST /responses - el formato nuevo de OpenAI: `instructions` + `input` plano."""
    cuerpo = {"model": modelo, "input": prompt, "max_output_tokens": MAX_TOKENS}
    if sistema:
        cuerpo["instructions"] = sistema
    if esquema:
        cuerpo["text"] = {"format": {"type": "json_schema", "name": "salida", "schema": esquema}}
    return cuerpo


def _leer_responses(datos):
    texto = datos.get("output_text")
    if isinstance(texto, str) and texto.strip():
        return texto
    partes = []
    for bloque in datos.get("output") or []:
        for c in bloque.get("content") or []:
            if c.get("type") in ("output_text", "text") and c.get("text"):
                partes.append(c["text"])
    return "\n".join(partes)


def _armar_chat(modelo, sistema, prompt, esquema):
    """POST /chat/completions - el clasico: lista de mensajes con roles."""
    mensajes = []
    if sistema:
        mensajes.append({"role": "system", "content": sistema})
    mensajes.append({"role": "user", "content": prompt})
    cuerpo = {"model": modelo, "messages": mensajes, "max_tokens": MAX_TOKENS}
    if esquema:
        cuerpo["response_format"] = {"type": "json_schema",
                                     "json_schema": {"name": "salida", "schema": esquema, "strict": False}}
    return cuerpo


def _leer_chat(datos):
    opciones = datos.get("choices") or [{}]
    mensaje = opciones[0].get("message") or {}
    contenido = mensaje.get("content")
    if isinstance(contenido, list):   # algunos devuelven bloques en vez de string
        return "".join(p.get("text", "") for p in contenido)
    return contenido or opciones[0].get("text") or ""


def _armar_messages(modelo, sistema, prompt, esquema):
    """POST /messages - el formato de Anthropic: `system` aparte y contenido en bloques.
       No tiene response_format; el esquema viaja dentro del prompt (ver _con_esquema)."""
    cuerpo = {"model": modelo, "max_tokens": MAX_TOKENS,
              "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}]}
    if sistema:
        cuerpo["system"] = sistema
    return cuerpo


def _leer_messages(datos):
    return "".join(b.get("text", "") for b in (datos.get("content") or []) if b.get("type") == "text")


ADAPTADORES = {
    "responses": {"ruta": "/responses", "armar": _armar_responses, "leer": _leer_responses,
                  "cabeceras": {}},
    "chat":      {"ruta": "/chat/completions", "armar": _armar_chat, "leer": _leer_chat,
                  "cabeceras": {}},
    "messages":  {"ruta": "/messages", "armar": _armar_messages, "leer": _leer_messages,
                  "cabeceras": {"anthropic-version": "2023-06-01"}},
}


# ---------------------------------------------------------------- transporte (el autotest lo parcha)

def _post(url, cabeceras, cuerpo, timeout):
    """Unico punto de salida HTTP. Devuelve (status, datos). El autotest reemplaza esta funcion."""
    try:
        r = httpx.post(url, headers=cabeceras, json=cuerpo, timeout=timeout)
    except Exception as e:
        raise _Bajar("red: %s" % _corto(e))
    try:
        datos = r.json()
    except Exception:
        datos = {"_texto": (r.text or "")[:400]}
    return r.status_code, datos


def _dormir(segundos):
    """Espera entre reintentos. Aparte para que el autotest la mida sin dormir de verdad."""
    time.sleep(segundos)


def _pedir_opencode(modelo, sistema, prompt, esquema, timeout):
    forma = FORMATO.get(modelo)
    if forma is None:
        raise _Bajar("modelo sin formato declarado en FORMATO")
    ad = ADAPTADORES[forma]
    clave = os.environ.get(CLAVE["opencode"], "").strip()
    if not clave:
        raise _Bajar("falta OPENCODE_API_KEY")
    cabeceras = {"Authorization": "Bearer " + clave, "Content-Type": "application/json"}
    cabeceras.update(ad["cabeceras"])
    estado, datos = _post(BASE_OPENCODE + ad["ruta"], cabeceras,
                          ad["armar"](modelo, sistema, prompt, esquema), timeout)
    if estado == 429:
        raise _Bajar("429 tope de cuota o de ritmo")
    if estado in (401, 403):
        raise _Bajar("%d credencial rechazada" % estado)
    if estado == 402:
        raise _Bajar("402 cuota agotada")
    if estado >= 500:
        raise _Bajar("%d error del proveedor" % estado)
    if estado >= 400:
        raise _Bajar("%d %s" % (estado, _mensaje_error(datos)))
    texto = ad["leer"](datos) or ""
    if not texto.strip():
        raise _Bajar("respuesta vacia")
    return texto


def _llamar_claude(sistema, prompt, timeout):
    """Red de emergencia: el Claude del VPS por el sdk anthropic. El autotest reemplaza esta funcion
       y cuenta las veces que se la llama (que en 'masivas' tiene que ser cero)."""
    clave = os.environ.get(CLAVE["claude"], "").strip()
    if not clave:
        raise _Bajar("falta ANTHROPIC_API_KEY")
    try:
        import anthropic
    except Exception as e:
        raise _Bajar("sdk anthropic no disponible: %s" % _corto(e))
    try:
        cliente = anthropic.Anthropic(api_key=clave, timeout=timeout, max_retries=0)
        kw = {"model": MODELO_CLAUDE, "max_tokens": MAX_TOKENS,
              "messages": [{"role": "user", "content": prompt}]}
        if sistema:
            kw["system"] = sistema
        r = cliente.messages.create(**kw)
    except Exception as e:
        raise _Bajar(_clasificar_anthropic(e))
    texto = "".join(getattr(b, "text", "") for b in (getattr(r, "content", None) or [])
                    if getattr(b, "type", "") == "text")
    if not texto.strip():
        raise _Bajar("claude devolvio vacio (stop_reason=%s)" % getattr(r, "stop_reason", "?"))
    return texto


def _clasificar_anthropic(e):
    """Traduce una excepcion del sdk a un motivo corto, sin depender de sus clases (el autotest
       inyecta dobles): mira status_code si esta, y si no el nombre de la clase."""
    estado = getattr(e, "status_code", None)
    if estado is None:
        estado = getattr(getattr(e, "response", None), "status_code", None)
    nombre = type(e).__name__
    if estado == 429 or "RateLimit" in nombre:
        return "429 tope de Claude"
    if estado and estado >= 500:
        return "%d error de Claude" % estado
    if "Timeout" in nombre or "Connection" in nombre:
        return "timeout o red hacia Claude"
    if estado:
        return "%d %s" % (estado, _corto(e))
    return "%s: %s" % (nombre, _corto(e))


def _pedir_compatible(proveedor, modelo, sistema, prompt, esquema, timeout):
    """Cualquier proveedor de PROVEEDORES. Todos hablan el dialecto de OpenAI."""
    cfg = PROVEEDORES[proveedor]
    ad = ADAPTADORES[cfg["formato"]]
    cabeceras = {"Content-Type": "application/json"}
    cabeceras.update(ad["cabeceras"])
    cabeceras.update(cfg.get("cabeceras") or {})
    if cfg["clave_env"]:
        clave = os.environ.get(cfg["clave_env"], "").strip()
        if not clave:
            # No es un error: es "este proveedor no esta configurado". La cascada sigue.
            raise _Bajar("falta %s" % cfg["clave_env"])
        cabeceras["Authorization"] = "Bearer " + clave
    cuerpo = ad["armar"](modelo, sistema, prompt, esquema)
    cuerpo.update(EXTRA_CUERPO.get(proveedor, {}))
    estado, datos = _post(cfg["base"] + ad["ruta"], cabeceras, cuerpo, timeout)
    if estado == 429:
        raise _Bajar("429 tope de cuota o de ritmo")
    if estado in (401, 403):
        raise _Bajar("%d credencial rechazada" % estado)
    if estado == 402:
        raise _Bajar("402 cuota agotada")
    if estado >= 500:
        raise _Bajar("%d error del proveedor" % estado)
    if estado >= 400:
        raise _Bajar("%d %s" % (estado, _mensaje_error(datos)))
    texto = ad["leer"](datos) or ""
    if not texto.strip():
        raise _Bajar("respuesta vacia")
    return texto


def _pedir(proveedor, modelo, sistema, prompt, esquema, timeout):
    if proveedor == "claude":
        return _llamar_claude(sistema, prompt, timeout)
    if proveedor == "opencode":
        return _pedir_opencode(modelo, sistema, prompt, esquema, timeout)
    if proveedor in PROVEEDORES:
        return _pedir_compatible(proveedor, modelo, sistema, prompt, esquema, timeout)
    raise _Bajar("proveedor desconocido: %r" % (proveedor,))


# ---------------------------------------------------------------- esquema: pedirlo y validarlo

def _con_esquema(prompt, esquema):
    """El esquema viaja SIEMPRE tambien dentro del prompt: los tres formatos no lo soportan igual
       (messages no tiene response_format) y los Flash rompen JSON si no se les insiste."""
    if not esquema:
        return prompt
    return ("%s\n\n--- FORMATO DE SALIDA ---\nRespondes UNICAMENTE con un JSON valido que cumpla este "
            "JSON Schema. Sin explicaciones, sin ``` y sin texto antes ni despues.\n%s"
            % (prompt, json.dumps(esquema, ensure_ascii=False, sort_keys=True)))


def _con_error(prompt, error):
    return ("%s\n\n--- CORRECCION ---\nTu respuesta anterior no sirvio: %s\nDevolve SOLO el JSON "
            "corregido, sin texto alrededor." % (prompt, error))


def _extraer_json(texto):
    """Saca el JSON de una respuesta que puede venir con ``` o con prosa ADELANTE Y ATRAS.

    Los modelos cierran con cortesias ("espero que te sirva") tanto como las abren. Recortar solo
    lo de adelante hacia que cada cortesia final costara un reintento completo y, al agotarlos, una
    bajada de modelo: plata tirada por una frase. `raw_decode` corta exacto donde termina el primer
    valor JSON, asi que no depende de contar llaves.
    """
    t = (texto or "").strip()
    m = re.search(r"```(?:json)?\s*(.+?)\s*```", t, re.S)
    if m:
        t = m.group(1).strip()
    arranques = [p for p in (t.find("{"), t.find("[")) if p >= 0]
    if not arranques:
        return t
    i = min(arranques)
    try:
        _dato, fin = json.JSONDecoder().raw_decode(t[i:])
        return t[i:i + fin]
    except ValueError:
        pass
    j = max(t.rfind("}"), t.rfind("]"))   # ultimo recurso: del primer abre al ultimo cierra
    return t[i:j + 1] if i < j else t


def _validar(texto, esquema):
    """-> (dato, None) si valida; (None, motivo) si no. El motivo se le devuelve al modelo."""
    try:
        dato = json.loads(_extraer_json(texto))
    except Exception as e:
        return None, "no es JSON (%s)" % _corto(e)
    try:
        jsonschema.validate(dato, esquema)
    except jsonschema.ValidationError as e:
        donde = "/".join(str(x) for x in e.absolute_path) or "raiz"
        return None, "no cumple el esquema en '%s': %s" % (donde, _corto(e.message))
    except jsonschema.SchemaError as e:
        return None, "el esquema esta mal escrito: %s" % _corto(e)
    return dato, None


# ---------------------------------------------------------------- quien sirvio la ultima llamada

_ULTIMO = {"modelo": "", "tarea": "", "intentos": 0, "caidas": [], "ms": 0, "ok": False}


def ultimo_modelo():
    """'proveedor/modelo' del que sirvio la ultima llamada. '' si la ultima fracaso o no hubo."""
    return _ULTIMO["modelo"]


def ultimo_detalle():
    """Dict completo de la ultima llamada, para run_log: modelo, tarea, intentos, caidas, ms, ok."""
    return dict(_ULTIMO)


def _anotar(modelo, tarea, intentos, caidas, t0, ok):
    _ULTIMO.update({"modelo": modelo if ok else "", "tarea": tarea, "intentos": intentos,
                    "caidas": list(caidas), "ms": int((time.time() - t0) * 1000), "ok": ok})


# ---------------------------------------------------------------- la funcion

def llm(tarea, prompt, esquema=None, sistema=None, max_reintentos=2, timeout=TIMEOUT):
    """Recorre RUTAS[tarea] y devuelve el texto (str) o, con `esquema`, el dato ya validado (dict/list).

    Con `esquema` valida con jsonschema; si no valida, reintenta hasta `max_reintentos` metiendole el
    error al prompt, y recien al agotarlos BAJA al siguiente modelo. Baja de una ante 429, cuota
    agotada, timeout, 5xx o credencial rechazada. Si se agota la cascada levanta CuotaAgotada.
    'masivas' no escala a Claude a proposito (ver docstring del modulo): ahi CuotaAgotada significa
    DEGRADAR a los N eventos mas importantes.
    Un `esquema` mal escrito levanta ValueError ANTES de salir a la red: es un bug nuestro, no una
    cuota agotada, y quemar la cascada entera contra el no lo iba a arreglar.
    Deja siempre en ultimo_modelo()/ultimo_detalle() por donde salio, para el run_log; si la llamada
    se corta antes de salir, quedan vacios (nunca con los restos de la llamada anterior).
    """
    t0 = time.time()
    # Trazabilidad sin restos: si esta llamada se corta antes de salir a la red (tarea mala, esquema
    # roto, falta de clave), ultimo_modelo() no puede quedar mintiendo con el de la llamada anterior.
    _anotar("", tarea, 0, [], t0, False)

    ruta = RUTAS.get(tarea)
    if not ruta:
        raise ValueError("tarea desconocida: %r (hay: %s)" % (tarea, ", ".join(sorted(RUTAS))))
    if not esquema:
        esquema = None          # {} es "cualquier cosa": lo tratamos como sin esquema, que es lo que
                                # ya asumen _con_esquema y _armar_chat al mirar la verdad del dict
    if esquema is not None:
        # Un esquema mal escrito no lo arregla ningun modelo: sin este corte se iba la cascada entera
        # (3 intentos por modelo, Claude incluido) contra un bug nuestro, y encima terminaba en
        # CuotaAgotada, que en 'masivas' le dice al llamador que DEGRADE cuando no hay nada agotado.
        try:
            jsonschema.validators.validator_for(esquema).check_schema(esquema)
        except jsonschema.SchemaError as e:
            raise ValueError("esquema mal escrito, ninguna respuesta lo iba a cumplir: %s" % _corto(e))
    # Un proveedor sin clave no es un error: es "no esta configurado", y la cascada lo saltea.
    # Asi se pueden tener tres puestos y usar el que tenga cuota ese dia, sin tocar codigo.
    utiles = [p for p, _m in ruta
              if clave_de(p) is None or os.environ.get(clave_de(p), "").strip()]
    if not utiles:
        faltan = sorted({clave_de(p) for p, _m in ruta if clave_de(p)})
        raise FaltaClave("tarea '%s': no hay ninguna clave en el entorno (falta %s)"
                         % (tarea, " y ".join(faltan)))

    caidas, intentos = [], 0
    for proveedor, modelo in ruta:
        etiqueta = "%s/%s" % (proveedor, modelo or MODELO_CLAUDE)
        if proveedor == "claude" and tarea in SIN_RED_CLAUDE:
            caidas.append((etiqueta, "saltado: '%s' no escala a Claude a proposito" % tarea))
            continue
        error_previo = None
        for reintento in range(max_reintentos + 1):
            intentos += 1
            texto_prompt = _con_esquema(prompt, esquema)
            if error_previo is not None:
                texto_prompt = _con_error(texto_prompt, error_previo)
            try:
                salida = _pedir(proveedor, modelo, sistema, texto_prompt, esquema, timeout)
            except _Bajar as e:
                caidas.append((etiqueta, str(e)))
                break                      # transporte o cuota: no se reintenta, se baja de modelo
            if esquema is None:
                _anotar(etiqueta, tarea, intentos, caidas, t0, True)
                return salida
            dato, error_previo = _validar(salida, esquema)
            if error_previo is None:
                _anotar(etiqueta, tarea, intentos, caidas, t0, True)
                return dato
            caidas.append((etiqueta, "json invalido: %s" % error_previo))
            if reintento < max_reintentos:
                _dormir(ESPERA_BASE * (2 ** reintento))

    _anotar("", tarea, intentos, caidas, t0, False)
    pista = ("la etapa masiva DEGRADA: procesa solo los N eventos mas importantes y marca el resto "
             "como pendientes" if tarea in SIN_RED_CLAUDE else "no queda modelo en la cascada")
    raise CuotaAgotada("tarea '%s': se agoto la cascada. %s. Caidas: %s"
                       % (tarea, pista, " | ".join("%s -> %s" % c for c in caidas) or "ninguna"))


# ---------------------------------------------------------------- utilidades chicas

def _corto(x, n=160):
    s = str(x).replace("\n", " ").strip()
    return s if len(s) <= n else s[:n - 3] + "..."


def _mensaje_error(datos):
    if isinstance(datos, dict):
        err = datos.get("error")
        if isinstance(err, dict):
            return _corto(err.get("message") or err)
        if err:
            return _corto(err)
        if datos.get("_texto"):
            return _corto(datos["_texto"])
    return _corto(datos)


# ---------------------------------------------------------------- autotest (no toca la red)

_FALLAS = []


def _ok(cond, msg):
    print(("OK:    " if cond else "FALLA: ") + msg)
    if not cond:
        _FALLAS.append(msg)
    return bool(cond)


def _parchar(**kw):
    """Reemplaza globals del modulo y devuelve los previos para restaurar."""
    previos = {k: globals()[k] for k in kw}
    globals().update(kw)
    return previos


def _cuerpo_respuesta(modelo, texto):
    """Arma una respuesta creible en el formato que le toca a ese modelo."""
    forma = FORMATO[modelo]
    if forma == "responses":
        return {"output_text": texto}
    if forma == "chat":
        return {"choices": [{"message": {"role": "assistant", "content": texto}}]}
    return {"content": [{"type": "text", "text": texto}]}


class _Transporte:
    """Transporte falso: guion por modelo (lista de (status, texto_o_datos), el ultimo se repite)."""

    def __init__(self, guion):
        self.guion = guion
        self.pedidos = []

    def post(self, url, cabeceras, cuerpo, timeout):
        modelo = cuerpo.get("model")
        self.pedidos.append({"url": url, "cab": cabeceras, "cuerpo": cuerpo, "modelo": modelo})
        pasos = self.guion.get(modelo)
        if not pasos:
            return 404, {"error": {"message": "modelo no guionado: %s" % modelo}}
        n = sum(1 for p in self.pedidos if p["modelo"] == modelo) - 1
        estado, carga = pasos[min(n, len(pasos) - 1)]
        if isinstance(carga, str):
            carga = _cuerpo_respuesta(modelo, carga)
        return estado, carga

    def cuantos(self, modelo):
        return sum(1 for p in self.pedidos if p["modelo"] == modelo)

    def ultimo(self, modelo):
        for p in reversed(self.pedidos):
            if p["modelo"] == modelo:
                return p
        return None


class _ClaudeFalso:
    """Doble de la red de emergencia. Cuenta llamadas: en 'masivas' TIENE que quedar en cero."""

    def __init__(self, texto="respuesta de claude", explota=None):
        self.n = 0
        self.texto = texto
        self.explota = explota

    def __call__(self, sistema, prompt, timeout):
        self.n += 1
        if self.explota:
            raise _Bajar(self.explota)
        return self.texto


ESQUEMA_PRUEBA = {"type": "object", "properties": {"tipo": {"enum": ["fact", "claim"]},
                                                   "texto": {"type": "string"}},
                  "required": ["tipo", "texto"], "additionalProperties": False}
BUEN_JSON = '{"tipo": "fact", "texto": "la comision publico el paquete 19"}'


def _autotest():
    del _FALLAS[:]
    print("--- radar/llm.py --autotest (transporte falso: no toca la red ni gasta creditos) ---")
    previo_env = {k: os.environ.get(k) for k in ("OPENCODE_API_KEY", "ANTHROPIC_API_KEY")}
    esperas = []
    previos = {k: globals()[k] for k in ("_post", "_dormir", "_llamar_claude")}
    _parchar(_dormir=lambda s: esperas.append(round(s, 3)))
    try:
        # (0) las claves faltan -> error claro AL LLAMAR, no al importar
        for k in previo_env:
            os.environ.pop(k, None)
        try:
            llm("analisis", "hola")
            _ok(False, "sin claves deberia levantar FaltaClave")
        except FaltaClave as e:
            _ok("OPENCODE_API_KEY" in str(e) and "ANTHROPIC_API_KEY" in str(e),
                "sin claves levanta FaltaClave y nombra las dos variables")
        except Exception as e:
            _ok(False, "sin claves levanto %s en vez de FaltaClave" % type(e).__name__)
        os.environ["OPENCODE_API_KEY"] = "prueba-opencode"
        os.environ["ANTHROPIC_API_KEY"] = "prueba-anthropic"

        _ok(ultimo_modelo() == "", "ultimo_modelo() arranca vacio")
        try:
            llm("inexistente", "x")
            _ok(False, "una tarea desconocida deberia levantar ValueError")
        except ValueError:
            _ok(True, "una tarea desconocida levanta ValueError")

        # (a) los tres formatos: cada modelo arma SU request
        t = _Transporte({"gpt-5.6-luna": [(200, "texto del guion")]})
        _parchar(_post=t.post)
        salida = llm("guion", "escribi el cold open", sistema="sos el editor")
        p = t.ultimo("gpt-5.6-luna")
        _ok(salida == "texto del guion" and p["url"] == BASE_OPENCODE + "/responses"
            and "input" in p["cuerpo"] and p["cuerpo"].get("instructions") == "sos el editor"
            and "messages" not in p["cuerpo"],
            "formato 'responses' (gpt-5.6-luna): /responses con input + instructions")

        t = _Transporte({"glm-5.3-flash": [(200, "clasificado")]})
        _parchar(_post=t.post)
        llm("masivas", "clasifica esto", sistema="sos el extractor")
        p = t.ultimo("glm-5.3-flash")
        msgs = p["cuerpo"].get("messages") or []
        _ok(p["url"] == BASE_OPENCODE + "/chat/completions" and len(msgs) == 2
            and msgs[0]["role"] == "system" and msgs[1]["role"] == "user"
            and p["cab"]["Authorization"] == "Bearer prueba-opencode",
            "formato 'chat' (glm-5.3-flash): /chat/completions con roles system+user")

        t = _Transporte({"qwen3.8-flash": [(200, "en bloques")]})
        _parchar(_post=t.post)
        RUTAS["_prueba"] = [("opencode", "qwen3.8-flash")]
        try:
            llm("_prueba", "hola", sistema="sistema aparte")
        finally:
            RUTAS.pop("_prueba", None)
        p = t.ultimo("qwen3.8-flash")
        cont = (p["cuerpo"].get("messages") or [{}])[0].get("content")
        _ok(p["url"] == BASE_OPENCODE + "/messages" and p["cuerpo"].get("system") == "sistema aparte"
            and isinstance(cont, list) and cont[0]["type"] == "text"
            and p["cab"].get("anthropic-version") == "2023-06-01",
            "formato 'messages' (qwen3.8-flash): /messages con system aparte y bloques")

        # (b) un 429 baja al siguiente modelo
        t = _Transporte({"glm-5.3-flash": [(429, {"error": {"message": "rate limit"}})],
                         "deepseek-v4-flash": [(200, "lo hizo el segundo")]})
        _parchar(_post=t.post)
        salida = llm("masivas", "clasifica esto")
        _ok(salida == "lo hizo el segundo" and ultimo_modelo() == "opencode/deepseek-v4-flash"
            and t.cuantos("glm-5.3-flash") == 1,
            "un 429 baja de glm-5.3-flash a deepseek-v4-flash")

        t = _Transporte({"kimi-k3": [(503, {"error": "boom"})], "glm-5.3": [(200, "segundo ok")]})
        _parchar(_post=t.post)
        llm("analisis", "narrativas")
        _ok(ultimo_modelo() == "opencode/glm-5.3", "un 5xx tambien baja de modelo")

        # (c) JSON invalido: reintenta con el error adentro del prompt y despues baja
        del esperas[:]
        t = _Transporte({"kimi-k3": [(200, "esto no es json, perdon")],
                         "glm-5.3": [(200, BUEN_JSON)]})
        _parchar(_post=t.post)
        dato = llm("analisis", "extrae el statement", esquema=ESQUEMA_PRUEBA, max_reintentos=2)
        pedidos_kimi = [x for x in t.pedidos if x["modelo"] == "kimi-k3"]
        primer_prompt = pedidos_kimi[0]["cuerpo"]["messages"][-1]["content"]
        segundo_prompt = pedidos_kimi[1]["cuerpo"]["messages"][-1]["content"]
        _ok(len(pedidos_kimi) == 3 and dato == json.loads(BUEN_JSON)
            and ultimo_modelo() == "opencode/glm-5.3",
            "JSON invalido: 1+2 reintentos en kimi-k3 y recien ahi baja a glm-5.3")
        _ok("CORRECCION" not in primer_prompt and "CORRECCION" in segundo_prompt
            and "no es JSON" in segundo_prompt,
            "el reintento le manda el error de validacion adentro del prompt")
        _ok("FORMATO DE SALIDA" in primer_prompt and '"required"' in primer_prompt,
            "con esquema, el esquema viaja en el prompt (los tres formatos)")
        _ok(esperas == [round(ESPERA_BASE, 3), round(ESPERA_BASE * 2, 3)],
            "la espera entre reintentos crece: %s" % esperas)

        t = _Transporte({"kimi-k3": [(200, '{"tipo": "rumor", "texto": "x"}')],
                         "glm-5.3": [(200, BUEN_JSON)]})
        _parchar(_post=t.post)
        llm("analisis", "extrae", esquema=ESQUEMA_PRUEBA, max_reintentos=1)
        _ok(t.cuantos("kimi-k3") == 2 and ultimo_modelo() == "opencode/glm-5.3",
            "JSON bien formado pero que viola el esquema tambien reintenta y baja")

        t = _Transporte({"kimi-k3": [(200, "prosa " + BUEN_JSON + " gracias")]})
        _parchar(_post=t.post)
        _ok(llm("analisis", "extrae", esquema=ESQUEMA_PRUEBA) == json.loads(BUEN_JSON),
            "el JSON se rescata aunque venga con texto alrededor")

        # (d) EL IMPORTANTE: 'masivas' nunca llama a Claude; levanta CuotaAgotada
        claude = _ClaudeFalso()
        t = _Transporte({"glm-5.3-flash": [(429, {"error": "sin cuota"})],
                         "deepseek-v4-flash": [(429, {"error": "sin cuota"})]})
        _parchar(_post=t.post, _llamar_claude=claude)
        try:
            llm("masivas", "clasifica esto")
            _ok(False, "con los dos Flash agotados deberia levantar CuotaAgotada")
        except CuotaAgotada as e:
            _ok(claude.n == 0, "'masivas' con los dos Flash agotados NO llama a Claude (llamadas=%d)"
                % claude.n)
            _ok("DEGRADA" in str(e), "el mensaje de CuotaAgotada le dice al llamador que degrade")
        _ok(not [p for p, _m in RUTAS["masivas"] if p == "claude"],
            "RUTAS['masivas'] no tiene a Claude en la cascada")

        # ... y si alguien mete a Claude en esa ruta igual no lo llama (guardarrail doble)
        claude = _ClaudeFalso()
        _parchar(_llamar_claude=claude)
        masivas_real = list(RUTAS["masivas"])   # se restaura EL VALOR, no un literal copiado: si
        RUTAS["masivas"] = masivas_real + [("claude", None)]   # manana cambia la cascada masiva, el
        try:                                                   # autotest no la puede pisar en silencio
            llm("masivas", "clasifica esto")
            _ok(False, "'masivas' saboteada deberia levantar CuotaAgotada igual")
        except CuotaAgotada:
            _ok(claude.n == 0, "aunque alguien agregue Claude a 'masivas', SIN_RED_CLAUDE lo saltea")
        finally:
            RUTAS["masivas"] = masivas_real

        # el resto de las tareas SI tiene red
        claude = _ClaudeFalso("lo escribio claude")
        t = _Transporte({"kimi-k3": [(429, {"error": "x"})], "glm-5.3": [(429, {"error": "x"})]})
        _parchar(_post=t.post, _llamar_claude=claude)
        salida = llm("analisis", "narrativas")
        _ok(salida == "lo escribio claude" and claude.n == 1
            and ultimo_modelo() == "claude/" + MODELO_CLAUDE,
            "'analisis' si cae en la red de emergencia cuando se agotan los dos de OpenCode")

        # (e) ultimo_modelo()/ultimo_detalle() reportan bien, tambien cuando falla todo
        t = _Transporte({"grok-4.6": [(200, "investigado")]})
        _parchar(_post=t.post)
        llm("investigacion", "cubri el hueco asiatico")
        d = ultimo_detalle()
        _ok(ultimo_modelo() == "opencode/grok-4.6" and d["tarea"] == "investigacion"
            and d["ok"] and d["intentos"] == 1 and isinstance(d["ms"], int),
            "ultimo_modelo()/ultimo_detalle() reportan el modelo que sirvio, para run_log")
        claude = _ClaudeFalso(explota="429 tope de Claude")
        t = _Transporte({"grok-4.6": [(429, {"error": "x"})]})
        _parchar(_post=t.post, _llamar_claude=claude)
        try:
            llm("investigacion", "x")
        except CuotaAgotada:
            pass
        # Contra el largo REAL de la ruta, no contra un numero fijo: agregar un proveedor a la
        # cascada no tiene por que romper este test.
        _ok(ultimo_modelo() == "" and ultimo_detalle()["ok"] is False
            and len(ultimo_detalle()["caidas"]) == len(RUTAS["investigacion"]),
            "si fracasa la cascada entera, ultimo_modelo() queda vacio y quedan anotadas las %d caidas"
            % len(RUTAS["investigacion"]))
        _ok(any("GEMINI_API_KEY" in str(c) for c in ultimo_detalle()["caidas"]),
            "un proveedor sin clave figura en las caidas diciendo que le falta, no en silencio")

        # (f) prosa DESPUES del JSON: el caso que mas repiten los modelos al cerrar
        t = _Transporte({"kimi-k3": [(200, BUEN_JSON + " Espero que te sirva.")]})
        _parchar(_post=t.post)
        _ok(llm("analisis", "extrae", esquema=ESQUEMA_PRUEBA) == json.loads(BUEN_JSON)
            and t.cuantos("kimi-k3") == 1,
            "una cortesia DESPUES del JSON no cuesta ni un reintento ni una bajada de modelo")

        # (g) un esquema mal escrito se corta antes de gastar un solo request
        t = _Transporte({"kimi-k3": [(200, BUEN_JSON)]})
        _parchar(_post=t.post)
        try:
            llm("analisis", "extrae", esquema={"type": "objetc"})
            _ok(False, "un esquema mal escrito deberia levantar ValueError")
        except ValueError as e:
            _ok(len(t.pedidos) == 0 and "esquema" in str(e),
                "un esquema mal escrito levanta ValueError sin salir a la red (pedidos=%d)"
                % len(t.pedidos))
        except CuotaAgotada:
            _ok(False, "un esquema mal escrito quemo la cascada entera y mintio con CuotaAgotada")

        # (h) una respuesta vacia (200 con cuerpo sin texto) tambien baja de modelo
        t = _Transporte({"kimi-k3": [(200, {"choices": [{"message": {"content": "   "}}]})],
                         "glm-5.3": [(200, "el segundo si contesto")]})
        _parchar(_post=t.post)
        _ok(llm("analisis", "x") == "el segundo si contesto"
            and ultimo_modelo() == "opencode/glm-5.3",
            "una respuesta vacia baja de modelo (no se devuelve el vacio como si fuera salida)")

        # (i) trazabilidad sin restos: un error temprano no puede dejar el modelo de la anterior
        t = _Transporte({"kimi-k3": [(200, "sirvio")]})
        _parchar(_post=t.post)
        llm("analisis", "x")
        _ok(ultimo_modelo() == "opencode/kimi-k3", "ultimo_modelo() tiene el de la llamada buena")
        try:
            llm("inexistente", "x")
        except ValueError:
            pass
        _ok(ultimo_modelo() == "" and ultimo_detalle()["tarea"] == "inexistente",
            "tras una tarea desconocida ultimo_modelo() no miente con la llamada anterior")
        llm("analisis", "x")
        os.environ.pop("OPENCODE_API_KEY")
        os.environ.pop("ANTHROPIC_API_KEY")
        try:
            llm("analisis", "x")
        except FaltaClave:
            pass
        _ok(ultimo_modelo() == "", "tras FaltaClave tampoco queda el modelo de la llamada anterior")
        os.environ["OPENCODE_API_KEY"] = "prueba-opencode"
        os.environ["ANTHROPIC_API_KEY"] = "prueba-anthropic"

        # coherencia de las tablas
        faltan = sorted({m for r in RUTAS.values() for p, m in r if p == "opencode"} - set(FORMATO))
        _ok(not faltan, "todos los modelos de RUTAS tienen formato en FORMATO (faltan: %s)" % faltan)
        _ok(set(FORMATO.values()) <= set(ADAPTADORES), "todo formato de FORMATO tiene adaptador")

        # ---- proveedores compatibles con OpenAI (la tabla PROVEEDORES) ----
        print()
        print("-- proveedores compatibles: openrouter, gemini, groq, cerebras, local --")

        class _TFalso:
            """Transporte falso: anota a que URL y con que cabeceras se pidio."""

            def __init__(self):
                self.visto = []

            def post(self, url, cabeceras, cuerpo, timeout):
                self.visto.append((url, dict(cabeceras), cuerpo))
                return 200, {"choices": [{"message": {"content": '{"ok": true}'}}]}

        for prov, modelo, clave_env in (
                ("openrouter", "meta-llama/llama-3.3-70b-instruct:free", "OPENROUTER_API_KEY"),
                ("gemini", "gemini-2.5-flash", "GEMINI_API_KEY"),
                ("groq", "llama-3.3-70b-versatile", "GROQ_API_KEY")):
            t = _TFalso()
            _prev2 = _parchar(_post=t.post)
            os.environ[clave_env] = "clave-de-prueba"
            try:
                txt = _pedir(prov, modelo, "sos util", "hola", None, 10)
                url, cab, cuerpo = t.visto[0]
                _ok(url.startswith(PROVEEDORES[prov]["base"]),
                    "%s pega a su propia base" % prov)
                _ok(cab.get("Authorization") == "Bearer clave-de-prueba",
                    "%s manda la credencial de %s" % (prov, clave_env))
                _ok(cuerpo.get("model") == modelo, "%s manda el modelo pedido" % prov)
                _ok("{" in txt, "%s devuelve el texto del modelo" % prov)
            finally:
                globals().update(_prev2)
                os.environ.pop(clave_env, None)

        # sin clave, el proveedor se SALTEA y la cascada sigue; no explota
        _prev2 = _parchar(_post=_TFalso().post)
        try:
            os.environ.pop("OPENROUTER_API_KEY", None)
            try:
                _pedir("openrouter", "x:free", "s", "p", None, 10)
                _ok(False, "sin clave, el proveedor se saltea en vez de explotar")
            except _Bajar as e:
                _ok("OPENROUTER_API_KEY" in str(e),
                    "sin clave configurada, se saltea y la cascada sigue")
        finally:
            globals().update(_prev2)

        # el proveedor local no pide clave: tiene que poder llamarse sin ninguna variable
        t = _TFalso()
        _prev2 = _parchar(_post=t.post)
        try:
            _pedir("local", "qwen2.5:3b", "s", "p", None, 10)
            _ok("Authorization" not in t.visto[0][1], "el proveedor 'local' no exige credencial")
        finally:
            globals().update(_prev2)

        _ok(all(v["formato"] in ADAPTADORES for v in PROVEEDORES.values()),
            "todo proveedor de la tabla declara un formato que existe")
        print()

        print("SALTEA: llamada real a OpenCode y a Claude (gasta plata y pide claves); "
              "se probaron los tres armados de request contra un transporte falso")
    finally:
        globals().update(previos)
        for k, v in previo_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    print("--- %d fallas ---" % len(_FALLAS))
    return not _FALLAS


if __name__ == "__main__":
    if "--autotest" in sys.argv:
        sys.exit(0 if _autotest() else 1)
    print(__doc__)
