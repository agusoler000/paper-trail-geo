# -*- coding: utf-8 -*-
"""Motor de render local para la mesa de mapas: capas con keyframes, rigs de papel con FK, mapa que se
dibuja, y render en paralelo con PIL + ffmpeg. 0 creditos.

Conceptos:
  Track     : lista de (t, valor, easing) -> valor(t) interpolado (easing hacia el siguiente kf)
  Obj       : imagen RGBA con tracks x,y,rot,sc,a (alpha) y ventana [on,off)
  Rig       : personaje cortado por cortador.py; acciones enter/exit/point/nod/slam/walk/hold/look
  MapSheet  : hoja de mapa con capas (wipe o fade) y rutas que se dibujan solas
  Scene     : lista de capas ordenadas por z; render(t) -> Image; check_framing() = nada parcialmente cortado

v2 (2026-09-07, feedback de Agustin "cosas cortadas"/"mas fluido"): bbox(t) en Obj y Rig, Scene.window(t) y
Scene.check_framing(); pops/unpops mas lentos; capas de mapa con fade.
v3 (2026-09-08, plan `canal/CREATIVO.md` nivel 0): fisica de papel (drop/flipin/slide_off/crumple), sombra dura por
objeto que crece al levantarse (lift), escala vertical (sy), profundidad con paralaje por capa (depth) en los push-in,
golpe de camara (Scene.shake) y barrido (Scene.whip), Rig.point_at(xy)/shrug/hop y bob al caminar,
Scene.report(): huecos sin evento y cortes por minuto.

v4 (2026-09-15, `canal/AUDITORIA_MOTOR_2026-09-15.md` §6.1). TODO lo nuevo es OPT-IN: una escena
vieja (`Scene(png_de_1920x1080)`) rinde exactamente igual que en la v3, cuadro a cuadro.
  Mundo     : superficie de fondo MAS GRANDE que el cuadro, con capas de pais, rutas y oscurecido.
              La camara vive dentro y puede abrir (zoom < 1) hasta ver el mundo entero.
  Scene(fondo, size=(w,h), v4=True)
              · `size` = formato del cuadro por escena (1080x1920 vertical, por ejemplo).
              · `v4=True` enciende la vida por defecto (camara, objetos y rigs) y `M.VIDA_V4`.
  Scene.hud : capa de PANTALLA. Se dibuja despues del recorte y del resize, en px de cuadro, sin
              parallax ni deriva: subtitulos, cifras, chips, barras. No se corta ni se achica.
  Scene.subtitulos(palabras, ...) arma esa capa a partir de `audio/_palabras.json`.
  Scene.corte / Scene.viaje : la gramatica nueva = un plano es un corte + UN viaje motivado.
  Scene.visible(t) : detector de vacio honesto (ignora rotulos y etiquetas de region).
  Track.set(0, v)  : ahora REEMPLAZA el keyframe inicial (antes convivia con el y ganaba el viejo).

Compatibilidad: `M.VIDA_V4` arranca en False. Las 12 producciones anteriores no lo encienden, asi
que su `bbox()`, su `check_framing` y sus cuadros no cambian. La unica diferencia medible en lo
viejo es el arreglo de `Track.set(0, v)`, que solo afecta al instante t = 0.
"""
import json, math, os
from PIL import Image, ImageDraw, ImageFilter
W,H=1920,1080; FPS=24
EVENTS=[]   # (t, kind, vol) -> mezcla.py
def ev(t,kind,vol=1.0): EVENTS.append((round(float(t),3),kind,vol))
BASE=os.path.dirname(os.path.abspath(__file__)); ASSETS=os.path.join(BASE,'assets'); ELENCO=os.path.join(BASE,'..','pruebas','elenco')

# ---------------------------------------------------------------- v4: formato y vida
VIDA_V4=False       # las coreos v4 lo encienden (o `Scene(..., v4=True)`); lo viejo queda igual
def set_formato(w,h):
    """Cambia los globales de formato para las coreos que los usan como constantes (`W, H = M.W, M.H`).
    Lo nuevo deberia leer `scene.W/scene.H`; esto es la puerta de atras para lo que ya existe."""
    global W,H; W,H=int(w),int(h); return (W,H)
def set_v4(on=True):
    global VIDA_V4; VIDA_V4=bool(on); return VIDA_V4

_NOBJ=[0]           # contador para repartir las fases de vida de forma DETERMINISTA
def _fase(n=None):
    """Fase 0..2pi estable entre procesos. `hash()` de Python esta aleatorizado por proceso y el
    render corre en un pool: con hash(), cada trozo de video daria una fase distinta y se veria el
    salto en la juntura. Para los objetos va por contador (build() es determinista); para los rigs,
    por una suma de codigos del nombre."""
    if n is None:
        _NOBJ[0]+=1; k=_NOBJ[0]*2.399963229728653          # angulo aureo: reparte las fases
    else:
        k=sum((i+1)*ord(c) for i,c in enumerate(str(n)))*0.37
    return k%6.283185307179586

# palabras que no pueden quedar al final de un subtitulo (rompen la lectura).
# Fuente unica: `produccion/shorts.py` la importa de aca.
DEBILES={'and','the','of','in','to','a','an','or','that','with','for','is','are',
         'it','on','at','as','but','by','from','was','were','not','its','their',
         'his','her','you','we','they','this','these','those','no','so','if','when',
         'without','into','over','about','than','because','while','after','before'}

def agrupar(palabras,grupos=(2,4),pausa=0.25):
    """Agrupa `[(palabra, t0, t1)]` en grupos de subtitulo de 2 a 4 palabras.

    Corta por puntuacion y por las pausas reales de la voz (> `pausa` s), y no deja una palabra
    debil al final del grupo: 'forty-nine thousand people crossed INTO' se lee mal, 'into Ceuta'
    se lee bien. Lo usan `Scene.subtitulos` (HUD del motor) y `shorts.cues` (subtitulo quemado):
    una sola manera de partir el texto en todo el canal."""
    pal=[(str(w),float(a),float(b)) for w,a,b in palabras]
    gr=[]; i=0; n=len(pal)
    while i<n:
        g=[pal[i]]; i+=1
        while i<n and len(g)<grupos[1]:
            w,a,b=g[-1]
            if len(g)>=grupos[0] and ((w and w[-1] in '.!?:;,—') or pal[i][1]-b>pausa): break
            g.append(pal[i]); i+=1
        while len(g)>grupos[0] and g[-1][0].strip('.,;:!?"').lower() in DEBILES:
            g.pop(); i-=1                                # la debil abre el grupo siguiente
        gr.append(g)
    return gr

def ease_io(t): return t*t*(3-2*t)
def ease_out(t): return 1-(1-t)**3
def ease_in(t): return t**3
def ease_back(t): c=1.70158; return 1+(c+1)*(t-1)**3+c*(t-1)**2      # overshoot al final
def ease_bounce(t):
    if t<1/2.75: return 7.5625*t*t
    if t<2/2.75: t-=1.5/2.75; return 7.5625*t*t+.75
    if t<2.5/2.75: t-=2.25/2.75; return 7.5625*t*t+.9375
    t-=2.625/2.75; return 7.5625*t*t+.984375
def ease_soft(t): return 0.5-0.5*math.cos(math.pi*t)   # seno: arranque y llegada muy suaves
EAS={'io':ease_io,'out':ease_out,'in':ease_in,'lin':lambda x:x,'hold':lambda x:0,'back':ease_back,'bounce':ease_bounce,'soft':ease_soft}

class Track:
    def __init__(self,v0=0.0): self.k=[(0.0,v0,'hold')]
    def set(self,t,v,e='io'):
        # insertar ordenado; el easing es el del tramo que TERMINA en este kf, guardado en el kf anterior
        # v4 (bug M7): un keyframe en t=0 REEMPLAZA al inicial. Antes convivian los dos y ganaba el
        # inicial (`__call__` devuelve k[0] cuando t<=k[0][0]), asi que `set(0, v)` era un no-op en el
        # cuadro 0 exacto y cada coreo lo parcheaba con `Track(v)`. El easing de k[0] no se lee nunca.
        if t<=0.0 and self.k and self.k[0][0]<=0.0:
            self.k[0]=(0.0,v,'hold'); return self
        self.k.append((t,v,e)); self.k.sort(key=lambda x:x[0]); return self
    def __call__(self,t):
        k=self.k
        if t<=k[0][0]: return k[0][1]
        for (t0,v0,_),(t1,v1,e) in zip(k,k[1:]):
            if t0<=t<=t1:
                if t1==t0 or t==t1: return v1      # en el instante exacto de un keyframe vale ESE keyframe (antes devolvia el anterior: flash en (0,0))
                u=(t-t0)/(t1-t0); f=EAS[e](u)
                if isinstance(v0,(tuple,list)): return tuple(a+(b-a)*f for a,b in zip(v0,v1))
                return v0+(v1-v0)*f
        return k[-1][1]

