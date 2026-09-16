"""Puesta en escena aditiva: actores, mecanismos, comparaciones y mapas exactos.

Coordenadas de composicion en 1280x720; rasterizado nativo al tamano solicitado.
No cambia las clases ni los valores por defecto de motor/compo.
"""
from functools import lru_cache
import json
import math
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))
import motor as M
import props as PR
import mapa_v2 as MV

INK = (30, 47, 49)
PAPER = (243, 240, 225)
TEAL = (33, 112, 118)
RED = (181, 61, 47)
GOLD = (213, 157, 52)
GREEN = (112, 144, 113)
MUTED = (109, 125, 123)
PALE = (218, 230, 224)
COLORS = (TEAL, RED, GOLD, GREEN, (68, 92, 147))
PLACES = {'Washington': (-77.0369, 38.9072), 'Tokyo': (139.6917, 35.6895),
          'London': (-.1276, 51.5072), 'Beijing': (116.4074, 39.9042),
          'Ohio': (-82.8, 40.2), 'Columbus': (-82.9988, 39.9612),
          'Argentina': (-64.0, -34.0), 'Greece': (23.7275, 37.9838),
          'Athens': (23.7275, 37.9838), 'Buenos Aires': (-58.3816, -34.6037),
          'United States': (-98.5, 39.8), 'Britain': (-2.5, 54.0),
          'Mississippi': (-89.7, 32.7), 'New York': (-74.006, 40.7128)}


def clamp(x):
    return min(1., max(0., x))


def smooth(x):
    x = clamp(x)
    return x*x*(3-2*x)


def mix(a, b, u):
    return a + (b-a)*u


@lru_cache(maxsize=256)
def font(size, sans=False):
    path = 'C:/Windows/Fonts/arialbd.ttf' if sans else 'C:/Windows/Fonts/GeorgiaPro-Bold.ttf'
    return ImageFont.truetype(path, max(8, int(size)))


@lru_cache(maxsize=8)
def fondo(w, h, oscuro=False):
    rng = np.random.default_rng(140)
    tex = rng.normal(0, .85, (h, w, 1))
    color = (37, 64, 66) if oscuro else (222, 232, 226)
    a = np.clip(np.array(color)+tex, 0, 255).astype('uint8')
    return Image.fromarray(a).convert('RGBA')


@lru_cache(maxsize=256)
def asset(path):
    with Image.open(path) as im:
        return im.convert('RGBA')


@lru_cache(maxsize=128)
def mapa(region, w):
    """Natural Earth y Mercator existentes, con rotulos dibujados aparte de la camara."""
    boxes = {'us': (-128, -63, 23, 53), 'world': (-170, 170, -53, 73),
             'europe': (-16, 38, 33, 61), 'britain': (-12, 5, 48, 61),
             'ohio': (-88, -76, 35, 44), 'east_us': (-92, -66, 29, 46),
             'asia': (91, 147, 17, 52)}
    bbox = boxes[region]
    pj, _, h = MV.proyeccion(*bbox, w)
    rng = np.random.default_rng(101)
    noise = rng.normal(0, 1.0, (h, w, 1))
    sea = np.clip(np.array((76, 142, 154))+noise, 0, 255).astype('uint8')
    im = Image.fromarray(sea).convert('RGBA')
    d = ImageDraw.Draw(im)
    from shapely.geometry import shape, box
    clip = box(bbox[0], bbox[2], bbox[1], bbox[3])
    for feature in MV.datos()['features']:
        g = shape(feature['geometry'])
        if not g.intersects(clip):
            continue
        g = g.intersection(clip)
        geoms = list(g.geoms) if hasattr(g, 'geoms') else [g]
        for poly in geoms:
            if poly.geom_type != 'Polygon':
                continue
            points = [pj(*p) for p in poly.exterior.coords]
            d.polygon(points, fill=(213, 222, 192), outline=(103, 133, 120), width=2)
            for ring in poly.interiors:
                d.polygon([pj(*p) for p in ring.coords], fill=(76, 142, 154))
    return im, bbox


