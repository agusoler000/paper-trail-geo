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
"""
import json, math, os
from PIL import Image, ImageDraw, ImageFilter
W,H=1920,1080; FPS=24
EVENTS=[]   # (t, kind, vol) -> mezcla.py
def ev(t,kind,vol=1.0): EVENTS.append((round(float(t),3),kind,vol))
BASE=os.path.dirname(os.path.abspath(__file__)); ASSETS=os.path.join(BASE,'assets'); ELENCO=os.path.join(BASE,'..','pruebas','elenco')

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
        self.wobble=0.0; self.phase=(id(self)%97)/97*6.28; self.sfx='pop'
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
    def slide_off(self,t,side='R',dur=0.6):
        """se desliza fuera de la hoja por un lado (transito, no cuenta como cortado)"""
        x0,y0=self.x(t),self.y(t); x1=W+self.img.width if side=='R' else -self.img.width
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
    def bbox(self,t):
        if not (self.on<=t<self.off): return None
        a=self.a(t); s=self.sc(t)
        if a<=0.02 or s<=0.01: return None
        w,h=self.img.width*s,self.img.height*s*self.sy(t); r=self.rot(t)+(self.wobble*math.sin(t*0.9+self.phase) if self.wobble else 0)
        w,h=_rot_extent(w,h,r); cx,cy=self.x(t),self.y(t)
        return (cx-w/2,cy-h/2,cx+w/2,cy+h/2)
    def draw(self,canvas,t,off=(0,0)):
        if not (self.on<=t<self.off): return
        a=self.a(t); s=self.sc(t); sy=self.sy(t)
        if a<=0.01 or s<=0.01 or sy<=0.01: return
        im=self.img
        if abs(s-1)>0.005 or abs(sy-1)>0.005: im=im.resize((max(1,int(im.width*s)),max(1,int(im.height*s*sy))),Image.BILINEAR)
        r=self.rot(t)+(self.wobble*math.sin(t*0.9+self.phase) if self.wobble else 0)
        if abs(r)>0.05: im=im.rotate(-r,resample=Image.BICUBIC,expand=True)
        if a<0.995:
            al=im.split()[3].point(lambda v:int(v*a)); im=im.copy(); im.putalpha(al)
        px,py=int(round(self.x(t)-im.width/2+off[0])),int(round(self.y(t)-im.height/2+off[1]))
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
    # ---- acciones
    def enter(self,t,side='R',dur=1.1,home=None):
        hx=home[0] if home else self.x(t+dur); hy=home[1] if home else self.y(t+dur)
        sx=W+400 if side=='R' else -700
        self.on=min(self.on,t); self.x.set(t,sx,'hold'); self.y.set(t,hy,'hold'); self.x.set(t+dur*0.85,hx-25 if side=='R' else hx+25,'out'); self.x.set(t+dur,hx,'io'); ev(t,'whoosh'); ev(t+dur*0.85,'clack',0.5)
        self.transit.append((t,t+dur+0.4)); return self
    def exit(self,t,side='R',dur=1.0):
        x0=self.x(t); self.x.set(t,x0,'hold'); self.x.set(t+dur,W+400 if side=='R' else -700,'in'); self.off=t+dur; ev(t,'whoosh',0.7); self.transit.append((t,t+dur)); return self
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
    def pose(self,t):
        P=self.rig['piezas']; V=self.rig['pivotes']; s=self.sc; ox,oy=self.x(t),self.y(t)+self.bob
        if any(a<=t<=b for a,b in self.walks): oy+=abs(math.sin(t*2*math.pi*2.0))*-5   # bob al caminar
        f={}
        for k,b in P.items(): f[k]=[(b[0]+b[2])/2,(b[1]+b[3])/2,0.0]
        r=self.ang['cabeza'](t)+1.4*math.sin(t*0.55+0.3); c=rot(f['cabeza'][:2],V['cabeza'],r); f['cabeza']=[c[0],c[1],r]
        hands={}
        for side in 'LR':
            idle=(1 if side=='L' else -1)*1.6*math.sin(t*0.7+(0 if side=='L' else 1.1))
            rh=self.ang[side+'_h'](t)+idle; rc=self.ang[side+'_c'](t)-idle*0.6
            S=V['brazo_%s_sup'%side]; E=V['brazo_%s_inf'%side]
            cs=rot(f['brazo_%s_sup'%side][:2],S,rh); f['brazo_%s_sup'%side]=[cs[0],cs[1],rh]
            E2=rot(E,S,rh); ci=rot(rot(f['brazo_%s_inf'%side][:2],S,rh),E2,rc); f['brazo_%s_inf'%side]=[ci[0],ci[1],rh+rc]
            # muneca aprox = codo + vector codo->centro_inf * 1.6
            wx,wy=E2[0]+(ci[0]-E2[0])*1.55,E2[1]+(ci[1]-E2[1])*1.55; hands[side]=(ox+wx*s,oy+wy*s)
        resp=1+0.012*math.sin(2*math.pi*t/2.8)
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

class Scene:
    def __init__(self,fondo):
        self.fondo=Image.open(fondo).convert('RGBA'); self.layers=[]
        self.cx=Track(W/2); self.cy=Track(H/2); self.zoom=Track(1.0)
        self.parallax=1.0; self.shakes=[]   # v3
    def cam(self,t0,t1,xy,z,e='io'):
        """mueve la camara: de donde este en t0 a (xy, zoom) en t1"""
        self.cx.set(t0,self.cx(t0),'hold'); self.cy.set(t0,self.cy(t0),'hold'); self.zoom.set(t0,self.zoom(t0),'hold')
        self.cx.set(t1,xy[0],e); self.cy.set(t1,xy[1],e); self.zoom.set(t1,z,e); return self
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
    def add(self,*objs):
        for o in objs: self.layers.append(o)
        return objs[0] if len(objs)==1 else objs
    def window(self,t):
        z=self.zoom(t); sx,sy=self._shake(t)
        if z<=1.005:
            if abs(sx)+abs(sy)<0.01: return (0,0,W,H)
            z=1.012
        w,h=W/z,H/z; cx=min(max(self.cx(t)+sx,w/2),W-w/2); cy=min(max(self.cy(t)+sy,h/2),H-h/2)
        return (cx-w/2,cy-h/2,cx+w/2,cy+h/2)
    def offset(self,o,t):
        """paralaje: las capas con depth>1 se desplazan mas que la hoja cuando la camara se mueve"""
        d=getattr(o,'depth',1.0)
        if self.parallax<=0 or abs(d-1)<1e-6 or getattr(o,'bg',False): return (0,0)
        x0,y0,x1,y1=self.window(t); cx,cy=(x0+x1)/2,(y0+y1)/2
        k=(d-1)*self.parallax
        return (-(cx-W/2)*k,-(cy-H/2)*k)
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
        c=self.fondo.copy()
        for o in sorted(self.layers,key=lambda o:o.z):
            off=self.offset(o,t)
            if abs(off[0])+abs(off[1])>0.5: o.draw(c,t,off)
            else: o.draw(c,t)
        z=self.zoom(t)
        if z>1.005:
            x0,y0,x1,y1=self.window(t)
            c=c.crop((int(x0),int(y0),int(x1),int(y1))).resize((W,H),Image.LANCZOS)
        return c

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