def _rot_extent(w,h,deg):
    a=math.radians(abs(deg)); return (w*math.cos(a)+h*math.sin(a), w*math.sin(a)+h*math.cos(a))

class Obj:
    def __init__(self,img,x=0,y=0,z=0,rot=0,sc=1.0,a=1.0,on=0.0,off=1e9):
        self.img=img if isinstance(img,Image.Image) else Image.open(img).convert('RGBA')
        self.x=Track(x); self.y=Track(y); self.rot=Track(rot); self.sc=Track(sc); self.a=Track(a); self.z=z; self.on=on; self.off=off
        # La fase del wobble salia de `id(self)`, que cambia de proceso a proceso. El render corre en
        # un pool de 20 procesos y cada uno construye la escena: las cartas giraban con OTRA fase en
        # cada trozo de video y en la juntura se veia el salto. Medido el 15-sep: dos corridas del
        # mismo cuadro del ep. 09 diferian 0,48/255 de media y 215 en el peor pixel. Ahora la fase
        # sale de un contador que `Scene.__init__` pone a cero: mismo build, misma fase, siempre.
        self.wobble=0.0; self.phase=_fase(); self.sfx='pop'
        # v4: vida propia. `Scene.add` pone los valores por defecto (wobble 0,35 grados y bob 1 px)
        # solo en escenas v4 y solo si la coreo no los toco. `vida=0` deja el objeto quieto.
        self.bob=0.0; self.vida=1.0; self.phase_b=(self.phase*1.7+2.1)%6.283185307179586
        self.scene=None      # la inyecta Scene.add: de ahi salen el ancho y el alto del formato
        self.transit=[]      # intervalos (t0,t1) en que puede cruzar el borde (entra/sale de cuadro a proposito)
        self.bg=False        # True = fondo/overlay: no se verifica encuadre
        self.name=''
        # v3
        self.sy=Track(1.0)   # escala vertical extra (flip-in, arrugar)
        self.lift=Track(0.0) # 0 = apoyado; 1 = levantado (sombra grande y desplazada)
        self.depth=1.03      # paralaje: 1.0 = pegado a la hoja, >1 = mas cerca de la camara
        self.shadow=True     # sombra dura de papel
    # helpers encadenables
    def at(self,t,x,y,e='io'): self.x.set(t,x,e); self.y.set(t,y,e); return self
    def move(self,t0,t1,xy0,xy1,e='io'):
        self.at(t0,*xy0,'hold'); self.at(t1,*xy1,e)
        if abs(xy1[0]-xy0[0])+abs(xy1[1]-xy0[1])>60: ev(t0,'slide',min(1.0,(t1-t0)*1.5))
        return self
    def spin(self,t0,t1,r0,r1,e='io'): self.rot.set(t0,r0,'hold'); self.rot.set(t1,r1,e); return self
    def scale(self,t0,t1,s0,s1,e='io'): self.sc.set(t0,s0,'hold'); self.sc.set(t1,s1,e); return self
    def fade(self,t0,t1,a0,a1,e='lin'): self.a.set(t0,a0,'hold'); self.a.set(t1,a1,e); return self
    def pop(self,t,x,y,dur=0.5):
        """aparece con overshoot en (x,y)"""
        self.on=t; self.at(t,x,y,'hold'); self.scale(t,t+dur,0.2,1.0,'back'); self.fade(t,t+0.15,0,1); ev(t,self.sfx); return self
    def unpop(self,t,dur=0.4):
        s0=self.sc(t-0.001); self.off=t+dur; self.scale(t,t+dur,s0,s0*0.2,'in'); self.fade(t,t+dur,1,0); ev(t,'unpop',0.6); return self   # parte de la escala REAL (antes saltaba a 1.0)
    def flyout(self,t0,t1,xy1,e='in'):
        """sale de cuadro a proposito (se marca como transito para el chequeo de encuadre)"""
        self.move(t0,t1,(self.x(t0),self.y(t0)),xy1,e); self.off=t1+0.02; self.transit.append((t0,t1+0.05)); return self
    # ---- v3: fisica de papel
    def drop(self,t,x,y,dur=0.55,h=60,sc_=1.0,tilt=3.0):
        """cae desde h px arriba, rebota y se asienta con una rotacion residual. Entrada por defecto del v3."""
        self.on=t; self.x.set(t,x,'hold'); self.y.set(t,y-h,'hold'); self.y.set(t+dur,y,'bounce')
        self.sc.set(t,sc_,'hold'); self.a.set(t,0,'hold'); self.a.set(t+0.08,1,'lin')
        self.lift.set(t,1,'hold'); self.lift.set(t+dur*0.7,0,'in')
        r0=self.rot(t); self.rot.set(t,r0+tilt,'hold'); self.rot.set(t+dur*0.7,r0-tilt*0.4,'io'); self.rot.set(t+dur+0.25,r0,'soft')
        ev(t+dur*0.7,'clack',0.6); return self
    def flipin(self,t,x,y,dur=0.45,sc_=1.0):
        """entra girando sobre su eje horizontal (para cifras y veredictos)"""
        self.on=t; self.at(t,x,y,'hold'); self.sc.set(t,sc_,'hold'); self.a.set(t,1,'hold')
        self.sy.set(t,0.02,'hold'); self.sy.set(t+dur,1.0,'back'); ev(t,'flip',0.7); return self
    def slide_off(self,t,side='R',dur=0.6,w_=None):
        """se desliza fuera de la hoja por un lado (transito, no cuenta como cortado).
        `w_`: ancho del lienzo. Por defecto el de la escena (v4) y si no, el global del modulo."""
        if w_ is None: w_=self.scene.WM if self.scene is not None else W
        x0,y0=self.x(t),self.y(t); x1=w_+self.img.width if side=='R' else -self.img.width
        self.x.set(t,x0,'hold'); self.x.set(t+dur,x1,'in'); self.lift.set(t,0,'hold'); self.lift.set(t+0.15,0.6,'out')
        self.off=t+dur+0.02; self.transit.append((t,t+dur+0.05)); ev(t,'slide',0.6); return self
    def crumple(self,t,dur=0.5):
        """se arruga: escala en X a casi 0 con giro, y desaparece"""
        s0=self.sc(t-0.001); self.sc.set(t,s0,'hold'); self.sc.set(t+dur,s0*0.15,'in')
        self.sy.set(t,self.sy(t-0.001),'hold'); self.sy.set(t+dur,0.6,'in')
        r0=self.rot(t); self.rot.set(t,r0,'hold'); self.rot.set(t+dur,r0+40,'in'); self.off=t+dur+0.02; ev(t,'flip',0.9); return self
    def raise_(self,t,dur=0.3,lift=1.0):
        """se levanta de la mesa (sombra grande): para agarrar, mover y volver a apoyar"""
        self.lift.set(t,self.lift(t),'hold'); self.lift.set(t+dur,lift,'out'); return self
    def settle(self,t,dur=0.3):
        self.lift.set(t,self.lift(t),'hold'); self.lift.set(t+dur,0,'in'); ev(t+dur,'clack',0.4); return self
    _CERO=(0.0,0.0,0.0)
    def _rv(self,t):
        """v4: rotacion de wobble y desplazamiento de bob. (0,0,0) en objetos de fondo y con vida=0."""
        if not (self.wobble or self.bob) or self.bg or self.vida<=0: return Obj._CERO
        dr=self.wobble*math.sin(t*0.9+self.phase)*self.vida if self.wobble else 0.0
        if self.bob<=0: return (dr,0.0,0.0)
        b=self.bob*self.vida
        return (dr, b*0.62*math.sin(t*0.53+self.phase_b), b*math.sin(t*0.81+self.phase))
    def bbox(self,t):
        if not (self.on<=t<self.off): return None
        a=self.a(t); s=self.sc(t)
        if a<=0.02 or s<=0.01: return None
        dr,dx,dy=self._rv(t)
        w,h=self.img.width*s,self.img.height*s*self.sy(t); r=self.rot(t)+dr
        w,h=_rot_extent(w,h,r); cx,cy=self.x(t)+dx,self.y(t)+dy
        return (cx-w/2,cy-h/2,cx+w/2,cy+h/2)
    def draw(self,canvas,t,off=(0,0)):
        if not (self.on<=t<self.off): return
        a=self.a(t); s=self.sc(t); sy=self.sy(t)
        if a<=0.01 or s<=0.01 or sy<=0.01: return
        im=self.img
        if abs(s-1)>0.005 or abs(sy-1)>0.005: im=im.resize((max(1,int(im.width*s)),max(1,int(im.height*s*sy))),Image.BILINEAR)
        dr,dx,dy=self._rv(t)
        r=self.rot(t)+dr
        if abs(r)>0.05: im=im.rotate(-r,resample=Image.BICUBIC,expand=True)
        if a<0.995:
            al=im.split()[3].point(lambda v:int(v*a)); im=im.copy(); im.putalpha(al)
        px,py=int(round(self.x(t)+dx-im.width/2+off[0])),int(round(self.y(t)+dy-im.height/2+off[1]))
        if self.shadow and not self.bg:
            lf=self.lift(t); dx,dy=int(4+14*lf),int(6+18*lf)
            sh=Image.new('RGBA',im.size,(30,24,18,0)); sh.putalpha(im.split()[3].point(lambda v:int(v*(0.32-0.12*lf))))
            canvas.alpha_composite(sh,(px+dx,py+dy))
        canvas.alpha_composite(im,(px,py))