class Lienzo:
    def __init__(self, width=1920, oscuro=False):
        self.w, self.h = width, width*9//16
        self.k = width/1280
        self.im = fondo(self.w, self.h, oscuro).copy()
        self.d = ImageDraw.Draw(self.im)
        self.boxes = []
        self.foreground = PAPER if oscuro else INK

    def coords(self, p):
        return tuple(round(v*self.k) for v in p)

    def rect(self, box, fill, outline=None, width=1, radius=0):
        self.d.rounded_rectangle(self.coords(box), radius=round(radius*self.k), fill=fill,
                                 outline=outline, width=max(1, round(width*self.k)))

    def line(self, points, fill=INK, width=2):
        self.d.line([self.coords(p) for p in points], fill=fill, width=max(1, round(width*self.k)))

    def ellipse(self, box, fill, outline=None, width=1):
        self.d.ellipse(self.coords(box), fill=fill, outline=outline, width=max(1, round(width*self.k)))

    def poly(self, points, fill):
        self.d.polygon([self.coords(p) for p in points], fill=fill)

    def text(self, txt, xy, size=28, color=None, maxw=1100, anchor='mm', sans=False):
        txt = str(txt)
        color = color or self.foreground
        s = int(size*self.k)
        while s > 12 and max(font(s, sans).getlength(l) for l in txt.split('\n')) > maxw*self.k:
            s -= 1
        f = font(s, sans)
        xy = self.coords(xy)
        bb = self.d.multiline_textbbox(xy, txt, font=f, anchor=anchor, align='center', spacing=7)
        if min(bb[:2]) < 0 or bb[2] > self.w or bb[3] > self.h:
            raise ValueError('Texto fuera de cuadro: %s %s' % (txt, bb))
        self.d.multiline_text(xy, txt, font=f, fill=color, anchor=anchor, align='center', spacing=7)
        self.boxes.append(('texto', bb))

    def image(self, img, xy, width=None, height=None, angle=0, alpha=1, name='imagen'):
        if isinstance(img, (str, Path)):
            img = asset(str(img))
        scale = min(width/img.width if width else 1e6, height/img.height if height else 1e6)
        if scale == 1e6:
            scale = 1
        sz = (max(1, round(img.width*scale*self.k)), max(1, round(img.height*scale*self.k)))
        img = img.resize(sz, Image.Resampling.BILINEAR)
        if abs(angle) > .05:
            img = img.rotate(angle, Image.Resampling.BICUBIC, expand=True)
        if alpha < 1:
            img.putalpha(img.getchannel('A').point(lambda x: round(x*clamp(alpha))))
        x, y = self.coords(xy)
        x, y = round(x-img.width/2), round(y-img.height/2)
        if x < 0 or y < 0 or x+img.width > self.w or y+img.height > self.h:
            raise ValueError('Imagen fuera de cuadro: %s %s' % (name, (x, y, img.size)))
        self.im.alpha_composite(img, (x, y))
        self.boxes.append((name, (x, y, x+img.width, y+img.height)))

    def arrow(self, a, b, color=TEAL, width=4, progress=1):
        if progress <= 0:
            return
        q = (mix(a[0], b[0], clamp(progress)), mix(a[1], b[1], clamp(progress)))
        self.line([a, q], color, width)
        theta = math.atan2(q[1]-a[1], q[0]-a[0])
        pts = [q, (q[0]-14*math.cos(theta-.45), q[1]-14*math.sin(theta-.45)),
               (q[0]-14*math.cos(theta+.45), q[1]-14*math.sin(theta+.45))]
        self.poly(pts, color)

    def coin(self, xy, r=19, color=GOLD):
        x, y = xy
        self.ellipse((x-r+3, y-r+4, x+r+3, y+r+4), (128, 132, 112))
        self.ellipse((x-r, y-r, x+r, y+r), color, INK, 2)
        self.text('$', xy, r*1.25, INK, maxw=r*2)

    def paper(self, box, title='', amount='', color=INK):
        x0,y0,x1,y1 = box
        self.rect((x0+5,y0+7,x1+5,y1+7), (157,172,162))
        self.rect(box, PAPER, (123,135,125), 1, 2)
        if title:
            self.text(title, ((x0+x1)/2,y0+31), 23, color, x1-x0-24)
        if y1-y0 > 75:
            self.line([(x0+18,y0+53),(x1-18,y0+53)], MUTED, 1)
        elif not title and not amount:
            for f in (.3,.5,.7):
                self.line([(x0+5,y0+(y1-y0)*f),(x1-5,y0+(y1-y0)*f)], MUTED, 1)
        if amount:
            self.text(amount, ((x0+x1)/2,(y0+y1)/2+12), 44, color, x1-x0-24)
        else:
            for i in range(3):
                yy = y0+80+i*26
                if yy < y1-15:
                    self.line([(x0+22,yy),(x1-22-i*13,yy)], (167,170,157), 2)


