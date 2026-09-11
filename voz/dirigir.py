# -*- coding: utf-8 -*-
"""Direccion de actor para ElevenLabs v3 — guion v2 (relato). Registro: narrador de historia, no locutor.
Cinematico y cercano en las escenas, seco en los chistes, cada revelacion precedida de pausa, y el tono baja
(no sube) cuando la cosa se pone seria. Crece acto a acto.

    python voz/dirigir.py guiones/01_aviacion_rusa/guion.md   -> produccion/audio/dirigido/beat_XX.txt
    python voz/dirigir.py guiones/02_afd_alemania/guion.md --out produccion/audio/dirigido_02   (DIR en guiones/02_afd_alemania/direccion.py)
"""
import sys
from pathlib import Path

# (tag de apertura del beat, {indice_linea: tag antes de esa linea})
DIR={
 0:("[low, intimate, almost a whisper]",
    {2:"[slower]",3:"[pause] [beat]",4:"[pause] [grave]",5:"[flat, cold]",6:"[slower, each word landing]"}),
 1:("[building, tense]",
    {1:"[dry]",2:"[pointed]",3:"[quick, sharp]",4:"[cold]",5:"[pause] [wry, low]",6:"[hushed]",7:"[pause] [flat]",
     8:"[warmer, conspiratorial]",9:"[firm]",10:"[list, low]",11:"[list, lower]",12:"[list, lowest, pause]"}),
 2:("[calm, inviting]",
    {1:"[wry]",2:"[precise]",3:"[pause] [flat]",4:"[conversational]",5:"[pointed]",6:"[list, quick]",
     7:"[slower, bleak]",8:"[measured]",9:"[pause]",10:"[quiet]",11:"[slow, ominous]"}),
 3:("[dry, conspiratorial]",
    {2:"[list]",3:"[list]",4:"[list]",5:"[pause] [wry]",6:"[flat]",7:"[measured]",8:"[lower]",9:"[calm]",
     10:"[pointed]",11:"[pause] [low, warning]"}),
 4:("[steady]",
    {1:"[pause] [quiet]",2:"[explanatory]",3:"[pointed]",5:"[wry]",7:"[pause]",8:"[flat, cold]",9:"[precise, heavy]",
     10:"[wry, amused]",11:"[measured]",12:"[flat]",14:"[pause] [dry, pointed]",15:"[calm]",16:"[lower, ominous]",
     17:"[pointed]",18:"[pause] [hushed]",19:"[flat, heavy]",20:"[slower]",21:"[measured]",22:"[dry]",
     23:"[pause] [slower, grim]",24:"[beat] [whisper, ominous]"}),
 5:("[quiet, cinematic, intimate]",
    {1:"[pause]",2:"[lower]",3:"[dry]",4:"[pause] [flat, chilling]",5:"[brisk, explanatory]",6:"[firm]",7:"[wry]",
     8:"[pause] [pointed, dark]",9:"[calm]",10:"[pause] [dry]",11:"[slower, heavy]",12:"[precise]",13:"[flat, pause]",
     14:"[measured]",15:"[pause] [low]",16:"[pointed]",17:"[pause] [wry, dark]",18:"[flat]",19:"[list, quick]",
     20:"[slower]",21:"[dry]",22:"[pause] [grave]",23:"[conspiratorial]",24:"[calm]",25:"[quicker]",
     26:"[pause] [measured]",27:"[list, precise]",28:"[calm]",29:"[pause]",30:"[slow, each word landing]",
     31:"[pointed]",32:"[warmer, rising]",33:"[pause] [slower, quiet]",34:"[whisper, ominous]"}),
 6:("[quiet, tense, cinematic]",
    {1:"[pause] [whisper]",2:"[flat]",3:"[brisk]",4:"[list, urgent, quick]",5:"[pause] [pointed]",6:"[calm]",7:"[lower]",
     8:"[measured]",9:"[rising]",10:"[steady]",11:"[flat]",12:"[pause] [conspiratorial]",13:"[firm]",
     14:"[list, building]",15:"[pointed]",16:"[pause] [dry, cold]",17:"[quick]",18:"[measured]",
     19:"[pause] [low, pointed]",20:"[calm]",21:"[questioning]",22:"[measured]",23:"[slower, grave]",
     24:"[pause] [hushed]",25:"[slow, deliberate]",26:"[flat, bitter]",27:"[dry]",28:"[explanatory]",29:"[measured]",
     30:"[pause] [pointed]",31:"[quiet]",32:"[flat, heavy]",33:"[list, tired]",34:"[slower, aching]",
     35:"[pause] [cold]",36:"[calm]",37:"[slower, ominous, warning]"}),
 7:("[grave, steady]",
    {1:"[list, even]",2:"[pointed]",3:"[list, quick]",4:"[measured]",6:"[slower, building, heavier]",7:"[pause] [flat]",
     8:"[conversational]",9:"[calm]",10:"[dry]",11:"[pause] [lower, ominous]",12:"[list, tense]",13:"[pointed]",
     14:"[slow, each word landing]",15:"[flat, cold]",16:"[pause] [hushed]",17:"[precise]",18:"[calm, sad]",
     19:"[pause] [pointed]",20:"[slower, cinematic]",21:"[wry, bitter]",22:"[flat]",23:"[slower, pointed]",
     24:"[pause] [whisper, ominous]"}),
 8:("[quiet, cold, intimate]",
    {1:"[precise]",2:"[calm, bleak]",3:"[pause]",4:"[list, low]",5:"[slower]",6:"[pause] [flat, chilling]",7:"[measured]",
     8:"[measured]",9:"[quiet]",10:"[pause] [pointed]",11:"[dry, cold]",12:"[measured]",13:"[pause]",14:"[flat, heavy]",
     15:"[calm]",16:"[lower]",17:"[slower, pointed]",18:"[measured]",19:"[dry]",20:"[pause] [whisper]",
     21:"[slow, final, ominous]"}),
 9:("[measured, gathering weight]",
    {1:"[list, low]",2:"[list, lower]",3:"[list, lowest, pause]",4:"[calm]",5:"[slower, pointed]",6:"[pause] [dry]",
     7:"[measured, heavy]",8:"[calm]",9:"[pause] [cold]",10:"[list, each one landing]",11:"[list]",12:"[list, pause]",
     13:"[slower, grave, final]"}),
 10:("[whisper, ominous, teaser]",{1:"[pause]",2:"[slower, final, cold]"}),
}