def rot(p,piv,deg):
    a=math.radians(deg); dx,dy=p[0]-piv[0],p[1]-piv[1]
    return (piv[0]+dx*math.cos(a)-dy*math.sin(a), piv[1]+dx*math.sin(a)+dy*math.cos(a))

class Rig:
    """Personaje de papel. Posicion = donde cae el pixel (0,0) de la imagen original, escalado."""
    def __init__(self,nombre,x,y,sc=0.6,z=50,on=0.0,off=1e9,flip=False):
        d=os.path.join(ELENCO,'rig',nombre); self.rig=json.load(open(os.path.join(d,'rig.json')))
        self.pz={k:Image.open(os.path.join(d,k+'.png')).convert('RGBA') for k in self.rig['orden']}
        self.pz={k:im.resize((max(1,int(im.width*sc)),max(1,int(im.height*sc))),Image.LANCZOS) for k,im in self.pz.items()}
        self.sc=sc; self.x=Track(x); self.y=Track(y); self.z=z; self.on=on; self.off=off
        self.ang={k:Track(0.0) for k in ('cabeza','L_h','L_c','R_h','R_c')}
        self.props=[]    # (Obj, side) pegado a la mano
        self.bob=0.0; self.a=Track(1.0); self.flip=flip; self.transit=[]; self.bg=False; self.name=nombre
        self.depth=1.06; self.walks=[]; self.shadow=True   # v3
        # v4: vida. `v4` lo enciende Scene.add en escenas v4; `vida` multiplica (0 = estatua).
        self.v4=False; self.vida=1.0; self.fase=_fase(nombre)
        self.scene=None
    def _w(self,w_=None):
        """Ancho del lienzo para entrar y salir de cuadro. v4: el de la escena; si no, el global."""
        if w_ is not None: return w_
        return self.scene.WM if self.scene is not None else W
    # ---- acciones
    def enter(self,t,side='R',dur=1.1,home=None,w_=None):
        hx=home[0] if home else self.x(t+dur); hy=home[1] if home else self.y(t+dur)
        WW=self._w(w_); sx=WW+400 if side=='R' else -700
        self.on=min(self.on,t); self.x.set(t,sx,'hold'); self.y.set(t,hy,'hold'); self.x.set(t+dur*0.85,hx-25 if side=='R' else hx+25,'out'); self.x.set(t+dur,hx,'io'); ev(t,'whoosh'); ev(t+dur*0.85,'clack',0.5)
        self.transit.append((t,t+dur+0.4)); return self
    def exit(self,t,side='R',dur=1.0,w_=None):
        WW=self._w(w_)
        x0=self.x(t); self.x.set(t,x0,'hold'); self.x.set(t+dur,WW+400 if side=='R' else -700,'in'); self.off=t+dur; ev(t,'whoosh',0.7); self.transit.append((t,t+dur)); return self
    def walk(self,t0,t1,x1,y1=None):
        self.x.set(t0,self.x(t0),'hold'); self.y.set(t0,self.y(t0),'hold'); self.x.set(t1,x1,'soft'); self.y.set(t1,y1 if y1 is not None else self.y(t0),'soft')
        self.walks.append((t0,t1)); return self
    # ---- v3
    def point_at(self,t,xy,side='L',hold=2.0,ret=True,dur=0.5):
        """el brazo `side` (de pantalla) apunta de verdad a un punto de composicion (p. ej. G('Moscow'))"""
        V=self.rig['pivotes']; s=self.sc; ox,oy=self.x(t+dur),self.y(t+dur)
        S=V['brazo_%s_sup'%side]; E=V['brazo_%s_inf'%side]
        sx,sy=ox+S[0]*s,oy+S[1]*s
        rest=math.degrees(math.atan2(E[1]-S[1],E[0]-S[0])); want=math.degrees(math.atan2(xy[1]-sy,xy[0]-sx))
        rh=(want-rest+180)%360-180
        h=self.ang[side+'_h']; c=self.ang[side+'_c']
        h.set(t,h(t),'hold'); c.set(t,c(t),'hold')
        h.set(t+dur*0.5,rh*-0.25,'io'); c.set(t+dur*0.5,c(t),'io')          # anticipacion
        h.set(t+dur,rh,'back'); c.set(t+dur,0,'out'); ev(t+dur*0.8,'slide',0.5)
        if ret:
            h.set(t+dur+hold,rh,'hold'); c.set(t+dur+hold,0,'hold'); h.set(t+dur+hold+0.7,0,'soft'); c.set(t+dur+hold+0.7,0,'soft')
        return self
    def shrug(self,t,dur=0.4,hold=0.8):
        for s,sg in (('L',1),('R',-1)):
            h=self.ang[s+'_h']; c=self.ang[s+'_c']
            h.set(t,h(t),'hold'); c.set(t,c(t),'hold'); h.set(t+dur,sg*-18,'out'); c.set(t+dur,sg*70,'out')
            h.set(t+dur+hold,sg*-18,'hold'); c.set(t+dur+hold,sg*70,'hold'); h.set(t+dur+hold+0.6,0,'soft'); c.set(t+dur+hold+0.6,0,'soft')
        k=self.ang['cabeza']; k.set(t,k(t),'hold'); k.set(t+dur,-6,'io'); k.set(t+dur+hold+0.6,0,'soft'); return self
    def hop(self,t,h=22):
        y0=self.y(t); self.y.set(t,y0,'hold'); self.y.set(t+0.12,y0-h,'out'); self.y.set(t+0.42,y0,'bounce'); ev(t+0.4,'clack',0.5); return self
    def lean(self,t,deg=6,dur=0.35,hold=1.0):
        """retrocede/avanza inclinando la cabeza y los hombros (reaccion)"""
        k=self.ang['cabeza']; k.set(t,k(t),'hold'); k.set(t+dur,deg,'out'); k.set(t+dur+hold,deg,'hold'); k.set(t+dur+hold+0.5,0,'soft')
        x0=self.x(t); self.x.set(t,x0,'hold'); self.x.set(t+dur,x0-deg*3,'out'); self.x.set(t+dur+hold,x0-deg*3,'hold'); self.x.set(t+dur+hold+0.5,x0,'soft'); return self
    def point(self,t,side='L',hold=2.5,ret=True,amp=1.0):
        """anticipacion, golpe, sostiene, vuelve. side = brazo de PANTALLA que senala."""
        sg=1 if side=='L' else -1
        h=self.ang[side+'_h']; c=self.ang[side+'_c']
        h.set(t,h(t),'hold'); c.set(t,c(t),'hold')
        h.set(t+0.3,sg*-40*amp,'io'); c.set(t+0.3,sg*-12,'io')
        h.set(t+0.6,sg*20*amp,'out'); c.set(t+0.6,sg*62,'out'); ev(t+0.5,'slide',0.5)
        h.set(t+0.85,sg*12*amp,'io'); c.set(t+0.85,sg*55,'io')
        if ret:
            h.set(t+0.85+hold,sg*12*amp,'hold'); c.set(t+0.85+hold,sg*55,'hold'); h.set(t+1.6+hold,0,'soft'); c.set(t+1.6+hold,0,'soft')
        return self
    def raise_arms(self,t,dur=0.5,deg=-70,hold=1.0):
        for s,sg in (('L',1),('R',-1)):
            h=self.ang[s+'_h']; h.set(t,h(t),'hold'); h.set(t+dur,sg*deg,'back'); h.set(t+dur+hold,sg*deg,'hold'); h.set(t+dur+hold+0.7,0,'soft')
        return self
    def slam(self,t):
        """levanta los dos brazos y los baja de golpe; el cuerpo salta"""
        for s,sg in (('L',1),('R',-1)):
            h=self.ang[s+'_h']; c=self.ang[s+'_c']
            h.set(t,h(t),'hold'); h.set(t+0.35,sg*-62,'out'); h.set(t+0.5,sg*15,'in'); h.set(t+1.1,0,'soft')
            c.set(t,c(t),'hold'); c.set(t+0.35,sg*-30,'out'); c.set(t+0.5,sg*20,'in'); c.set(t+1.1,0,'soft')
        y0=self.y(t); self.y.set(t+0.49,y0,'hold'); self.y.set(t+0.57,y0-26,'out'); self.y.set(t+0.8,y0,'bounce'); ev(t+0.5,'thump'); return self
    def nod(self,t,deg=8):
        k=self.ang['cabeza']; k.set(t,k(t),'hold'); k.set(t+0.3,deg,'io'); k.set(t+0.6,-deg*0.4,'io'); k.set(t+0.9,0,'soft'); return self
    def look(self,t,deg,dur=0.45):
        k=self.ang['cabeza']; k.set(t,k(t),'hold'); k.set(t+dur,deg,'soft'); return self
    def gesture(self,t,i=0):
        """gesto chico automatico por frase: alterna cabeza, mano, asentir"""
        k=i%4
        if k==0: self.nod(t,6)
        elif k==1: self.look(t,-7); self.look(t+1.4,0)
        elif k==2:
            h=self.ang['L_h']; h.set(t,h(t),'hold'); h.set(t+0.5,-14,'io'); h.set(t+1.3,0,'soft')
        else: self.look(t,6); self.look(t+1.2,0)
        return self
    def hold(self,obj,side='R',t0=0,t1=1e9):
        """pega un Obj a la mano (se dibuja en la posicion de la muneca)"""
        obj.on=max(obj.on,t0); obj.off=min(obj.off,t1); self.props.append((obj,side)); return self
    # ---- cinematica
    def _amp(self):
        """Amplitudes de la vida involuntaria (cabeza, brazos, respiracion, cabeceo).

        v3: 1,4 grados de cabeza y 1,2 % de respiracion. Medido sobre un cuadro a 405 px de ancho
        (como se ve en un telefono) eso son 0,3 px: el recorte se lee como una calcomania. La v4
        sube a 4,0 / 4,5 / 3 % — que a 1920 se nota y a 405 tambien — y reparte la fase POR RIG,
        para que dos personajes no respiren a la vez."""
        if not self.v4: return (1.4,1.6,0.012,0.0,0.55,0.70,0.30,1.10)
        k=self.vida
        return (4.0*k,4.5*k,0.030*k,2.6*k,0.47,0.61,self.fase,self.fase+1.9)
    def _cabeceo(self,t,amp):
        """Micro-cabeceo cada 3-6 s: un gesto corto de 0,55 s que rompe la respiracion periodica."""
        if amp<=0: return 0.0
        per=3.0+(self.fase/6.2832)*3.0                  # entre 3 y 6 s, distinto por rig
        u=(t+self.fase*0.7)%per
        if u>0.55: return 0.0
        return -amp*math.sin(math.pi*u/0.55)
    def pose(self,t):
        P=self.rig['piezas']; V=self.rig['pivotes']; s=self.sc; ox,oy=self.x(t),self.y(t)+self.bob
        if any(a<=t<=b for a,b in self.walks): oy+=abs(math.sin(t*2*math.pi*2.0))*-5   # bob al caminar
        AK,AB,AR,AN,WK,WB,F0,F1=self._amp()
        f={}
        for k,b in P.items(): f[k]=[(b[0]+b[2])/2,(b[1]+b[3])/2,0.0]
        r=self.ang['cabeza'](t)+AK*math.sin(t*WK+(0.3 if not self.v4 else F0))+self._cabeceo(t,AN)
        c=rot(f['cabeza'][:2],V['cabeza'],r); f['cabeza']=[c[0],c[1],r]
        hands={}
        for side in 'LR':
            idle=(1 if side=='L' else -1)*AB*math.sin(t*WB+((0 if side=='L' else 1.1) if not self.v4 else F1+(0 if side=='L' else 1.1)))
            rh=self.ang[side+'_h'](t)+idle; rc=self.ang[side+'_c'](t)-idle*0.6
            S=V['brazo_%s_sup'%side]; E=V['brazo_%s_inf'%side]
            cs=rot(f['brazo_%s_sup'%side][:2],S,rh); f['brazo_%s_sup'%side]=[cs[0],cs[1],rh]
            E2=rot(E,S,rh); ci=rot(rot(f['brazo_%s_inf'%side][:2],S,rh),E2,rc); f['brazo_%s_inf'%side]=[ci[0],ci[1],rh+rc]
            # muneca aprox = codo + vector codo->centro_inf * 1.6
            wx,wy=E2[0]+(ci[0]-E2[0])*1.55,E2[1]+(ci[1]-E2[1])*1.55; hands[side]=(ox+wx*s,oy+wy*s)
        resp=1+AR*math.sin(2*math.pi*t/2.8+(0.0 if not self.v4 else F0))
        out={k:(ox+v[0]*s,oy+v[1]*s,v[2]) for k,v in f.items()}
        return out,hands,resp
    def bbox(self,t):
        if not (self.on<=t<self.off) or self.a(t)<=0.02: return None
        pose,hands,resp=self.pose(t); xs=[];ys=[]
        for k in self.rig['orden']:
            im=self.pz[k]; cx,cy,r=pose[k]; w,h=_rot_extent(im.width,im.height,r)
            xs+= [cx-w/2,cx+w/2]; ys+=[cy-h/2,cy+h/2]
        for obj,sd in self.props:
            if obj.on<=t<obj.off:
                hx,hy=hands[sd]; s=obj.sc(t); w,h=_rot_extent(obj.img.width*s,obj.img.height*s,obj.rot(t)); xs+=[hx-w/2,hx+w/2]; ys+=[hy-h/2,hy+h/2]
        return (min(xs),min(ys),max(xs),max(ys))
    def draw(self,canvas,t,off=(0,0)):
        if not (self.on<=t<self.off): return
        pose,hands,resp=self.pose(t); a=self.a(t)
        for k in self.rig['orden']:
            im=self.pz[k]; cx,cy,r=pose[k]
            if k=='torso' and abs(resp-1)>0.002:
                im=im.resize((int(im.width*resp),int(im.height*resp)),Image.BILINEAR); cy-= (resp-1)*im.height/2
            if abs(r)>0.05: im=im.rotate(-r,resample=Image.BICUBIC,expand=True)
            if a<0.995: al=im.split()[3].point(lambda v:int(v*a)); im=im.copy(); im.putalpha(al)
            px,py=int(round(cx-im.width/2+off[0])),int(round(cy-im.height/2+off[1]))
            if self.shadow and a>0.5:
                sh=Image.new('RGBA',im.size,(30,24,18,0)); sh.putalpha(im.split()[3].point(lambda v:int(v*0.28))); canvas.alpha_composite(sh,(px+5,py+7))
            canvas.alpha_composite(im,(px,py))
            if k.endswith('_inf'):
                side=k.split('_')[1]
                for obj,sd in self.props:
                    if sd==side and obj.on<=t<obj.off:
                        hx,hy=hands[side]; obj.x=Track(hx); obj.y=Track(hy); obj.draw(canvas,t,off)