class Plano:
    def __init__(self, spec, lineas, palabras, base, width=1920):
        self.spec, self.base, self.width = spec, Path(base), width
        self.start, self.end = spec['start'], spec['end']
        self.dur = self.end-self.start
        self.lineas = lineas
        self.words = [(w,a-self.start,b-self.start) for w,a,b in palabras if self.start <= a < self.end]
        self.rigs = {}
        self.events = []
        self.oscuro = spec['kind'] in ('document','question','receipt')
        self.sub = M.Scene(Image.new('RGBA',(1,1)), size=(width,width*9//16), v4=True)
        self.sub.vida = None
        self.sub.subtitulos(self.words, size=round(width*.024), fy=.916, ancho=.88, fade=.025,
                           resaltar=('debt','interest','bill','paid','you','forty','trillion'))

    def at(self, i):
        return self.lineas[(self.spec['beat'], i)]['inicio']-self.start

    def reveal(self, i, t):
        rs = self.spec.get('reveals', [])
        when = self.at(rs[i]) if i < len(rs) else .2+i*min(1.4,self.dur/6)
        return smooth((t-when)/.7)

    def cue(self, key, default):
        return self.at(self.spec['cues'][key]) if key in self.spec.get('cues',{}) else default

    def prop(self, name):
        paths = [self.base/'arte/assets'/('prop_'+name+'.png'), BASE/'assets'/('prop_'+name+'.png')]
        for p in paths:
            if p.exists():
                return p
        raise FileNotFoundError(name)

    def actor(self, c, name, x, t, on=0, reaction=None):
        key = (name,x,on,reaction)
        if key not in self.rigs:
            r = M.Rig(name,0,0,sc=.40*c.k,on=on,off=self.dur+1)
            b = r.bbox(on)
            r.x = M.Track(x*c.k-(b[0]+b[2])/2)
            r.y = M.Track(540*c.k-b[3])
            r.vida, r.v4, r.depth = .4, True, 1
            for j, tt in enumerate([l['inicio']-self.start for l in self.lineas.values()
                                    if self.start <= l['inicio'] < self.end]):
                r.gesture(max(on,tt)+.3,j)
            if reaction is not None:
                r.lean(reaction, deg=-7 if x>640 else 7, hold=1.3)
                r.point_at(reaction+1.8,(640*c.k,360*c.k),side='L' if x>640 else 'R',hold=1.4)
            self.rigs[key]=r
        r=self.rigs[key]
        if t < on:
            return
        c.ellipse((x-86,528,x+86,549),(150,170,159))
        bb=r.bbox(t)
        if bb and (bb[0]<0 or bb[1]<0 or bb[2]>c.w or bb[3]>c.h*.84):
            raise ValueError('Rig fuera de zona segura: '+name)
        r.draw(c.im,t)

    def heading(self,c):
        c.text('PAPER TRAIL  /  THE RECEIPT',(64,32),13,MUTED,anchor='lm',sans=True)
        c.text(self.spec['title'],(640,87),36,maxw=1130)
        c.line([(64,124),(1216,124)],TEAL if not self.oscuro else GOLD,2)

    def fmt(self,v):
        unit=self.spec.get('unit','')
        s=('%g'%v) if isinstance(v,(int,float)) else str(v)
        if unit in ('$T','$B','$M'):
            return '$'+s+unit[-1]
        if unit=='$':
            return '$'+format(v,',.0f')
        return s+(' ' if unit and unit[0].isalpha() else '')+unit

    def frame(self,t):
        c=Lienzo(self.width,self.oscuro)
        self.heading(c)
        method=getattr(self,'draw_'+self.spec['kind'],None)
        if method is None:
            raise ValueError('Tipo visual no soportado: '+self.spec['kind'])
        method(c,t)
        self.sub._dibujar_hud(c.im,t)
        return c.im.convert('RGB')

    def draw_map(self,c,t):
        names=self.spec.get('places') or ['Washington']
        single=len(names)==1
        region=self.spec.get('region') or ('us' if all(n in ('Washington','Ohio','Columbus','United States','Mississippi','New York') for n in names) else 'world')
        if single:
            region={'Washington':'east_us','Columbus':'ohio','Ohio':'ohio',
                    'Beijing':'asia','London':'britain','Athens':'europe'}.get(names[0],region)
        im,bbox=mapa(region,1600)
        pj,_,hh=MV.proyeccion(*bbox,im.width)
        coords=[pj(*PLACES[n]) for n in names]
        # La geografia nunca se desplaza con independencia de sus puntos.
        area=650 if single else 1152
        k=min(area/im.width,420/hh)
        dx,dy=64+(area-im.width*k)/2,155+(420-hh*k)/2
        c.image(im,(dx+im.width*k/2,dy+hh*k/2),width=im.width*k,name='mapa')
        pts=[(dx+x*k,dy+y*k) for x,y in coords]
        labels=self.spec.get('labels',names)
        lookup=dict(zip(names,pts))
        for j,(origin,dest) in enumerate(self.spec.get('routes',[])):
            q,p=lookup[origin],lookup[dest]
            st=self.cue('foreign',.8)+j*.45
            c.arrow(q,p,GOLD,3,smooth((t-st)/2.1))
            if t>st:
                u=((t-st)/4.5)%1
                xy=(mix(q[0],p[0],smooth(u)),mix(q[1],p[1],smooth(u)))
                c.paper((xy[0]-16,xy[1]-23,xy[0]+16,xy[1]+23))
        for j,(name,p) in enumerate(zip(names,pts)):
            color=RED if j==0 else GOLD
            c.ellipse((p[0]-6,p[1]-6,p[0]+6,p[1]+6),color,PAPER,2)
            radius=10+7*((t*.4+j*.3)%1)
            c.ellipse((p[0]-radius,p[1]-radius,p[0]+radius,p[1]+radius),None,color,1)
            txt='OHIO' if name=='Columbus' else name.upper()
            lx=min(1130,max(145,p[0])); ly=p[1]-22 if p[1]>205 else p[1]+26
            # Japon/China comparten zona: los nombres se separan y el punto nunca se mueve.
            if name=='Tokyo': lx,ly=p[0]+30,p[1]+30
            if name=='Beijing': lx,ly=p[0]-55,p[1]-25
            c.text(txt,(lx,ly),24,INK,maxw=230)
        if single:
            if self.spec.get('asset')=='cuna':
                c.image(self.prop('cuna'),(961,374),width=420,height=302,name='cuna')
                when=self.cue('receipt',self.dur*.65)
                if t>=when:
                    x=mix(789,997,smooth((t-when)/1.5))
                    c.paper((x-72,451,x+72,554),'HER NAME')
                c.text('ILLUSTRATION',(956,585),13,MUTED,sans=True)
            elif names[0]=='Washington':
                self.actor(c,'01_burocrata',995,t,reaction=self.cue('publish',.5)+1)
                x=mix(772,837,smooth(t/2))
                c.paper((x-88,312,x+88,526),'TREASURY')
            else:
                active=[lab for i,lab in enumerate(labels) if self.reveal(i,t)>0]
                lab=active[-1] if active else 'TREASURY PAPER'
                rise=8*math.sin(t*.65)
                c.paper((800,222+rise,1160,526+rise),'THE PAPER',lab,RED)
                c.text('ILLUSTRATIVE HOLDING' if names[0]=='Beijing' else 'NEXT FILE',
                       (980,576),17,MUTED,sans=True)
        if labels and labels!=names and not self.spec.get('values'):
            current=[str(x) for i,x in enumerate(labels) if self.reveal(i,t)>0]
            c.text('  /  '.join(current),(640,611),23,INK,maxw=1100)

    def draw_receipt(self,c,t):
        labels=self.spec.get('labels',[])
        names=self.spec.get('actors') or ['01_burocrata']
        self.actor(c,names[0],265,t,reaction=self.cue('reaction',2.0))
        height=mix(185,362,smooth(t/3))
        c.paper((540,175,1118,175+height),'U.S. TREASURY',' ',INK)
        amount=labels[0] if labels and self.reveal(0,t)>0 else 'THE RECEIPT'
        if len(amount)>18:
            amount=amount.replace('178,','178,\n')
        c.text(amount,(829,330),53,RED,maxw=510)
        if len(labels)>1 and self.reveal(1,t)>0:
            c.text(labels[1],(829,480),26,INK,maxw=490)
        # La mano y el papel conservan continuidad; no se inventa otro saldo.
        if 'total' in self.spec.get('cues',{}):
            at=self.cue('cents',self.dur*.65)
            if t>=at:
                c.line([(888,379),(1060,379)],RED,4)
                c.text('TO THE PENNY',(829,577),25,GOLD,maxw=400)
        else:
            at=self.cue('name',self.cue('pocket',self.dur*.55))
            if t>=at:
                u=smooth((t-at)/1.5)
                c.coin((mix(369,504,u),mix(438,550,u)),22)
                c.arrow((458,460),(545,460),GOLD,4,u)

    def draw_machine(self,c,t):
        original='send' in self.spec.get('cues',{})
        self.actor(c,'03_ejecutivo',210,t,reaction=self.cue('pay',2.1))
        send=self.cue('send',self.cue('wanted',self.cue('larger',1.5)))
        self.actor(c,'06_vecino',1060,t,on=max(0,send-.4),reaction=send+1.3)
        c.text('TODAY' if original else 'SPENDING',(210,157),25,TEAL)
        if t>=send:
            c.text('TEN YEARS OLDER' if original else 'THE BILL',(1055,157),23,RED,maxw=285)
        c.rect((440,232,732,521),TEAL,INK,2,5)
        c.rect((459,254,712,420),(35,64,66),radius=4)
        for x,y,r,sign,col in ((533,312,51,1,GOLD),(646,365,43,-1,PAPER)):
            pts=[]
            angle=t*.85*sign
            for j in range(48):
                a=j*math.tau/48+angle
                rr=r*(1 if j%4 in (1,2) else .77)
                pts.append((x+math.cos(a)*rr,y+math.sin(a)*rr))
            c.poly(pts,col)
            c.ellipse((x-11,y-11,x+11,y+11),PALE,INK,2)
        c.text('SPEND',(586,468),30,PAPER)
        pay=self.cue('pay',2.1)
        for j in range(4):
            u=((t-pay-j*.25)%3.1)/1.15 if t>=pay+j*.25 else -1
            if 0<=u<1:
                c.coin((mix(434,345,smooth(u)),mix(412,338-j*12,smooth(u))),19)
        if t>=send:
            x=mix(702,835,smooth((t-send)/1.5))
            c.paper((x-64,328,x+64,510),'THE BILL','DUE',RED)
        c.rect((722,343,744,462),INK,radius=7)
        c.rect((428,526,745,545),INK,radius=5)
        if not original:
            active=[str(lab) for i,lab in enumerate(self.spec.get('labels',[])) if self.reveal(i,t)>0]
            for i,lab in enumerate(active[:2]):
                c.text(lab,(640,575+i*28),25 if i else 31,RED if i==0 else INK,maxw=1100)

    def draw_bars(self,c,t):
        values=self.spec.get('values',[])
        labels=self.spec.get('labels',[])
        if not values or len(values)!=len(labels) or min(values)<0:
            raise ValueError('Barras requieren datos y etiquetas explicitos: '+self.spec['title'])
        component_fall=self.spec['title']=='AN 83-POINT FALL'
        maximum=83 if component_fall else max(values) or 1
        n=len(values); slot=min(250,1050/n)
        active=[i for i in range(n) if self.reveal(i,t)>0]
        if not active:
            self._waiting(c,t)
            return
        focused=self._focus(t,active)
        for j,(v,label) in enumerate(zip(values,labels)):
            x=640+(j-(n-1)/2)*slot
            u=self.reveal(j,t)
            if not u:
                continue
            height=274*v/maximum*u
            col=COLORS[j%len(COLORS)]
            if component_fall:
                c.rect((x-slot*.30,251,x+slot*.30,525),None,MUTED,1)
            c.rect((x-slot*.30,525-height,x+slot*.30,525),col)
            c.line([(x-slot*.30+4,525-height+3),(x+slot*.30-4,525-height+3)],PAPER,2)
            c.text(self._value(v),(x,496-height),38 if n<5 else 29,col,maxw=slot-8)
            c.text(label,(x,562),23,INK,maxw=slot-10)
            if 'COUNTERFACTUAL' in label:
                for y in range(258,522,18):
                    c.line([(x-slot*.30-5,y),(x-slot*.30-5,min(522,y+8))],INK,2)
        c.line([(90,526),(1190,526)],INK,2)
        x=640+(focused-(n-1)/2)*slot
        c.arrow((x,620),(x,592),TEAL,3)
        if self.spec.get('foot'):
            c.text(self.spec['foot'],(640,165),18,MUTED)
        elif component_fall:
            c.text('EACH COMPONENT / 83-POINT TOTAL',(640,165),23,MUTED,maxw=1080)
        elif 'PROJECTION' in self.spec['title']:
            c.text('PROJECTED',(640,165),23,RED)

    def draw_comparison(self,c,t):
        if self.spec.get('values'):
            return self.draw_bars(c,t)
        title=self.spec['title']
        labs=self.spec.get('labels',[])
        if title=='COUNTRY / HOUSEHOLD':
            self.actor(c,'01_burocrata',220,t,reaction=self.cue('retire',2))
            self.actor(c,'06_vecino',1060,t,reaction=self.cue('retire',2))
            c.text('COUNTRY',(350,187),25,TEAL)
            c.text('HOUSEHOLD',(921,187),25,RED)
            c.rect((406,378,598,500),PALE,TEAL,3)
            c.rect((685,378,877,500),PAPER,RED,3)
            for j in range(3):
                u=(t*.28-j*.3)%1
                self._slip(c,(501,mix(224,432,u)),48,'DEBT')
            paid=smooth((t-self.cue('retire',2))/1.5)
            self._slip(c,(781,mix(235,430,paid)),48,'BILL')
            c.line([(682,378),(880,378)],RED,7)
            c.text('CONTINUES',(502,553),22,TEAL)
            if paid>.8:
                c.text('CLOSED',(781,553),22,RED)
        elif title=="MONEY / MONEY'S WORTH":
            self.actor(c,'06_vecino',255,t,reaction=self.cue('difference',3))
            c.paper((480,243,749,477),'MONEY',' ')
            c.text('PROMISED',(614,358),29,TEAL,maxw=225)
            c.text("MONEY'S WORTH",(996,205),25,TEAL,maxw=320)
            self._basket(c,997,390,t,shrink=0)
            u=smooth((t-self.cue('difference',3))/1.7)
            c.arrow((775,356),(844,356),RED,3,u)
            c.text('WHAT IT BUYS',(995,547),25,RED,maxw=330)
        elif title=='WHO IS COMPENSATED?':
            cols=[435,845]
            self.actor(c,'04_trabajador',170,t,reaction=self.cue('wages',2))
            self.actor(c,'06_vecino',1110,t,reaction=self.cue('wages',2))
            wages=t<self.cue('pensions',self.dur*.55)
            headings=labs[:2] if wages else labs[2:4]
            for j,x in enumerate(cols):
                lab=headings[j] if j<len(headings) else ''
                c.text(lab,(x,210),22,TEAL if j==0 else RED,maxw=270)
                self._basket(c,x,420,t,shrink=0,scale=.78)
                c.paper((x-102,280,x+102,359),'ADJUSTMENT' if j==0 else 'PURCHASING POWER','')
            start=self.cue('wages',2) if wages else self.cue('pensions',self.dur*.55)
            u=clamp((t-start)/1.6)
            if 0<u<1:
                self._slip(c,(cols[0],mix(257,387,smooth(u))),35,'')
            c.arrow((575,420),(707,420),MUTED,2,smooth((t-self.cue('compensation',0))/.8))
            c.text('WHO GETS AN ADJUSTMENT?',(640,583),25,INK,maxw=720)
            if t>=self.cue('reason',self.dur+1):
                c.text('$40T',(640,178),31,RED)
        else:
            # El paralelo historico comparte objetos; no implica una proporcion numerica.
            for j,x in enumerate((350,940)):
                label=labs[j] if j<len(labs) else ('THEN' if j==0 else 'NOW')
                c.text(label,(x,195),28,TEAL if j==0 else RED,maxw=470)
                c.paper((x-190,251,x+190,501),'THE RECEIPT','')
                self._basket(c,x,550,t,shrink=0,scale=.65)
            u=smooth((t-self.cue('repeat',.2))/max(1,self.dur*.4))
            c.arrow((562,371),(728,371),GOLD,4,u)

    def draw_ranking(self,c,t):
        vals=self.spec.get('values',[])
        labels=self.spec.get('labels',[])
        if vals and (len(vals)!=len(labels) or max(vals)<=0):
            raise ValueError('Ranking con datos incompletos: '+self.spec['title'])
        top=202; n=len(labels)
        gap=min(108,344/max(1,n-1))
        visible=[]
        for i,lab in enumerate(labels):
            u=self.reveal(i,t)
            if not u:
                continue
            visible.append(i)
            y=top+gap*i
            c.text(str(i+1),(111,y),32,TEAL)
            c.text(lab,(169,y),26,INK,maxw=310,anchor='lm')
            if vals:
                c.rect((505,y-19,505+430*vals[i]/max(vals)*u,y+19),COLORS[i%5])
                c.text(self._value(vals[i]),(1090,y),31,COLORS[i%5],maxw=200)
            else:
                c.line([(525,y),(1170,y)],MUTED,1)
                if 'INTEREST' in lab.upper():
                    c.rect((510,y-30,1180,y+31),RED,radius=2)
                    c.text('THE COST OF BORROWING',(845,y),25,PAPER,maxw=640)
        if visible:
            target=self._focus(t,visible)
            y=top+gap*target
            c.arrow((65,y+12),(88,y+12),GOLD,3)
        else:
            self._waiting(c,t)

    draw_budget=draw_ranking

    def draw_timeline(self,c,t):
        if self.spec.get('values'):
            self.draw_bars(c,t)
            # Estos incrementos pertenecen al presidente saliente, no al nombre del traspaso.
            additions=[('added','OBAMA','+$9.32T'),('trump_added','TRUMP I','+$7.80T'),
                       ('biden_added','BIDEN','+$8.47T')]
            applicable=[a for a in additions if a[0] in self.spec.get('cues',{})]
            for i,(cue,name,value) in enumerate(applicable):
                if t>=self.cue(cue,self.dur+1):
                    x=640 if len(applicable)==1 else 405+i*470
                    c.text(name+'  '+value,(x,178),24,RED,maxw=440)
            return
        labels=self.spec.get('labels',[])
        c.line([(140,506),(1140,506)],MUTED,3)
        visible=[]
        for i,lab in enumerate(labels):
            u=self.reveal(i,t)
            x=190+i*900/max(1,len(labels)-1)
            if not u:
                continue
            visible.append(i)
            c.ellipse((x-7,499,x+7,513),TEAL)
            c.text(lab,(x,556),25,maxw=235)
            for j in range(3):
                yy=444-j*20
                self._slip(c,(x,mix(yy-60,yy,u)),63,'DEBT' if j==2 else '')
        if visible:
            target=self._focus(t,visible)
            x=190+target*900/max(1,len(labels)-1)
            c.arrow((x,259),(x,321),GOLD,4)
            if len(visible)>1:
                u=smooth((t-self.cue('history',self.cue('add',.4)))/max(1,self.dur*.55))
                self._slip(c,(mix(190,1090,u),206),43,'RECEIPT')
        else:
            self._waiting(c,t)

    def draw_counter(self,c,t):
        vals=self.spec.get('values',[])
        labs=self.spec.get('labels',[])
        if len(vals)!=len(labs):
            raise ValueError('Cifra con etiquetas incompletas: '+self.spec['title'])
        active=[i for i in range(len(labs)) if self.reveal(i,t)>0]
        self.actor(c,'01_burocrata',255,t,reaction=1.5)
        i=active[-1] if active else None
        label=labs[i] if i is not None else 'THE RECORD'
        c.paper((487,215,1150,520),label,' ')
        if i is not None:
            value=self._value(vals[i])
            if self.spec['title']=='INTEREST ALONE' and i==1:
                value='$1T'
            if self.spec['title']=='TWENTY MONTHS LATER' and i==1:
                value='+'+value
            c.text(value,(818,354),72,RED,maxw=605)
        for j in range(3):
            u=(t*.27-j*.31)%1
            self._slip(c,(mix(419,513,u),563),22,'')
        if self.spec['title']=='INTEREST ALONE' and t>=self.cue('growth',self.dur+1):
            c.text('MORE THAN 10%',(818,556),24,RED,maxw=540)

    def draw_document(self,c,t):
        name=self.spec.get('asset') or 'paper_imf'
        self.actor(c,'05_jurista',268,t,reaction=1)
        c.image(self.prop(name),(820,351),width=620,height=414,name=name)
        u=smooth(t/max(1,self.dur*.8))
        y=mix(252,435,u)
        c.line([(548,y),(1070,y)],GOLD,3)
        for i,lab in enumerate(self.spec.get('labels',[])[:2]):
            if self.reveal(i,t):
                c.text(lab,(810,572+i*29),23,GOLD,maxw=650)

    def draw_actors(self,c,t):
        names=self.spec.get('actors') or ['03_ejecutivo','06_vecino']
        labs=self.spec.get('labels',[])
        title=self.spec['title']
        if title=='FOUR PRESIDENTS':
            self.actor(c,names[0],194,t,reaction=self.cue('reject',1))
            self.actor(c,names[-1],1095,t,reaction=self.cue('exception',3))
            for i,lab in enumerate(labs):
                if not self.reveal(i,t):
                    continue
                x=416+149*i
                lift=16*math.sin(math.pi*clamp((t-self.cue('exception',3))/1.8)) if i==2 else 0
                c.paper((x-66,283-lift,x+66,430-lift),lab,'')
            if t>=self.cue('same',self.dur+1):
                c.line([(350,473),(929,473)],TEAL,3)
                c.text('THE SAME MACHINE',(640,537),28,TEAL,maxw=620)
            return
        if title=='THE FIRST ONE':
            self.actor(c,names[0],550,t,reaction=self.cue('you',1))
            u=smooth((t-self.cue('turn',0))/1.6)
            self._slip(c,(mix(1070,775,u),361),85,'YOUR CLAIM')
            if self.reveal(0,t):
                c.text('YOU',(885,240),38,RED)
            return
        if title=='DEBT AND GOVERNMENT':
            self.actor(c,names[0],270,t,reaction=self.cue('attached',3))
            u=smooth((t-self.cue('attached',3))/1.7)
            for i in range(6):
                c.paper((mix(726,620,u)+i*7,257+i*25,mix(1058,952,u)+i*7,364+i*25),'DEBT' if i==5 else '','')
            c.line([(398,440),(620,440)],INK,3)
            c.text('GOVERNMENT',(271,575),23,TEAL,maxw=350)
            return
        for i,name in enumerate(names[:2]):
            x=230 if i==0 else 1070
            self.actor(c,name,x,t,reaction=min(self.dur/2,2+i))
            if i<len(labs) and self.reveal(i,t):
                c.text(labs[i],(x,580),23,TEAL,maxw=360)
        if title=='THE CURRENCY IT PRINTS':
            c.rect((462,297,816,488),TEAL,INK,2,4)
            c.rect((486,314,790,389),INK,radius=2)
            c.text('DOLLARS',(639,348),29,PAPER,maxw=265)
            if t>=self.cue('print',self.dur+1):
                for j in range(3):
                    u=(t*.38-j*.3)%1
                    self._slip(c,(640,mix(412,561,u)),55,'$')
        elif title=='THE GROWTH EXPLANATION':
            u=smooth((t-self.cue('economy',1))/2)
            for i in range(5):
                x=487+i*76
                h=60+(i%3+1)*45*u
                c.rect((x,490-h,x+53,490),PALE,TEAL,2)
            c.paper((487,214,811,366),'THE SAME DEBT','')
            if t>=self.cue('check',self.dur+1):
                self._slip(c,(645,537),91,'CHECKED')
        else:
            title='TREASURY RECORD' if title=='THE TREASURY RECORD' else 'THE RECEIPT'
            u=smooth((t-self.cue('record',self.cue('person',.8)))/1.8)
            x=mix(509,680,u)
            c.paper((x-137,280,x+137,464),title,'')

    def draw_flow(self,c,t):
        labs=self.spec.get('labels',[])
        title=self.spec['title']
        if self.spec.get('routes'):
            self.draw_map(c,t)
            c.paper((78,457,424,594),'FOREIGN / TOTAL',' ')
            if self.reveal(0,t):
                c.text('$8.5T',(178,550),32,TEAL,maxw=145)
            if self.reveal(1,t):
                c.text('/ $40T',(329,550),32,RED,maxw=145)
            if t>=self.cue('domestic',self.dur+1):
                c.text('ABOUT 4 IN 5 / OWED TO AMERICANS',(834,598),24,TEAL,maxw=730)
            return
        if title=='WHAT A DOLLAR LEAVES':
            for i,lab in enumerate(labs[:3]):
                if not self.reveal(i,t):
                    continue
                x=260+380*i
                c.text(lab,(x,198),25,COLORS[i],maxw=330)
                start=self.at(self.spec['reveals'][i])
                u=clamp((t-start)/1.5)
                if u<1:
                    c.coin((x,mix(244,364,smooth(u))),24)
                if i==0:
                    c.poly([(x-122,520),(x-40,345),(x+40,345),(x+122,520)],MUTED)
                    for y in range(365,515,31):
                        c.line([(x,y),(x,y+14)],PAPER,4)
                elif i==1:
                    c.image(self.prop('soldado_grande'),(x,425),width=180,height=235,name='soldier')
                else:
                    c.paper((x-131,333,x+131,516),'INTEREST','')
                    c.text('NO NEW GOODS',(x,559),22,RED,maxw=340)
            return
        if title=='HOW IT WORKED':
            self.actor(c,'06_vecino',180,t,reaction=self.cue('alternatives',3))
            for i,lab in enumerate(labs[:3]):
                if not self.reveal(i,t):
                    continue
                x=497+260*i
                c.paper((x-99,327,x+99,504),lab,'')
                u=self.reveal(i,t)
                y=mix(205,302,u)
                c.rect((x-113,y,x+113,y+17),RED,INK,2)
                c.line([(x-92,264),(x-92,302)],INK,3)
                c.line([(x+92,264),(x+92,302)],INK,3)
            if t>=self.cue('payment',0):
                c.text('PAYMENTS CONTINUE',(751,575),26,TEAL,maxw=800)
                u=(t*.32)%1
                self._slip(c,(mix(435,1145,u),225),35,'PAID')
            return
        if title=='WHO PAID FOR THE WAR':
            self.actor(c,'01_burocrata',220,t,reaction=self.cue('transfer',1))
            self.actor(c,'04_trabajador',1060,t,reaction=self.cue('bondholders',3))
            c.text('GOVERNMENT',(250,575),25,TEAL,maxw=350)
            c.text('DOLLAR SAVERS',(1030,575),25,RED,maxw=360)
            c.paper((466,241,814,430),'NOMINAL CLAIM','UNCHANGED')
            u=smooth((t-self.cue('transfer',1))/max(2,self.dur*.6))
            c.rect((421,500,860,521),PALE,INK,2)
            x=mix(455,826,u)
            c.rect((x-25,487,x+25,532),RED,INK,2)
            c.text('REAL BURDEN',(640,574),26,RED,maxw=440)
            return
        self.actor(c,'01_burocrata',640,t,reaction=self.cue('borrow',0))
        left=labs[0] if labs else 'NEW BORROWING'
        right=labs[-1] if labs else 'OLD DEBT'
        c.paper((79,270,391,482),left,'')
        c.paper((889,270,1201,482),right,'')
        c.arrow((404,394),(492,394),TEAL,3)
        c.arrow((788,394),(876,394),TEAL,3)
        for j in range(3):
            u=(max(0,t-self.cue('borrow',0))*.34-j*.28)%1
            x=mix(406,875,u)
            if x<497 or x>779:
                c.coin((x,392),18)
        c.text('TREASURY',(640,581),26,TEAL,maxw=300)

    def draw_trust(self,c,t):
        labs=self.spec.get('labels',[])
        self.actor(c,'04_trabajador',640,t,reaction=2)
        if self.spec.get('values'):
            c.paper((76,255,442,485),labs[0],' ')
            if self.reveal(0,t):
                c.text(self._value(self.spec['values'][0]),(259,374),61,RED,maxw=315)
            c.paper((850,294,1204,458),'RETIREMENT MONEY','')
            c.line([(453,381),(517,381)],GOLD,3)
            c.line([(766,381),(838,381)],GOLD,3)
            if t>=self.cue('social',self.dur+1):
                c.text('MOSTLY SOCIAL SECURITY',(638,581),25,TEAL,maxw=1000)
            u=(t*.22)%1
            self._slip(c,(mix(458,837,u),206),32,'CLAIM')
            return
        positions=[(214,238),(1066,238),(214,477),(1066,477)]
        for i,(lab,(x,y)) in enumerate(zip(labs,positions)):
            if not self.reveal(i,t):
                continue
            c.paper((x-140,y-61,x+140,y+67),lab,'')
            target=(520,363) if x<640 else (760,363)
            origin=(x+145 if x<640 else x-145,y)
            c.line([origin,target],GOLD,3)
            u=(t*.24-i*.19)%1
            self._slip(c,(mix(origin[0],target[0],u),mix(origin[1],target[1],u)),18,'')

    def draw_purchasing(self,c,t):
        self.actor(c,'06_vecino',220,t,reaction=self.cue('loss',self.cue('half',2)))
        vals=self.spec.get('values',[])
        if self.spec.get('unit')=='%':
            c.paper((452,230,1164,509),'THE SAVER\'S RETURN',' ')
            for i,(label,value) in enumerate(zip(self.spec.get('labels',[]),vals)):
                if not self.reveal(i,t):
                    continue
                x=576+235*i
                c.text(label,(x,319),23,INK,maxw=215)
                txt=('-' if i==2 else '')+('%g'%value)+'%'
                c.text(txt,(x,405),56,RED if i==2 else TEAL,maxw=208)
            if t>=self.cue('loss',self.dur+1):
                c.text('REAL LOSS / APPROXIMATE',(805,556),25,RED,maxw=750)
            if t>=self.cue('paid',self.dur+1):
                c.text('NOMINAL PAYMENT UNCHANGED',(807,588),22,TEAL,maxw=740)
            return
        exact_half=self.spec.get('unit')=='$' and vals==[100,100]
        when=self.cue('half',self.cue('erode',self.cue('value',self.dur*.45)))
        u=smooth((t-when)/2.2)
        c.paper((435,234,738,500),'FACE VALUE','$100' if exact_half else 'DOLLARS')
        c.text('BUYING POWER',(993,192),25,TEAL,maxw=350)
        self._basket(c,991,379,t,shrink=u*.5 if exact_half else 0)
        if not exact_half:
            # Sin porcentaje narrado, se muestra friccion en la compra, no una cuota inventada.
            c.rect((832,497,1154,515),PALE,TEAL,2)
            pos=mix(853,1099,u)
            c.rect((pos-16,487,pos+16,525),RED,INK,2)
            if t>=when:
                c.text('LESS TO BUY',(994,559),25,RED,maxw=330)
        else:
            if t>=when:
                c.text('HALF AS MUCH',(993,557),25,RED,maxw=345)
        c.text('SAME DOLLARS',(587,557),25,TEAL,maxw=310)
        if t>=self.cue('paid',self.cue('pay',self.dur+1)):
            c.text('PAID',(587,426),39,RED,maxw=270)

    def draw_rates(self,c,t):
        if self.spec.get('values'):
            return self.draw_bars(c,t)
        labels=self.spec.get('labels',[])
        self.actor(c,'01_burocrata',233,t,reaction=self.cue('rise',self.cue('below',2)))
        repression='INFLATION' in labels
        if repression:
            u=smooth((t-self.cue('below',0))/1.8)
            c.text('INFLATION',(1015,218),25,RED,maxw=340)
            c.text('INTEREST RATES',(1015,420),25,TEAL,maxw=340)
            c.line([(507,266),(1174,266)],RED,4)
            c.line([(507,461),(1174,461)],TEAL,4)
            c.rect((513,mix(335,412,u),781,mix(353,430,u)),INK)
            c.text('CAPPED',(646,379),27,TEAL,maxw=255)
            c.arrow((841,446),(841,279),RED,4,u)
            if t>=self.cue('loss',self.dur+1):
                c.text('REAL VALUE FALLS',(857,555),26,RED,maxw=680)
            if t>=self.cue('nominal',self.dur+1):
                c.text('PAID IN FULL',(857,589),24,TEAL,maxw=680)
            return
        low='LOW RATES' in labels
        u=0 if low else smooth((t-self.cue('rise',0))/2.1)
        c.rect((472,251,720,500),TEAL,INK,2,4)
        c.text('BORROWING',(596,293),25,PAPER,maxw=218)
        c.rect((504,352,689,386),INK,radius=3)
        for j in range(3):
            phase=(t*.34-j*.29)%1
            c.coin((mix(488,704,phase),370),16)
        c.line([(825,224),(825,500)],INK,4)
        level=mix(471,262,u)
        c.rect((798,level-13,852,level+13),GOLD,INK,2)
        c.text('LOW COST' if low else 'INTEREST COST',(1012,200),25,TEAL if low else RED,maxw=340)
        c.paper((891,280,1170,492),'THE BILL','')
        if not low:
            for j in range(3):
                phase=clamp((t-self.cue('rise',0)-j*.5)/2)
                if 0<phase<1:
                    self._slip(c,(mix(734,937,smooth(phase)),420),42,'DUE')
            if 'EVERY MONTH' in labels and t>=self.cue('monthly',self.dur+1):
                c.text('EVERY MONTH',(1029,550),25,RED,maxw=340)
        else:
            c.text('ALMOST NOTHING TO CARRY',(826,558),25,TEAL,maxw=745)

    def draw_savings(self,c,t):
        names=self.spec.get('actors') or ['04_trabajador','06_vecino']
        labels=self.spec.get('labels',[])
        self.actor(c,names[0],238,t,reaction=self.cue('save',1))
        self.actor(c,names[-1],1051,t,reaction=self.cue('politics',3))
        c.paper((457,284,832,518),'SAVINGS','DOLLARS')
        for j in range(3):
            u=(max(0,t-self.cue('save',0))*.27-j*.28)%1
            if t>=self.cue('save',0):
                c.coin((mix(355,568,smooth(u)),mix(353,465,smooth(u))),19)
        for i,lab in enumerate(labels[:3]):
            if self.reveal(i,t):
                c.text(lab,(425+i*222,190),23,TEAL,maxw=210)
        if t>=self.cue('add',self.dur+1):
            self._slip(c,(928,222),63,'MORE DEBT')

    def draw_question(self,c,t):
        self.actor(c,'06_vecino',255,t,reaction=2)
        c.paper((520,264,1137,484),'NAME',' ')
        u=smooth((t-self.cue('you',1))/1.6)
        c.line([(559,410),(mix(560,1095,u),410)],INK,2)
        if t>=self.cue('you',1):
            c.text('IN YOUR LIFE',(828,350),43,RED,maxw=540)
        if t>=self.cue('comments',self.dur*.6):
            c.text('ONE SENTENCE IN THE COMMENTS',(828,560),26,GOLD,maxw=725)

    def _value(self,value):
        unit=self.spec.get('unit','')
        if unit and not unit.startswith('$') and not unit.startswith('%'):
            return ('%g'%value)+' '+unit
        return self.fmt(value)

    def _focus(self,t,visible):
        """El puntero sigue la ultima revelacion, nunca el numero de frases del guion."""
        rs=self.spec.get('reveals',[])
        ordered=sorted((self.at(rs[i]) if i<len(rs) else .2+i*min(1.4,self.dur/6),i)
                       for i in visible)
        when,current=ordered[-1]
        previous=ordered[-2][1] if len(ordered)>1 else current
        return mix(previous,current,smooth((t-when)/.65))

    def _waiting(self,c,t):
        """Mantiene un objeto concreto mientras la voz prepara una cifra todavia no dicha."""
        self.actor(c,'01_burocrata',262,t,reaction=1.3)
        c.paper((494,234,1084,502),'THE RECEIPT','')
        u=(t*.18)%1
        self._slip(c,(mix(588,952,u),372),54,'RECORD')

    def _slip(self,c,xy,r,title=''):
        x,y=xy
        c.rect((x-r+3,y-r*.55+4,x+r+3,y+r*.55+4),MUTED)
        c.rect((x-r,y-r*.55,x+r,y+r*.55),PAPER,INK,1,1)
        if title and r>30:
            c.text(title,(x,y),min(22,r*.30),INK,maxw=r*1.8)
        elif r>24:
            c.line([(x-r*.7,y),(x+r*.7,y)],MUTED,1)

    def _basket(self,c,x,y,t,shrink=0,scale=1):
        """Ocho bienes iguales; una mitad solo desaparece en el ejemplo que la voz cuantifica."""
        for j in range(8):
            xx=x+((j%4)-1.5)*65*scale
            yy=y+((j//4)-.5)*91*scale
            k=1 if j<4 else max(0,1-shrink*2)
            if k<=0:
                continue
            w,h=23*scale,54*scale*k
            c.rect((xx-w,yy-h/2,xx+w,yy+h/2),TEAL if j<4 else GOLD,INK,1,2)
            c.line([(xx-12*scale,yy-h/2),(xx-12*scale,yy-h/2-10*scale*k),
                    (xx+12*scale,yy-h/2-10*scale*k),(xx+12*scale,yy-h/2)],INK,2)
