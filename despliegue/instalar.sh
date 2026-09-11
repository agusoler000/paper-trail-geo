#!/usr/bin/env bash
# Instala Paper Trail · THE LEDGER en el VPS. Idempotente: se puede correr las veces que haga falta.
#
#   sudo bash despliegue/instalar.sh
#
# Pensado para el VPS real (Contabo, Ubuntu 24.04, 6 vCPU, 11 GB, Francia) que ya corre Coolify,
# Supabase, n8n y Evolution API. Por eso NO toca Docker ni nada de lo que ya esta andando: la app
# va al host en su propio venv, y la base se crea DENTRO del Postgres de Supabase que ya existe.
#
# Que hace, en orden:
#   1. swap de 8 GB (sin esto el render puede tumbar Supabase y n8n: hay 5,6 GB libres y 0 de swap)
#   2. paquetes del sistema (python3-venv, ffmpeg, git)
#   3. venv + dependencias de Python
#   4. los tres modelos de voz de Piper (250 MB) y el de embeddings
#   5. la base `radar` con pgvector
#   6. los timers de systemd
set -euo pipefail

APP="${APP:-/opt/papertrail}"
USUARIO="${SUDO_USER:-$(whoami)}"
SWAP_GB="${SWAP_GB:-8}"
REPO_ORIGEN="${REPO_ORIGEN:-https://github.com/agusoler000/paper-trail-geo.git}"

azul()  { printf "\n\033[1;34m== %s\033[0m\n" "$*"; }
ok()    { printf "   \033[0;32mOK\033[0m   %s\n" "$*"; }
aviso() { printf "   \033[0;33m!!\033[0m   %s\n" "$*"; }
malo()  { printf "   \033[0;31mXX\033[0m   %s\n" "$*"; }

[ "$(id -u)" -eq 0 ] || { malo "corré con sudo"; exit 1; }

# ---------------------------------------------------------------- 1. swap
azul "1/6  swap"
if swapon --show | grep -q .; then
  ok "ya hay swap: $(swapon --show --noheadings --bytes | awk '{printf "%.1f GB", $3/1073741824}')"
else
  if [ -f /swapfile ]; then
    aviso "/swapfile existe pero no esta activo; lo activo"
  else
    fallocate -l "${SWAP_GB}G" /swapfile
    chmod 600 /swapfile
    mkswap /swapfile >/dev/null
  fi
  swapon /swapfile
  grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
  ok "swap de ${SWAP_GB} GB activo y persistente"
fi
sysctl -q vm.swappiness=10
grep -q '^vm.swappiness' /etc/sysctl.conf || echo 'vm.swappiness=10' >> /etc/sysctl.conf
ok "swappiness=10 (usar swap solo cuando de verdad falta RAM)"

# ---------------------------------------------------------------- 2. sistema
azul "2/6  paquetes del sistema"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3-venv python3-dev build-essential ffmpeg git curl jq >/dev/null
ok "python3-venv, ffmpeg, git, jq"
command -v rhubarb >/dev/null && ok "rhubarb presente (mejora el lip-sync)" \
  || aviso "rhubarb no esta: el lip-sync sale del sobre de amplitud. Es opcional."

# ---------------------------------------------------------------- 3. app + venv
azul "3/6  aplicacion y entorno de Python"
mkdir -p "$APP"
if [ -n "$REPO_ORIGEN" ] && [ ! -d "$APP/.git" ]; then
  git clone --depth 1 "$REPO_ORIGEN" "$APP"
  ok "repo clonado"
elif [ -d "$APP/.git" ]; then
  git -C "$APP" pull --ff-only || aviso "no pude hacer pull; sigo con lo que hay"
else
  aviso "sin REPO_ORIGEN: copiá el proyecto a $APP antes de seguir (rsync/scp)"
fi
[ -f "$APP/radar/fuentes.json" ] || { malo "no encuentro $APP/radar/fuentes.json"; exit 1; }

python3 -m venv "$APP/.venv" 2>/dev/null || true
"$APP/.venv/bin/pip" install -q --upgrade pip
"$APP/.venv/bin/pip" install -q \
  numpy requests httpx jsonschema sqlalchemy "psycopg[binary]" \
  pillow openai anthropic mcp fastapi uvicorn \
  google-api-python-client google-auth google-auth-oauthlib \
  fastembed piper-tts
ok "dependencias instaladas en $APP/.venv"
chown -R "$USUARIO":"$USUARIO" "$APP"