class MapSheet:
    """Hoja de mapa: base + capas con reveal (wipe oeste->este) o fade."""
    def __init__(self,x,y,sc,z=5,rot=0.0,base='mapa_base.png',pts='mapa_pts.json'):
        self.x,self.y,self.sc,self.z,self.r=x,y,sc,z,rot
        self.base=Image.open(os.path.join(ASSETS,base)).convert('RGBA')
        self.layers=[]   # (img, Track progreso, modo)
        self.routes=[]   # dicts
        self.pts=json.load(open(os.path.join(ASSETS,pts)))
        self.on=0.0; self.reveal=Track(0.0); self.a=Track(1.0); self.dark=Track(0.0); self.bg=True; self.name='mapa'
        self.w=int(self.base.width*sc); self.h=int(self.base.height*sc); self.depth=1.0
    def P(self,name):
        """pixel de composicion de un punto del mapa, YA CON LA ROTACION DE LA HOJA APLICADA.

        `draw()` compone la hoja rotada (`im.rotate(-self.r, expand=True)`) y recentrada, pero esta
        funcion devolvia el punto como si la hoja estuviera derecha. Todo lo que se ancla con G()
        quedaba corrido: hasta 4,7 px sobre la hoja, que en un plano cerrado (zoom 4,6) son 22 px en
        pantalla. Afectaba a TODOS los episodios: todos usan la hoja con una inclinacion de 0,3 a 1
        grado. Regla 2 de Agustin: los sitios del mapa son exactos."""
        p=self.pts[name]; u,v=p[0]*self.sc, p[1]*self.sc
        if abs(self.r)<=0.01: return (self.x+u, self.y+v)
        a=math.radians(self.r); dx,dy=u-self.w/2, v-self.h/2
        return (self.x+self.w/2 + dx*math.cos(a)-dy*math.sin(a),
                self.y+self.h/2 + dx*math.sin(a)+dy*math.cos(a))
    def add_layer(self,name,t_on,dur=1.5,mode='wipe',t_off=None,dur_off=1.0):
        im=Image.open(os.path.join(ASSETS,name)).convert('RGBA'); rv=Track(0.0); rv.set(t_on,0,'hold'); rv.set(t_on+dur,1,'io')
        if t_off is not None: rv.set(t_off,1,'hold'); rv.set(t_off+dur_off,0,'io')
        self.layers.append((im,rv,mode)); return self
    def route(self,names,t0,t1,color=(184,64,47),width=8,dotted=False,z=1,t_off=None):
        pts=[self.pts[n] for n in names]; self.routes.append({'pts':pts,'t0':t0,'t1':t1,'c':color,'w':width,'d':dotted,'off':t_off}); return self
    def _sheet(self,t):
        im=self.base.copy()
        rv=self.reveal(t)
        for lay,r,mode in self.layers:
            p=r(t)
            if p<=0: continue
            if mode=='wipe':
                l=lay if p>=1 else lay.crop((0,0,int(lay.width*p),lay.height)); im.alpha_composite(l,(0,0))
            else:
                l=lay if p>=1 else Image.merge('RGBA',lay.split()[:3]+(lay.split()[3].point(lambda v:int(v*p)),)); im.alpha_composite(l,(0,0))
        d=ImageDraw.Draw(im)
        for R in self.routes:
            if R['off'] is not None and t>=R['off']: continue
            p=(t-R['t0'])/(R['t1']-R['t0']); p=max(0,min(1,p))
            if p<=0: continue
            pts=R['pts']; L=sum(math.dist(a,b) for a,b in zip(pts,pts[1:])); target=L*p; acc=0; seg=[pts[0]]
            for a,b in zip(pts,pts[1:]):
                dl=math.dist(a,b)
                if acc+dl>=target:
                    u=(target-acc)/dl; seg.append((a[0]+(b[0]-a[0])*u,a[1]+(b[1]-a[1])*u)); break
                seg.append(b); acc+=dl
            if R['d']:
                for i in range(len(seg)-1):
                    a,b=seg[i],seg[i+1]; n=max(1,int(math.dist(a,b)/22))
                    for j in range(0,n,2):
                        u0,u1=j/n,min(1,(j+1)/n); d.line([(a[0]+(b[0]-a[0])*u0,a[1]+(b[1]-a[1])*u0),(a[0]+(b[0]-a[0])*u1,a[1]+(b[1]-a[1])*u1)],fill=R['c']+(255,),width=R['w'])
            else: d.line(seg,fill=R['c']+(255,),width=R['w'],joint='curve')
        dk=self.dark(t)
        if dk>0:
            ov=Image.new('RGBA',im.size,(34,32,28,int(255*dk*0.6))); im.alpha_composite(ov)
        if rv<1:
            m=Image.new('L',im.size,0); ImageDraw.Draw(m).rectangle([0,0,int(im.width*rv),im.height],fill=255); im.putalpha(Image.composite(im.split()[3],Image.new('L',im.size,0),m))
        return im
    def bbox(self,t): return None
    def draw(self,canvas,t,off=(0,0)):
        if t<self.on: return
        im=self._sheet(t)
        im=im.resize((self.w,self.h),Image.LANCZOS)
        # sombra de la hoja
        sh=Image.new('RGBA',im.size,(0,0,0,0)); sh.putalpha(im.split()[3].point(lambda v:min(v,120)).filter(ImageFilter.GaussianBlur(8)))
        if abs(self.r)>0.01: im=im.rotate(-self.r,resample=Image.BICUBIC,expand=True); sh=sh.rotate(-self.r,resample=Image.BICUBIC,expand=True)
        canvas.alpha_composite(sh,(int(self.x+10-(im.width-self.w)//2+off[0]),int(self.y+14-(im.height-self.h)//2+off[1])))
        canvas.alpha_composite(im,(int(self.x-(im.width-self.w)//2+off[0]),int(self.y-(im.height-self.h)//2+off[1])))

class Mundo:
    """v4 · El SUELO del video: una superficie mas grande que el cuadro por la que la camara vuela.

    Es lo que `MapSheet` no podia ser: `MapSheet` dibuja la hoja entera cada cuadro (el 65 % del
    tiempo de render del ep. 09) y despues se recorta; `Mundo` recorta primero y compone **solo el
    recorte** de cada capa activa. Y como el mundo puede medir 4000 px, un plano cerrado se ve a 1:1
    en vez de ser un upscale ×2-4 de un lienzo de 1920.

        mundo = M.Mundo('assets/mundo_estrecho.png', pts='assets/mundo_estrecho_pts.json')
        mundo.add_layer('assets/mundo_estrecho_esp.png', 12.0, 1.4)     # se pinta Espana
        sc = M.Scene(mundo, size=(1080,1920), v4=True)

    `pts` esta en px de MUNDO (lo escribe `produccion/mapa_v2.mundo`, de lon/lat: regla 24).
    """
    def __init__(self,base,pts=None,meta=None,nombre=''):
        self.base=base if isinstance(base,Image.Image) else Image.open(base).convert('RGB')
        if self.base.mode!='RGB': self.base=self.base.convert('RGB')
        self.w,self.h=self.base.size
        if isinstance(pts,str): pts=json.load(open(pts,encoding='utf-8'))
        if isinstance(pts,dict) and 'pts' in pts and isinstance(pts['pts'],dict):
            meta=meta or pts; pts=pts['pts']
        self.pts=pts or {}
        if isinstance(meta,str): meta=json.load(open(meta,encoding='utf-8'))
        self.meta=meta or {}
        self.nombre=nombre
        self.layers=[]     # (RGBA, Track 0..1, modo, (x,y))
        self.routes=[]
        self.dark=Track(0.0)
        self.bg=True; self.name='mundo:'+nombre; self.z=-1
    def P(self,name):
        """px de mundo de un sitio. Nunca a ojo: sale de la proyeccion que escribio mapa_v2."""
        p=self.pts[name]; return (float(p[0]),float(p[1]))
    def add_layer(self,png,t_on,dur=1.4,mode='fade',t_off=None,dur_off=1.0,xy=(0,0)):
        """Capa que se enciende cuando la voz lo pide (el color narra). `mode`: 'fade' o 'wipe'."""
        im=png if isinstance(png,Image.Image) else Image.open(png)
        im=im.convert('RGBA')
        if im.size!=(self.w,self.h) and xy==(0,0) and abs(im.width/max(1,im.height)-self.w/max(1,self.h))<0.02:
            im=im.resize((self.w,self.h),Image.LANCZOS)
        tr=Track(0.0); tr.set(t_on,0,'hold'); tr.set(t_on+dur,1,'io')
        if t_off is not None: tr.set(t_off,1,'hold'); tr.set(t_off+dur_off,0,'io')
        self.layers.append((im,tr,mode,(int(xy[0]),int(xy[1])))); return self
    def route(self,names,t0,t1,color=(184,64,47),width=8,dotted=False,z=1,t_off=None):
        pts=[self.P(n) for n in names]
        self.routes.append({'pts':pts,'t0':t0,'t1':t1,'c':color,'w':width,'d':dotted,'off':t_off}); return self
    def bbox(self,t): return None
    def crop(self,t,box):
        """Recorte RGBA del mundo en `box` (px de mundo) con las capas y rutas activas, compuestas
        SOLO dentro del recorte."""
        x0,y0,x1,y1=(int(round(v)) for v in box)
        x0=max(0,min(x0,self.w-1)); y0=max(0,min(y0,self.h-1))
        x1=max(x0+1,min(x1,self.w)); y1=max(y0+1,min(y1,self.h))
        im=self.base.crop((x0,y0,x1,y1)).convert('RGBA')
        for lay,tr,mode,(lx,ly) in self.layers:
            p=tr(t)
            if p<=0.002: continue
            ax0=max(x0,lx); ay0=max(y0,ly); ax1=min(x1,lx+lay.width); ay1=min(y1,ly+lay.height)
            if ax1<=ax0 or ay1<=ay0: continue
            if mode=='wipe' and p<1:
                xw=lx+lay.width*p
                if ax0>=xw: continue
                ax1=min(ax1,int(round(xw)))
                if ax1<=ax0: continue
            sub=lay.crop((ax0-lx,ay0-ly,ax1-lx,ay1-ly))
            if mode!='wipe' and p<1:
                b=sub.split(); sub=Image.merge('RGBA',b[:3]+(b[3].point(lambda v:int(v*p)),))
            im.alpha_composite(sub,(ax0-x0,ay0-y0))
        if self.routes:
            d=ImageDraw.Draw(im)
            for R in self.routes:
                if R['off'] is not None and t>=R['off']: continue
                p=max(0.0,min(1.0,(t-R['t0'])/max(1e-6,R['t1']-R['t0'])))
                if p<=0: continue
                pts=R['pts']; L=sum(math.dist(a,b) for a,b in zip(pts,pts[1:])); target=L*p; acc=0; seg=[pts[0]]
                for a,b in zip(pts,pts[1:]):
                    dl=math.dist(a,b)
                    if acc+dl>=target:
                        u=(target-acc)/max(1e-6,dl); seg.append((a[0]+(b[0]-a[0])*u,a[1]+(b[1]-a[1])*u)); break
                    seg.append(b); acc+=dl
                seg=[(px-x0,py-y0) for px,py in seg]
                if len(seg)<2: continue
                if R['d']:
                    for i in range(len(seg)-1):
                        a,b=seg[i],seg[i+1]; n=max(1,int(math.dist(a,b)/22))
                        for j in range(0,n,2):
                            u0,u1=j/n,min(1,(j+1)/n)
                            d.line([(a[0]+(b[0]-a[0])*u0,a[1]+(b[1]-a[1])*u0),(a[0]+(b[0]-a[0])*u1,a[1]+(b[1]-a[1])*u1)],fill=R['c']+(255,),width=R['w'])
                else: d.line(seg,fill=R['c']+(255,),width=R['w'],joint='curve')
        dk=self.dark(t)
        if dk>0:
            im.alpha_composite(Image.new('RGBA',im.size,(34,32,28,int(255*dk*0.72))))
        return im


class Scene:
    def __init__(self,fondo,size=None,v4=False):
        """`fondo`: ruta de PNG, Image o Mundo. `size`: (ancho, alto) DEL CUADRO; por defecto el
        global del modulo (1920x1080). `v4=True` enciende la vida por defecto (camara, objetos y
        rigs) y el flag de modulo `M.VIDA_V4`."""
        self.mundo=fondo if isinstance(fondo,Mundo) else None
        if self.mundo is not None: self.fondo=None
        else: self.fondo=fondo if isinstance(fondo,Image.Image) else Image.open(fondo)
        if self.fondo is not None and self.fondo.mode!='RGBA': self.fondo=self.fondo.convert('RGBA')
        self.W,self.H=(int(size[0]),int(size[1])) if size else (W,H)
        self.WM,self.HM=(self.mundo.w,self.mundo.h) if self.mundo is not None else self.fondo.size
        self.layers=[]; self.hud=[]
        self.cx=Track(self.WM/2); self.cy=Track(self.HM/2); self.zoom=Track(1.0)
        self.parallax=1.0; self.shakes=[]   # v3
        # v4
        _NOBJ[0]=0                          # fases de vida deterministas entre procesos del pool
        self.v4=bool(v4)
        if self.v4: set_v4(True)
        # `_compat`: el mundo mide exactamente lo que el cuadro (todas las producciones 01-S12).
        # En ese caso `render` y `window` recorren el camino de la v3, cuadro a cuadro identico.
        self._compat=(self.mundo is None and self.WM==self.W and self.HM==self.H)
        self.vida={'push':0.010,'push_max':0.14,'deriva':9.0} if self.v4 else None
        self._kfc=None
    def cam(self,t0,t1,xy,z,e='io'):
        """mueve la camara: de donde este en t0 a (xy, zoom) en t1"""
        self.cx.set(t0,self.cx(t0),'hold'); self.cy.set(t0,self.cy(t0),'hold'); self.zoom.set(t0,self.zoom(t0),'hold')
        self.cx.set(t1,xy[0],e); self.cy.set(t1,xy[1],e); self.zoom.set(t1,z,e); self._kfc=None; return self
    # ---- v3 camara
    def shake(self,t,amp=4,dur=0.22):
        """golpe de camara (sellos, dominos, stingers)"""
        self.shakes.append((t,amp,dur)); return self
    def whip(self,t,xy,z,dur=0.35):
        """barrido rapido hacia otra region de la misma hoja (en vez de corte)"""
        self.cam(t,t+dur,xy,z,'io'); ev(t,'whoosh',0.5); return self
    def _shake(self,t):
        dx=dy=0.0
        for t0,amp,dur in self.shakes:
            if t0<=t<t0+dur:
                u=(t-t0)/dur; k=amp*(1-u); dx+=k*math.sin(u*math.pi*9); dy+=k*0.7*math.cos(u*math.pi*7)
        return dx,dy
    # ---- v4 camara: corte + viaje, y vida por defecto en los tramos quietos
    def viaje(self,t0,t1,xy,z,e='io'):
        """`cam` con el nombre de la gramatica v4: un plano = un corte + UN viaje motivado.

        Igual que `cam` salvo en un detalle: no duplica el keyframe de arranque si `corte` ya puso
        uno en `t0`. Con el duplicado, la pista queda con tres o cuatro keyframes en el mismo
        instante y el orden entre ellos decide el resultado."""
        for pista,v in ((self.cx,xy[0]),(self.cy,xy[1]),(self.zoom,z)):
            if not any(abs(kk[0]-t0)<1e-9 for kk in pista.k): pista.set(t0,pista(t0),'hold')
            pista.set(t1,v,e)
        self._kfc=None; return self
    def corte(self,t,xy,z,tick=True):
        """Recolocacion seca de la camara en `t`, sin arrastrar el plano anterior.

        OJO con el keyframe de cierre en `t-0,001`. Si se pone con easing 'hold' —que es lo que
        parece natural y lo que hacen a mano las coreografias viejas— **congela el viaje del plano
        ANTERIOR entero**: en este motor el easing vive en el keyframe que TERMINA el tramo, asi que
        un 'hold' ahi le dice al tramo que va de 12,9 a 17,7 que no se mueva. Medido el 15-sep en
        `prueba_vida.py`, que arrastraba el bug: la camara no viajaba en ningun plano y nadie lo
        habia visto porque los objetos si se movian. El cierre HEREDA el easing del tramo en curso."""
        tp=max(0.0,t-0.001)
        for pista,v in ((self.cx,xy[0]),(self.cy,xy[1]),(self.zoom,z)):
            e=next((kk[2] for kk in pista.k if kk[0]>=tp),'io')
            pista.set(tp,pista(tp),e)
            # si el viaje anterior terminaba justo en `t`, su keyframe se va: en el instante exacto
            # del corte manda el plano NUEVO, no el que se acaba de cerrar en t-0,001.
            if t>0: pista.k=[kk for kk in pista.k if abs(kk[0]-t)>1e-9]
            pista.set(t,v,'hold')
        self._kfc=None
        if tick: ev(t,'tick',0.35)
        return self
    def _kf_cam(self):
        if self._kfc is None:
            self._kfc=sorted(set([k[0] for k in self.cx.k]+[k[0] for k in self.cy.k]+[k[0] for k in self.zoom.k]))
        return self._kfc
    def _vida_cam(self,t):
        """Deriva y push automaticos en los tramos HOLD (la camara nunca esta del todo quieta).

        Solo actua donde la coreo no manda: si entre el ultimo keyframe y `t` la camara ya se movio,
        devuelve cero y no se pisa con el viaje. El sentido de la deriva alterna por indice de
        keyframe para que dos planos seguidos no se vayan hacia el mismo lado. El push va SIEMPRE
        hacia dentro: alternarlo haria que un plano abierto se pegue al tope del mundo y se congele."""
        V=self.vida
        if not V or not self.v4: return (1.0,0.0,0.0)
        ts=self._kf_cam()
        i=0
        for j,tk in enumerate(ts):
            if tk<=t: i=j
            else: break
        tk=ts[i]; u=t-tk
        if u<=0.02: return (1.0,0.0,0.0)
        if (abs(self.zoom(t)-self.zoom(tk))>1e-6 or abs(self.cx(t)-self.cx(tk))>0.05
                or abs(self.cy(t)-self.cy(tk))>0.05):
            return (1.0,0.0,0.0)                         # hay viaje: la coreo manda
        push=min(V.get('push',0.010)*u,V.get('push_max',0.14))
        s=1.0 if i%2==0 else -1.0
        d=V.get('deriva',9.0)*ease_io(min(1.0,u/12.0))*s
        # la deriva se pide en px de CUADRO; la ventana vive en px de MUNDO: 1 px de cuadro = 1/z de mundo
        zef=max(1e-6,self.zoom(t)*(1.0+push))
        return (1.0+push,d/zef,d*0.32/zef)
    def _zoom_ef(self,t):
        k,_,_=self._vida_cam(t); return self.zoom(t)*k
    def add(self,*objs):
        for o in objs:
            o.scene=self
            if (self.v4 or VIDA_V4) and not getattr(o,'bg',False):
                if isinstance(o,Obj):
                    if o.wobble==0.0 and o.bob==0.0: o.wobble=0.35; o.bob=1.0
                elif isinstance(o,Rig): o.v4=True
            self.layers.append(o)
        return objs[0] if len(objs)==1 else objs
    def add_hud(self,*objs):
        """Capa de PANTALLA: px de cuadro, sin parallax, sin deriva, nunca recortada por la camara.
        Es donde viven los subtitulos, las cifras grandes, los chips y las barras."""
        for o in objs:
            o.scene=self; o.hud=True
            self.hud.append(o)
        return objs[0] if len(objs)==1 else objs
    def window(self,t):
        kz,dx,dy=self._vida_cam(t)
        z=self.zoom(t)*kz; sx,sy=self._shake(t)
        if self._compat:
            if z<=1.005:
                if abs(sx)+abs(sy)+abs(dx)+abs(dy)<0.01: return (0,0,self.W,self.H)
                z=1.012
        zmin=max(self.W/self.WM,self.H/self.HM)          # v4: se puede ABRIR hasta ver el mundo entero
        z=max(z,zmin)
        w,h=self.W/z,self.H/z
        cx=min(max(self.cx(t)+sx+dx,w/2),self.WM-w/2); cy=min(max(self.cy(t)+sy+dy,h/2),self.HM-h/2)
        return (cx-w/2,cy-h/2,cx+w/2,cy+h/2)
    def offset(self,o,t):
        """paralaje: las capas con depth>1 se desplazan mas que la hoja cuando la camara se mueve"""
        d=getattr(o,'depth',1.0)
        if self.parallax<=0 or abs(d-1)<1e-6 or getattr(o,'bg',False): return (0,0)
        x0,y0,x1,y1=self.window(t); cx,cy=(x0+x1)/2,(y0+y1)/2
        k=(d-1)*self.parallax
        return (-(cx-self.WM/2)*k,-(cy-self.HM/2)*k)
    def visible(self,t,ignorar=('rotulo:','region:','sub:','mundo:')):
        """v4 (§6.1.F) · Los objetos que CUENTAN como contenido en `t`: no-bg, dentro de la ventana,
        y con un nombre que no empiece por los prefijos ignorados. El rotulo de plano y la etiqueta
        de region no son contenido: contarlos es lo que dejaba pasar los 24 s vacios del ep. 09."""
        def ok(o):
            n=getattr(o,'name','') or ''
            return not any(n.startswith(p) for p in ignorar)
        out=[]
        x0,y0,x1,y1=self.window(t)
        for o in self.layers:
            if getattr(o,'bg',False) or not ok(o): continue
            b=o.bbox(t)
            if b is None: continue
            ox,oy=self.offset(o,t); b=(b[0]+ox,b[1]+oy,b[2]+ox,b[3]+oy)
            if b[2]<x0 or b[0]>x1 or b[3]<y0 or b[1]>y1: continue
            out.append(o)
        for o in self.hud:
            if getattr(o,'bg',False) or not ok(o): continue
            b=o.bbox(t)
            if b is None: continue
            if b[2]<0 or b[0]>self.W or b[3]<0 or b[1]>self.H: continue
            out.append(o)
        return out
    def check_framing(self,t0,t1,step=0.25,tol=3):
        """devuelve [(t,nombre,bbox,ventana)] con todo objeto visible que cruza el borde sin estar en transito"""
        bad=[]; t=t0
        while t<t1:
            x0,y0,x1,y1=self.window(t)
            for o in self.layers:
                if getattr(o,'bg',False): continue
                b=o.bbox(t)
                if b is None: continue
                if any(a<=t<=c for a,c in getattr(o,'transit',[])): continue
                ox,oy=self.offset(o,t); b=(b[0]+ox,b[1]+oy,b[2]+ox,b[3]+oy)
                inter=not(b[2]<x0 or b[0]>x1 or b[3]<y0 or b[1]>y1)
                inside=b[0]>=x0-tol and b[1]>=y0-tol and b[2]<=x1+tol and b[3]<=y1+tol
                if inter and not inside: bad.append((round(t,2),getattr(o,'name','') or type(o).__name__,tuple(int(v) for v in b),tuple(int(v) for v in (x0,y0,x1,y1))))
            for o in self.hud:                           # el HUD se verifica contra el CUADRO
                if getattr(o,'bg',False): continue
                b=o.bbox(t)
                if b is None: continue
                if any(a<=t<=c for a,c in getattr(o,'transit',[])): continue
                inter=not(b[2]<0 or b[0]>self.W or b[3]<0 or b[1]>self.H)
                inside=b[0]>=-tol and b[1]>=-tol and b[2]<=self.W+tol and b[3]<=self.H+tol
                if inter and not inside: bad.append((round(t,2),'HUD '+(getattr(o,'name','') or type(o).__name__),tuple(int(v) for v in b),(0,0,self.W,self.H)))
            t+=step
        return bad
    def report(self,t0,t1,gap=6.0):
        """v3: ritmo. Huecos > gap s sin ningun evento (sonoro = visual) y cortes por minuto (eventos 'tick')."""
        ts=sorted(set(t for t,k,v in EVENTS if t0<=t<=t1)); holes=[]; prev=t0
        for t in ts+[t1]:
            if t-prev>gap: holes.append((round(prev,1),round(t,1)))
            prev=t
        cuts=sum(1 for t,k,v in EVENTS if k=='tick' and t0<=t<=t1)
        return {'huecos':holes,'cortes':cuts,'cortes_por_min':round(cuts/max(1e-6,(t1-t0)/60),1)}
    def render(self,t):
        if self._compat:
            # camino de la v3, intacto: se dibuja sobre el lienzo entero y se recorta al final.
            c=self.fondo.copy()
            for o in sorted(self.layers,key=lambda o:o.z):
                off=self.offset(o,t)
                if abs(off[0])+abs(off[1])>0.5: o.draw(c,t,off)
                else: o.draw(c,t)
            if self._zoom_ef(t)>1.005:
                x0,y0,x1,y1=self.window(t)
                c=c.crop((int(x0),int(y0),int(x1),int(y1))).resize((self.W,self.H),Image.LANCZOS)
            if self.hud: self._dibujar_hud(c,t)
            return c
        # ---- v4: se RECORTA primero y se dibuja solo lo que interseca la ventana
        x0,y0,x1,y1=self.window(t)
        ix0,iy0=int(round(x0)),int(round(y0))
        ix1,iy1=max(ix0+2,int(round(x1))),max(iy0+2,int(round(y1)))
        if self.mundo is not None: c=self.mundo.crop(t,(ix0,iy0,ix1,iy1))
        else: c=self.fondo.crop((ix0,iy0,ix1,iy1)).copy()
        base=(-ix0,-iy0)
        mx,my=(ix1-ix0)*0.15,(iy1-iy0)*0.15              # margen: un objeto medio fuera igual se ve
        for o in sorted(self.layers,key=lambda o:o.z):
            b=o.bbox(t)
            if b is not None and (b[2]<x0-mx or b[0]>x1+mx or b[3]<y0-my or b[1]>y1+my): continue
            ox,oy=self.offset(o,t)
            o.draw(c,t,(base[0]+ox,base[1]+oy))
        if (ix1-ix0,iy1-iy0)!=(self.W,self.H): c=c.resize((self.W,self.H),Image.LANCZOS)
        if self.hud: self._dibujar_hud(c,t)
        return c
    def _dibujar_hud(self,c,t):
        for o in sorted(self.hud,key=lambda o:o.z): o.draw(c,t)
    # ------------------------------------------------------------ v4: subtitulos como HUD
    def subtitulos(self,palabras,grupos=(2,4),estilo='banda',fy=0.86,resaltar=(),ancho=0.86,
                   size=None,z=95,fade=0.08,pausa=0.25,t0=0.0,t1=1e9,mayus=True,hueco=0.0):
        """v4 · Subtitulo palabra a palabra a partir de `[(palabra, t0, t1)]` (`audio/_palabras.json`).

        Agrupa de 2 a 4 palabras cortando por puntuacion y por pausas de mas de `pausa` segundos, y
        no deja una palabra debil al final del grupo (`DEBILES`). Cada grupo es UN objeto del HUD:
        vive en px de cuadro, asi que **puede cruzar un corte de camara** sin partirse y sin
        achicarse con el zoom — que era el problema estructural del motor v3 (carencia M3).

        `resaltar`: palabras que van en rojo (la del dato). `estilo`: 'banda' (banda oscura
        translucida, se lee sobre el mapa) o 'papel' (tarjeta de papel, para planos de mesa).
        Devuelve la lista de objetos creados.
        """
        import props as PR
        W_,H_=self.W,self.H
        res={str(x).strip('.,;:!?"’\'').lower() for x in resaltar}
        pal=[(str(w),float(a),float(b)) for w,a,b in palabras if t0-1e-9<=float(a)<=t1]
        if not pal: return []
        gr=agrupar(pal,grupos=grupos,pausa=pausa)
        # ---- 2. un objeto de HUD por grupo.
        # RELEVO, NO FUNDIDO CRUZADO. La primera version daba a cada grupo [t0-fade, t1+fade]: como
        # las palabras van pegadas, dos grupos seguidos se solapaban 0,14 s y en ese tramo se veian
        # LOS DOS TEXTOS ENCIMA, ilegibles (se cazo en la hoja de contacto de Ceuta, t = 5,2 s).
        # Ahora cada grupo vive hasta que empieza el siguiente y ni un cuadro mas: `off` del grupo N
        # es exactamente `on` del N+1, y como la ventana es [on, off) nunca coinciden. Si despues
        # del grupo viene una pausa larga, el texto aguanta 1,2 s y se va (si no, se queda quieto
        # en pantalla y `sync.py` lo marca como TEXTO_VIEJO, con razon).
        s=size or int(W_*0.062)
        fnt=PR.FONTC(s); anc=int(W_*ancho)
        out=[]
        for i,g in enumerate(gr):
            txt=' '.join(w for w,_,_ in g)
            a0=g[0][1]; a1=g[-1][2]
            fin=min(gr[i+1][0][1],a1+1.2) if i+1<len(gr) else a1+max(0.35,hueco)
            fin=max(fin,a0+2.2*fade+0.02)
            im=self._sub_img(txt,fnt,anc,estilo,res,mayus)
            o=Obj(im,z=z); o.name='sub:'+txt; o.bg=False; o.shadow=(estilo=='papel')
            o.x=Track(W_/2.0); o.y=Track(H_*fy); o.wobble=0.0; o.bob=0.0; o.vida=0.0
            o.on=a0; o.off=fin
            o.a.set(a0,0,'hold'); o.a.set(a0+fade,1,'io')
            o.a.set(fin-fade,1,'hold'); o.a.set(fin,0,'io')
            self.add_hud(o); out.append(o)
        return out
    def _sub_img(self,txt,fnt,anc,estilo,res,mayus=True):
        """Dibuja un grupo de subtitulo. 'banda': banda oscura translucida + crema (se lee sobre
        cualquier mapa). 'papel': tinta sobre una tarjeta de papel con halo (planos de mesa)."""
        import props as PR
        t=txt.upper() if mayus else txt
        d0=ImageDraw.Draw(Image.new('L',(8,8)))
        pals=t.split()
        anchos=[d0.textlength(p+' ',font=fnt) for p in pals]
        lineas=[[]]; acc=0.0
        for p,w_ in zip(pals,anchos):
            if acc+w_>anc and lineas[-1]: lineas.append([]); acc=0.0
            lineas[-1].append(p); acc+=w_
        lh=int(fnt.size*1.24)
        wmax=int(max(sum(d0.textlength(p+' ',font=fnt) for p in ln)-d0.textlength(' ',font=fnt) for ln in lineas))
        pad=int(fnt.size*0.52)
        W0,H0=wmax+2*pad,lh*len(lineas)+int(pad*1.1)
        if estilo=='papel':
            im=Image.new('RGBA',(W0,H0),(0,0,0,0)); d=ImageDraw.Draw(im)
            d.rounded_rectangle([0,0,W0-1,H0-1],radius=int(pad*0.5),fill=PR.PAPEL+(238,))
            d.rounded_rectangle([6,6,W0-7,H0-7],radius=int(pad*0.4),outline=PR.TINTA+(210,),width=3)
            base,alto=PR.TINTA,PR.ROJO
        else:
            im=Image.new('RGBA',(W0,H0),(0,0,0,0)); d=ImageDraw.Draw(im)
            d.rounded_rectangle([0,0,W0-1,H0-1],radius=int(pad*0.45),fill=(26,24,21,214))
            base,alto=(247,241,226),(232,96,78)
        y=H0/2-(len(lineas)-1)*lh/2
        for ln in lineas:
            anchura=sum(d0.textlength(p+' ',font=fnt) for p in ln)-d0.textlength(' ',font=fnt)
            x=(W0-anchura)/2
            for p in ln:
                col=alto if p.strip('.,;:!?"’\'').lower() in res else base
                if estilo!='papel':
                    for dx,dy in ((-2,0),(2,0),(0,-2),(0,2)):
                        d.text((x+dx,y+dy),p,font=fnt,fill=(14,13,11,235),anchor='lm')
                d.text((x,y),p,font=fnt,fill=col+(255,),anchor='lm')
                x+=d0.textlength(p+' ',font=fnt)
            y+=lh
        return im

def prop(name,**kw):
    o=Obj(os.path.join(ASSETS,'prop_%s.png'%name),**kw); o.name=name; return o

# ---------------------------------------------------------------- render paralelo
def _worker(args):
    build_module,func,i0,i1,outdir=args
    import importlib; m=importlib.import_module(build_module); sc=getattr(m,func)()
    for i in range(i0,i1):
        fr=sc.render(i/FPS).convert('RGB'); fr.save(os.path.join(outdir,'f_%06d.jpg'%i),quality=92)
    return i1-i0
def render(build_module,func,dur,out_mp4,audio=None,workers=None,t0=0.0,frames=None):
    """frames: directorio propio de cuadros. Sin el, usa produccion/_frames (comportamiento viejo).
    Cada produccion debe pasar el suyo (canal/ESTRUCTURA.md §4.1): asi dos renders no se pisan
    y no se borran los cuadros de otro episodio que este corriendo."""
    import multiprocessing as mp, subprocess, shutil, time
    outdir=frames or os.path.join(BASE,'_frames'); shutil.rmtree(outdir,ignore_errors=True); time.sleep(0.5); os.makedirs(outdir,exist_ok=True)
    n=int(dur*FPS); i_start=int(t0*FPS); workers=workers or max(1,(os.cpu_count() or 4)-2)
    # v4: el formato sale del PRIMER CUADRO, no de los globales del modulo (hay escenas verticales).
    import importlib
    _m=importlib.import_module(build_module); _sc=getattr(_m,func)()
    _fw,_fh=_sc.render(i_start/FPS).size
    print('formato %dx%d  ·  %d cuadros  ·  %d workers'%(_fw,_fh,n-i_start,workers),flush=True)
    del _sc,_m
    chunks=[]; step=max(24,(n-i_start)//(workers*6))
    for i in range(i_start,n,step): chunks.append((build_module,func,i,min(n,i+step),outdir))
    with mp.Pool(workers) as pool:
        done=0
        for k in pool.imap_unordered(_worker,chunks): done+=k
    cmd=['ffmpeg','-v','error','-y','-start_number',str(i_start),'-framerate',str(FPS),'-i',os.path.join(outdir,'f_%06d.jpg')]
    if audio: cmd+=['-ss',str(t0),'-i',audio]
    cmd+=['-c:v','libx264','-pix_fmt','yuv420p','-crf','19']
    if audio: cmd+=['-c:a','aac','-b:a','192k','-shortest']
    cmd.append(out_mp4); subprocess.run(cmd,check=True); return out_mp4
