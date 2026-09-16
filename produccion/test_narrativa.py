"""Regresiones semanticas: las imagenes no deben inventar cifras ni mecanismos."""

import hashlib
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from produccion import narrativa as N


class Registro:
    def __init__(self):
        self.calls=[]

    def __getattr__(self,name):
        def registrar(*args,**kwargs):
            self.calls.append((name,args,kwargs))
        return registrar

    def textos(self):
        return [str(args[0]) for name,args,_ in self.calls if name=='text']


class NarrativaTest(unittest.TestCase):
    def plano(self,kind,**datos):
        spec=dict(kind=kind,title='PRUEBA',start=0,end=12,beat=0)
        spec.update(datos)
        lineas={(0,i):dict(inicio=i*2,fin=i*2+1.5) for i in range(6)}
        plano=N.Plano(spec,lineas,[],ROOT/'videos/09_deuda_eeuu',width=640)
        plano.actor=Mock()
        return plano

    def test_barras_sin_valores_no_inventan_datos(self):
        plano=self.plano('bars',labels=['A','B'])
        with self.assertRaises(ValueError):
            plano.draw_bars(Registro(),1)

    def test_comparacion_cualitativa_no_usa_barras(self):
        for title,labels in [('COUNTRY / HOUSEHOLD',['A COUNTRY','A HOUSEHOLD']),
                             ("MONEY / MONEY'S WORTH",['MONEY',"MONEY'S WORTH"]),
                             ('WHO IS COMPENSATED?',['WAGES','WAGES','PENSIONS','SAVINGS']),
                             ('A RE-RUN',['THEN','NOW'])]:
            plano=self.plano('comparison',title=title,labels=labels)
            plano.draw_bars=Mock(side_effect=AssertionError('Barras ficticias'))
            plano.draw_comparison(Registro(),5)
            plano.draw_bars.assert_not_called()

    def test_coste_interes_no_inventa_inflacion(self):
        for labels in [['INTEREST','EXPENSIVE'],['LOW RATES','BORROWING'],['INTEREST','EVERY MONTH']]:
            plano=self.plano('rates',labels=labels)
            registro=Registro()
            plano.draw_rates(registro,6)
            self.assertNotIn('INFLATION',registro.textos())

    def test_porcentajes_del_ahorrador_no_se_convierten_en_mitad(self):
        plano=self.plano('purchasing',labels=['BOND','PRICES','SAVINGS LOST'],
                         values=[2,5,3],unit='%',reveals=[0,0,1])
        registro=Registro()
        plano.draw_purchasing(registro,6)
        self.assertTrue({'2%','5%','-3%'}.issubset(registro.textos()))
        self.assertNotIn('HALF AS MUCH',registro.textos())
        self.assertNotIn('$100',registro.textos())

    def test_mitad_solo_en_ejemplo_explicito(self):
        for values,unit,esperado in [([100,100],'$',.5),([],None,0)]:
            plano=self.plano('purchasing',values=values,unit=unit,cues={'half':1})
            plano._basket=Mock()
            plano.draw_purchasing(Registro(),8)
            self.assertEqual(plano._basket.call_args.kwargs['shrink'],esperado)

    def test_trust_muestra_cifra_del_guion(self):
        plano=self.plano('trust',labels=['TRUST FUNDS'],values=[7.69],unit='$T',reveals=[0])
        registro=Registro()
        plano.draw_trust(registro,3)
        self.assertIn('$7.69T',registro.textos())

    def test_counter_respeta_reveal(self):
        plano=self.plano('counter',labels=['PER SECOND'],values=[74000],unit='$',reveals=[2])
        antes,despues=Registro(),Registro()
        plano.draw_counter(antes,3)
        plano.draw_counter(despues,5)
        self.assertNotIn('$74,000',antes.textos())
        self.assertIn('$74,000',despues.textos())

    def test_incrementos_aparecen_con_el_mandatario_saliente(self):
        plano=self.plano('timeline',labels=['BIDEN / 2021','TRUMP II / 2025'],
                         values=[27.75,36.22],unit='$T',reveals=[0,2],
                         cues={'trump_added':1,'biden_added':3})
        antes,medio,final=Registro(),Registro(),Registro()
        plano.draw_timeline(antes,1)
        plano.draw_timeline(medio,3)
        plano.draw_timeline(final,7)
        self.assertNotIn('TRUMP I  +$7.80T',antes.textos())
        self.assertIn('TRUMP I  +$7.80T',medio.textos())
        self.assertNotIn('BIDEN  +$8.47T',medio.textos())
        self.assertIn('BIDEN  +$8.47T',final.textos())

    def test_componentes_usan_el_descenso_total_como_denominador(self):
        plano=self.plano('bars',title='AN 83-POINT FALL',
                         labels=['BUDGET SURPLUSES','RATE DISTORTIONS'],
                         values=[17,28],unit='POINTS',reveals=[0,0])
        registro=Registro()
        plano.draw_bars(registro,3)
        bars=[args[0] for name,args,_ in registro.calls
              if name=='rect' and args[1] in N.COLORS]
        self.assertEqual(len(bars),2)
        self.assertAlmostEqual(bars[0][3]-bars[0][1],274*17/83)
        self.assertAlmostEqual(bars[1][3]-bars[1][1],274*28/83)

    def test_foco_sigue_dato_reciente_no_el_numero_de_frases(self):
        plano=self.plano('bars',labels=['SURPLUS','RATES'],values=[17,28],reveals=[0,1])
        self.assertEqual(plano._focus(5,[0,1]),1)
        self.assertEqual(plano._focus(11,[0,1]),1)
        ranking=self.plano('ranking',labels=['SOCIAL SECURITY','MEDICARE','INTEREST','DEFENCE','MEDICAID'],
                           reveals=[4,4,1,2,3])
        self.assertIn(ranking._focus(10,[0,1,2,3,4]),[0,1])

    def test_proporcion_domestica_aparece_en_su_cue(self):
        plano=self.plano('flow',labels=['FOREIGN','TOTAL'],values=[8.5,40],unit='$T',
                         routes=[['Washington','Tokyo']],reveals=[0,1],cues={'domestic':3})
        plano.draw_map=Mock()
        antes,despues=Registro(),Registro()
        plano.draw_flow(antes,5)
        plano.draw_flow(despues,7)
        texto='ABOUT 4 IN 5 / OWED TO AMERICANS'
        self.assertNotIn(texto,antes.textos())
        self.assertIn(texto,despues.textos())

    def test_cuatro_fechas_no_se_reducen_a_dos_actores(self):
        dates=['2009','2017','2021','2025']
        plano=self.plano('actors',title='FOUR PRESIDENTS',actors=['01_burocrata','03_ejecutivo'],
                         labels=dates,reveals=[0,0,0,0])
        registro=Registro()
        plano.draw_actors(registro,3)
        titles=[args[1] for name,args,_ in registro.calls if name=='paper']
        self.assertEqual(titles,dates)

    def test_usos_del_dolar_no_forman_transferencias(self):
        plano=self.plano('flow',title='WHAT A DOLLAR LEAVES',
                         labels=['A ROAD','A SOLDIER','INTEREST'],reveals=[0,1,2])
        plano.prop=Mock(return_value='soldado.png')
        registro=Registro()
        plano.draw_flow(registro,8)
        self.assertFalse(any(name=='arrow' for name,_,_ in registro.calls))

    def test_frame_determinista_y_cifra_visible(self):
        plano=self.plano('bars',labels=['1946','1974'],values=[106,23],unit='%',reveals=[0,1])
        a=plano.frame(5)
        b=plano.frame(5)
        self.assertEqual(a.size,(640,360))
        self.assertEqual(hashlib.sha256(a.tobytes()).digest(),hashlib.sha256(b.tobytes()).digest())
        self.assertGreater(len(a.getcolors(a.width*a.height)),100)


if __name__=='__main__':
    from radar.entorno import cargar
    cargar()
    unittest.main()
