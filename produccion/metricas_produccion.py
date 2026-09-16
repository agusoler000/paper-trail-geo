"""Capturas locales de YouTube Studio, sin API ni publicacion.

python produccion/metricas_produccion.py init
python produccion/metricas_produccion.py capture --input captura.json
python produccion/metricas_produccion.py report

Los datos no observados son null. Las comparaciones son descriptivas y no prueban
que la animacion, el gancho o la miniatura hayan causado un cambio de rendimiento.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from radar.entorno import cargar

STORE=ROOT/'canal/_metricas_produccion.json'
WINDOWS={'24h':24,'48h':48,'7d':168}
METRICS=('views','ctr_pct','retention_30s_pct','average_view_duration_seconds','subscribers_gained')
NOTE=('Comparacion descriptiva: una asociacion entre versiones y metricas no demuestra causalidad. '
      'Comparar videos del mismo formato y revisar su edad real, tema, impresiones y fuente de trafico.')


def aware(value,label='timestamp'):
    if not isinstance(value,str):
        raise ValueError(label+' debe ser una fecha ISO con zona horaria.')
    try:
        dt=datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError as exc:
        raise ValueError(label+' no es una fecha ISO valida.') from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError(label+' debe incluir UTC o un desplazamiento explicito.')
    return dt.astimezone(timezone.utc)


def iso(value):
    return value.astimezone(timezone.utc).isoformat().replace('+00:00','Z')


def number(value,label,integer=False,maximum=None):
    if value is None:
        return None
    if isinstance(value,bool) or not isinstance(value,(int,float)):
        raise ValueError(label+' debe ser un numero o null.')
    if not math.isfinite(value) or value<0 or (integer and value!=int(value)):
        raise ValueError(label+' debe ser finito, no negativo'+(' y entero.' if integer else '.'))
    if maximum is not None and value>maximum:
        raise ValueError(label+' no puede superar '+str(maximum)+'.')
    return int(value) if integer else float(value)


def empty_store():
    return {
        'schema':1,
        'objective':{'deadline_utc':'2026-09-30T23:59:59Z','channel_subscribers':500,
                     'views_per_long':500,'kind':'objective_not_guarantee'},
        'baseline':{'observed_at':None,'channel_subscribers':None},
        'snapshots':[],
    }


def validate_capture(payload):
    if not isinstance(payload,dict):
        raise ValueError('La captura debe ser un objeto JSON.')
    allowed={'video_id','format','published_at','observed_at','window','metrics',
             'channel_subscribers','video_duration_seconds','source','variant'}
    unexpected=set(payload)-allowed
    if unexpected:
        raise ValueError('Campos desconocidos: '+', '.join(sorted(unexpected)))
    video=payload.get('video_id')
    if not isinstance(video,str) or not video.strip() or len(video)>160:
        raise ValueError('video_id debe identificar un video concreto.')
    if payload.get('format') not in ('largo','short'):
        raise ValueError('format debe ser largo o short.')
    if payload.get('window') not in WINDOWS:
        raise ValueError('window debe ser 24h, 48h o 7d.')
    published=aware(payload.get('published_at'),'published_at')
    observed=aware(payload.get('observed_at'),'observed_at')
    if observed<published:
        raise ValueError('La observacion no puede preceder a la publicacion.')
    metrics=payload.get('metrics',{})
    if not isinstance(metrics,dict) or set(metrics)-set(METRICS):
        raise ValueError('metrics contiene campos desconocidos o no es un objeto.')
    # La retencion puede reflejar repeticiones; no se recorta al 100% como el CTR.
    values={name:number(metrics.get(name),name,integer=name in ('views','subscribers_gained'),
                        maximum=100 if name=='ctr_pct' else None) for name in METRICS}
    duration=number(payload.get('video_duration_seconds'),'video_duration_seconds')
    if duration==0:
        raise ValueError('video_duration_seconds debe ser positivo o null.')
    if duration is not None and duration<30 and values['retention_30s_pct'] is not None:
        raise ValueError('Un video menor de 30s no tiene retencion en el segundo 30: usar null.')
    for field in ('source','variant'):
        if payload.get(field) is not None and not isinstance(payload[field],str):
            raise ValueError(field+' debe ser texto o null.')
    hours=(observed-published).total_seconds()/3600
    return {
        'video_id':video.strip(),'format':payload['format'],
        'published_at':iso(published),'observed_at':iso(observed),'window':payload['window'],
        'observed_age_hours':round(hours,6),
        'window_offset_hours':round(hours-WINDOWS[payload['window']],6),
        'metrics':values,'channel_subscribers':number(payload.get('channel_subscribers'),
                                                    'channel_subscribers',integer=True),
        'video_duration_seconds':duration,'source':payload.get('source'),
        'variant':payload.get('variant'),
    }


def load(path):
    if not path.exists():
        return empty_store()
    data=json.loads(path.read_text(encoding='utf-8'))
    if data.get('schema')!=1 or not isinstance(data.get('snapshots'),list):
        raise ValueError('El archivo no es un almacen de metricas compatible.')
    for record in data['snapshots']:
        payload={key:value for key,value in record.items()
                 if key not in ('id','recorded_at','observed_age_hours','window_offset_hours')}
        normalized=validate_capture(payload)
        if any(normalized[key]!=record.get(key) for key in normalized):
            raise ValueError('Una captura guardada no coincide con sus datos normalizados.')
        aware(record['recorded_at'],'recorded_at')
    baseline=data.get('baseline',{})
    number(baseline.get('channel_subscribers'),'baseline.channel_subscribers',integer=True)
    if baseline.get('observed_at') is not None:
        aware(baseline['observed_at'],'baseline.observed_at')
    return data


def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=path.parent,
                                     prefix=path.name+'.',suffix='.tmp',delete=False) as output:
        temporary=Path(output.name)
        json.dump(data,output,indent=2,ensure_ascii=True,allow_nan=False)
        output.write('\n')
    temporary.replace(path)


def capture(path,payload):
    data=load(path)
    record=validate_capture(payload)
    previous=[s for s in data['snapshots'] if s['video_id']==record['video_id']]
    if any(s['format']!=record['format'] or s['published_at']!=record['published_at'] for s in previous):
        raise ValueError('Un video no puede cambiar de formato ni fecha de publicacion entre capturas.')
    serialized=json.dumps(record,sort_keys=True,separators=(',',':'),allow_nan=False)
    identifier=hashlib.sha256(serialized.encode()).hexdigest()[:20]
    if any(s['id']==identifier for s in previous):
        return {'status':'already_exists','id':identifier,'store':str(path)}
    record['id']=identifier
    record['recorded_at']=iso(datetime.now(timezone.utc))
    data['snapshots'].append(record)
    save(path,data)
    return {'status':'recorded','snapshot':record,'store':str(path)}


def baseline(path,count,at):
    data=load(path)
    data['baseline']={'channel_subscribers':number(count,'channel_subscribers',integer=True),
                      'observed_at':iso(aware(at,'observed_at'))}
    save(path,data)
    return data['baseline']


def report(data):
    groups={'largo':[],'short':[]}
    records=sorted(data['snapshots'],key=lambda s:(aware(s['observed_at']),aware(s['recorded_at'])))
    channel=[s for s in records if s['channel_subscribers'] is not None]
    base=data.get('baseline',{})
    candidates=[(aware(s['observed_at']),s['channel_subscribers']) for s in channel]
    if base.get('channel_subscribers') is not None and base.get('observed_at') is not None:
        candidates.append((aware(base['observed_at']),base['channel_subscribers']))
    current=max(candidates,key=lambda item:item[0])[1] if candidates else None
    goal=data['objective']
    for video in sorted({s['video_id'] for s in records}):
        snapshots=[s for s in records if s['video_id']==video]
        last=snapshots[-1]
        windows={w:None for w in WINDOWS}
        for s in snapshots:
            windows[s['window']]={key:s[key] for key in ('id','observed_at','observed_age_hours',
                                                       'window_offset_hours','metrics','variant','source')}
        views=last['metrics']['views']
        groups[last['format']].append({
            'video_id':video,'published_at':last['published_at'],'windows':windows,
            'latest_observed_at':last['observed_at'],'latest_views':views,
            'long_views_goal_met_at_latest_observation':
                (views>=goal['views_per_long'] if views is not None else None)
                if last['format']=='largo' else None,
        })
    return {
        'objective':dict(goal,baseline_channel_subscribers=base.get('channel_subscribers'),
                         latest_channel_subscribers=current,
                         remaining_channel_subscribers=max(0,goal['channel_subscribers']-current)
                         if current is not None else None),
        'by_format':groups,'snapshot_count':len(records),
        'interpretation':NOTE,
        'missing_values':'null significa no observado o no aplicable; cero solo significa cero medido.',
        'window_definition':'24h/48h/7d son puntos de observacion objetivo. observed_age_hours '
                            'y window_offset_hours conservan la edad real; no son ventanas moviles.',
    }


def main():
    cargar()
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--store',type=Path,default=STORE)
    commands=parser.add_subparsers(dest='command',required=True)
    commands.add_parser('init',help='Crear un almacen vacio sin inventar valores de partida')
    commands.add_parser('report',help='Comparar capturas separando largo y short')
    add=commands.add_parser('capture',help='Agregar una captura de Studio desde un JSON local')
    add.add_argument('--input',type=Path,required=True)
    base=commands.add_parser('baseline',help='Registrar los suscriptores observados del canal')
    base.add_argument('--subscribers',type=int,required=True)
    base.add_argument('--at',required=True)
    template=commands.add_parser('template',help='Imprimir una captura vacia con fechas conocidas')
    template.add_argument('--video-id',required=True)
    template.add_argument('--format',choices=('largo','short'),required=True)
    template.add_argument('--published-at',required=True)
    template.add_argument('--observed-at',required=True)
    template.add_argument('--window',choices=WINDOWS,required=True)
    args=parser.parse_args()
    try:
        if args.command=='init':
            data=load(args.store)
            if not args.store.exists():
                save(args.store,data)
            result=report(data)
        elif args.command=='report':
            result=report(load(args.store))
        elif args.command=='capture':
            result=capture(args.store,json.loads(args.input.read_text(encoding='utf-8')))
        elif args.command=='baseline':
            result=baseline(args.store,args.subscribers,args.at)
        else:
            payload=dict(video_id=args.video_id,format=args.format,published_at=args.published_at,
                         observed_at=args.observed_at,window=args.window,
                         metrics={key:None for key in METRICS},channel_subscribers=None,
                         video_duration_seconds=None,source=None,variant=None)
            validate_capture(payload)
            result=payload
        print(json.dumps(result,indent=2,ensure_ascii=True,allow_nan=False))
        return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print('ERROR: '+str(exc),file=sys.stderr)
        return 1


if __name__=='__main__':
    sys.exit(main())