def leer(p):
    beats=[];cur=None
    for l in Path(p).read_text(encoding='utf-8').splitlines():
        if l.startswith('## BEAT'): cur=[]; beats.append(cur)
        elif l.startswith('A:') and cur is not None: cur.append(l[2:].strip())
    return [b for b in beats if b]

def cargar_dir(g):
    """Si existe guiones/<ep>/direccion.py, usa su DIR (por episodio); si no, el DIR de arriba (ep. 1)."""
    d=Path(g).resolve().parent/'direccion.py'
    if d.exists():
        import importlib.util
        spec=importlib.util.spec_from_file_location('direccion',d); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m.DIR
    return DIR

if __name__=='__main__':
    g=sys.argv[1]
    out=Path(sys.argv[sys.argv.index('--out')+1]) if '--out' in sys.argv else Path(g).resolve().parents[2]/'produccion'/'audio'/'dirigido'
    out.mkdir(parents=True,exist_ok=True)
    D=cargar_dir(g); beats=leer(g); total=0
    for bi,lines in enumerate(beats):
        head,tags=D.get(bi,("",{}))
        assert all(k<len(lines) for k in tags), (bi,len(lines),tags)
        parts=[head]
        for li,l in enumerate(lines):
            if li in tags: parts.append(tags[li])
            parts.append(l)
        txt=' '.join(p for p in parts if p)
        (out/f'beat_{bi:02d}.txt').write_text(txt,encoding='utf-8'); total+=len(txt)
        print(f'beat {bi:2d}: {len(lines):2d} lineas, {len(txt):5d} chars')
    print('total chars',total,'-> creditos aprox',round(total/560*3))