# ---------------------------------------------------------------- 4. modelos
azul "4/6  modelos (se bajan una vez, ~600 MB)"
sudo -u "$USUARIO" "$APP/.venv/bin/python" "$APP/videos/DAILY/voz.py" --bajar
ok "voces de Piper"
sudo -u "$USUARIO" "$APP/.venv/bin/python" - <<'PY'
from fastembed import TextEmbedding
TextEmbedding("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
print("   OK   modelo de embeddings en cache")
PY

# ---------------------------------------------------------------- 5. base
azul "5/6  base de datos propia"
# Contenedor APARTE, no dentro del Postgres de Supabase. Dos motivos:
#  1. Aislamiento: si Coolify recrea Supabase, la base del Radar no se va con el.
#  2. No compite por conexiones con lo que ya esta en produccion.
# Se ata a 127.0.0.1: el VPS esta en internet y esta base NO tiene por que verse desde afuera.
DB_NOMBRE="${DB_NOMBRE:-papertrail-db}"
DB_BASE="${DB_BASE:-radar}"
DB_USUARIO="${DB_USUARIO:-radar}"

if ! command -v docker >/dev/null; then
  aviso "no hay docker: la app va a usar SQLite. Anda, pero agrupar tarda ~4 veces mas."
elif docker ps -a --format '{{.Names}}' | grep -qx "$DB_NOMBRE"; then
  DB_PUERTO=$(docker port "$DB_NOMBRE" 5432/tcp 2>/dev/null | head -1 | sed 's/.*://')
  docker start "$DB_NOMBRE" >/dev/null 2>&1 || true
  ok "la base ya existia: $DB_NOMBRE en el puerto ${DB_PUERTO:-?}"
else
  # Puerto libre, lejos del 5432 estandar para no chocar con nada.
  DB_PUERTO=""
  for p in 5442 5443 5444 5445 54329; do
    if ! ss -ltn 2>/dev/null | grep -q ":$p " && ! docker ps --format '{{.Ports}}' | grep -q ":$p->"; then
      DB_PUERTO=$p; break
    fi
  done
  [ -n "$DB_PUERTO" ] || { malo "no encontre un puerto libre entre 5442 y 54329"; exit 1; }
  DB_CLAVE=$(head -c 24 /dev/urandom | base64 | tr -d '/+=' | head -c 28)
  docker run -d --name "$DB_NOMBRE" --restart unless-stopped     -e POSTGRES_PASSWORD="$DB_CLAVE" -e POSTGRES_USER="$DB_USUARIO" -e POSTGRES_DB="$DB_BASE"     -p 127.0.0.1:"$DB_PUERTO":5432     -v papertrail_db:/var/lib/postgresql/data     pgvector/pgvector:pg16 >/dev/null
  ok "contenedor $DB_NOMBRE creado en 127.0.0.1:$DB_PUERTO (solo local)"

  printf "   esperando a que la base levante"
  for _ in $(seq 1 40); do
    docker exec "$DB_NOMBRE" pg_isready -U "$DB_USUARIO" -q 2>/dev/null && break
    printf "."; sleep 1
  done
  echo
  docker exec "$DB_NOMBRE" psql -U "$DB_USUARIO" -d "$DB_BASE"     -c 'CREATE EXTENSION IF NOT EXISTS vector;' >/dev/null
  ok "pgvector activo en la base '$DB_BASE'"

  # Se escribe el DSN solo: una cosa menos que completar a mano y sin riesgo de erratas.
  DSN="postgresql+psycopg://$DB_USUARIO:$DB_CLAVE@127.0.0.1:$DB_PUERTO/$DB_BASE"
  [ -f "$APP/.env" ] || cp "$APP/despliegue/env.ejemplo" "$APP/.env"
  if grep -q '^RADAR_DSN=' "$APP/.env"; then
    sed -i "s#^RADAR_DSN=.*#RADAR_DSN=$DSN#" "$APP/.env"
  else
    echo "RADAR_DSN=$DSN" >> "$APP/.env"
  fi
  chown "$USUARIO":"$USUARIO" "$APP/.env"; chmod 600 "$APP/.env"
  ok "RADAR_DSN escrito en $APP/.env (no hay que completarlo a mano)"
fi

# ---------------------------------------------------------------- 6. systemd
azul "6/6  timers"
[ -f "$APP/.env" ] || { cp "$APP/despliegue/env.ejemplo" "$APP/.env"; chown "$USUARIO":"$USUARIO" "$APP/.env"; chmod 600 "$APP/.env"; aviso "creé $APP/.env — HAY QUE COMPLETARLO"; }
for u in "$APP"/despliegue/systemd/*.service "$APP"/despliegue/systemd/*.timer; do
  sed -e "s#__APP__#$APP#g" -e "s#__USUARIO__#$USUARIO#g" "$u" > "/etc/systemd/system/$(basename "$u")"
done
systemctl daemon-reload
for t in papertrail-radar.timer papertrail-diario.timer papertrail-vigilante.timer; do
  systemctl enable --now "$t" >/dev/null 2>&1 && ok "$t activo"
done

azul "listo"
cat <<FIN
   Falta SOLO esto, y no es codigo:

   1. Poner tu clave de OpenCode en $APP/.env  (es la UNICA imprescindible):
        nano $APP/.env
      RADAR_DSN ya quedo escrito. ANTHROPIC_API_KEY es opcional: solo es la red
      si OpenCode se agota, y la suscripcion de Claude Code NO sirve ahi.
   2. Autorizar YouTube una vez:
        cd $APP && .venv/bin/python videos/DAILY/subir.py --autorizar
   3. Comprobar que todo esta:
        cd $APP && .venv/bin/python despliegue/comprobar.py

   Despues, la primera corrida a mano (sin publicar nada):
        cd $APP && .venv/bin/python videos/DAILY/daily.py --correr \$(date -u +%F) --solo recolectar
FIN
