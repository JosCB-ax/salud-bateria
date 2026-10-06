import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bandeja import decidir_aviso  # noqa: E402
from actualizaciones import _de_github, es_mas_nueva, suma_esperada  # noqa: E402
from consumo import parse_srum_csv  # noqa: E402
from prueba import calcular_resultado  # noqa: E402

SRUM = """AppId,UserId,TimeStamp,TotalEnergyConsumption,CPUEnergyConsumption
\\Device\\HarddiskVolume3\\Program Files\\Google\\Chrome\\Application\\chrome.exe,S-1-5,2026-10-06 10:00:00,300,200
\\Device\\HarddiskVolume3\\Teams\\ms-teams.exe,S-1-5,2026-10-06 11:00:00,100,50
\\Device\\HarddiskVolume3\\Antiguo\\viejo.exe,S-1-5,2026-10-01 11:00:00,999,1
"""


class TestAvisos(unittest.TestCase):
    CFG = {"avisos": True, "umbral_alto": 80, "umbral_bajo": 20}

    def test_avisa_una_vez_y_se_rearma(self):
        st = {}
        pasos = [(79, True), (80, True), (90, True), (90, False), (20, False), (18, False),
                 (30, False), (20, False)]
        avisos = [decidir_aviso(st, p, e, self.CFG) for p, e in pasos]
        self.assertIsNone(avisos[0])
        self.assertIn("Desenchufa", avisos[1])
        self.assertEqual(avisos[2:4], [None, None])
        self.assertIn("Enchufa", avisos[4])
        self.assertIsNone(avisos[5])
        self.assertIn("Enchufa", avisos[7])  # volvió a subir más de 3 puntos y bajó otra vez

    def test_desactivado(self):
        self.assertIsNone(decidir_aviso({}, 95, True, dict(self.CFG, avisos=False)))


class TestSrum(unittest.TestCase):
    def test_reparto_ultimas_24h(self):
        self.assertEqual(parse_srum_csv(SRUM), [("chrome", 75.0), ("ms-teams", 25.0)])

    def test_formato_desconocido(self):
        self.assertEqual(parse_srum_csv("a,b\n1,2\n"), [])


class TestArranqueLinux(unittest.TestCase):
    @unittest.skipUnless(sys.platform.startswith("linux"), "solo Linux")
    def test_crea_y_borra_desktop(self):
        import tempfile
        import configuracion
        ruta = os.path.join(tempfile.mkdtemp(), "autostart", "salud.desktop")
        configuracion.DESKTOP = ruta
        configuracion.fijar_arranque(True)
        self.assertTrue(configuracion.arranque_activado())
        with open(ruta) as f:
            self.assertIn("--bandeja", f.read())
        configuracion.fijar_arranque(False)
        self.assertFalse(configuracion.arranque_activado())


class TestPrueba(unittest.TestCase):
    def test_con_energia_en_mwh(self):
        r = calcular_resultado({"porcentaje": 90, "carga_mwh": 45000}, {"porcentaje": 84, "carga_mwh": 42000},
                               1200, 50000, 57000)
        self.assertEqual(r["vatios"], 9.0)          # 3 Wh en 20 min
        self.assertAlmostEqual(r["horas_hoy"], 5.56, places=2)
        self.assertAlmostEqual(r["horas_nueva"], 6.33, places=2)
        self.assertEqual(r["precision"], "alta")

    def test_solo_porcentaje(self):
        r = calcular_resultado({"porcentaje": 90}, {"porcentaje": 84}, 1200, 50000, None)
        self.assertEqual(r["vatios"], 9.0)
        self.assertEqual(r["precision"], "media")

    def test_sin_bajada(self):
        with self.assertRaises(ValueError):
            calcular_resultado({"porcentaje": 90}, {"porcentaje": 90}, 600, 50000, None)


class TestHistorialPropio(unittest.TestCase):
    def test_registra_y_completa(self):
        import datetime as dt
        import tempfile
        import configuracion
        import historial
        from lectores import Bateria
        carpeta = tempfile.mkdtemp()
        original = configuracion.carpeta
        configuracion.carpeta = lambda: carpeta
        self.addCleanup(setattr, configuracion, "carpeta", original)
        t = dt.datetime(2026, 10, 6, 10, 0)
        for dia, cap in ((1, 50000), (2, 49900)):
            historial.registrar(Bateria(capacidad_diseno_mwh=57000, capacidad_actual_mwh=cap, enchufado=True),
                                t + dt.timedelta(days=dia))
        historial.registrar(Bateria(capacidad_diseno_mwh=57000, capacidad_actual_mwh=49800, enchufado=True),
                            t + dt.timedelta(days=2, hours=3))  # mismo día: sustituye
        for m in range(6):
            historial.registrar(Bateria(enchufado=False, potencia_w=8 + m), t + dt.timedelta(minutes=10 * m))
        b = Bateria(capacidad_diseno_mwh=57000, capacidad_actual_mwh=49800)
        historial.completar(b, t + dt.timedelta(days=3))
        self.assertEqual([f for f, _ in b.historial], ["2026-10-07", "2026-10-08"])
        self.assertEqual(b.historial[-1][1], round(100 * 49800 / 57000, 1))
        self.assertEqual(b.consumo_medio_w, 10.5)
        self.assertEqual(b.horas_medidas, 1.0)


class TestVersiones(unittest.TestCase):
    def test_comparacion(self):
        self.assertTrue(es_mas_nueva("1.10.0", "1.9.3"))
        self.assertFalse(es_mas_nueva("v1.3.0", "1.3.0"))



class TestIdioma(unittest.TestCase):
    def setUp(self):
        import idioma
        self.idioma = idioma
        idioma.fijar("en")
        self.addCleanup(idioma.fijar, "es")

    def test_plantillas_y_compuestos(self):
        t = self.idioma.t
        self.assertEqual(t("Salud de la batería: Buena"), "Battery health: Good")
        self.assertEqual(t("312 ciclos · carga al 100 % · llena"), "312 cycles · 100 % charged · full")
        self.assertEqual(t("Pierde 10,8 puntos de salud al año. Llegará al 80 % en un mes aproximadamente."),
                         "It loses 10,8 health points per year. It will reach 80 % in about a month.")
        self.assertEqual(t("Modo ahorro activado. Plan de energía: Economizador; Brillo: 90 % → 40 %"),
                         "Saver mode on. Power plan: Power saver; Brightness: 90 % → 40 %")
        self.assertEqual(t("texto sin traducción"), "texto sin traducción")

    def test_todos_los_consejos_traducidos(self):
        from consejos import consejos
        from lectores import Bateria
        b = Bateria(capacidad_diseno_mwh=57000, capacidad_actual_mwh=30000, porcentaje=100, enchufado=True,
                    ciclos=100, temperatura_c=41)
        for c in consejos(b, [], {"Brillo de pantalla": "90 %"}):
            self.assertNotEqual(self.idioma.t(c), c, c)

    def test_espanol_no_cambia(self):
        self.idioma.fijar("es")
        self.assertEqual(self.idioma.t("Salud de la batería"), "Salud de la batería")


class TestPrediccion(unittest.TestCase):
    def test_ritmo_y_plazos(self):
        import prediccion
        hist = [("2025-10-01", 90.0), ("2026-04-01", 85.0), ("2026-10-01", 80.0)]
        p = prediccion.predecir(82.0, hist)
        self.assertAlmostEqual(p["ritmo"], 10.0, delta=0.1)
        self.assertEqual(p["meses"][80], 2)
        self.assertEqual(p["meses"][60], 26)
        self.assertIsNone(prediccion.predecir(82.0, hist[:1]))
        self.assertIsNone(prediccion.predecir(55.0, hist)["meses"][60])

    def test_aviso_temperatura(self):
        from bandeja import decidir_aviso_temperatura
        st, cfg = {}, {"aviso_temperatura": True, "umbral_temp": 40}
        self.assertIsNone(decidir_aviso_temperatura(st, 39, cfg))
        self.assertIn("41", decidir_aviso_temperatura(st, 41, cfg))
        self.assertIsNone(decidir_aviso_temperatura(st, 42, cfg))
        decidir_aviso_temperatura(st, 35, cfg)
        self.assertIsNotNone(decidir_aviso_temperatura(st, 40, cfg))


class TestSeguridadActualizaciones(unittest.TestCase):
    def test_solo_descarga_de_github(self):
        base = "https://github.com/JosCB-ax/salud-bateria/releases/download/v2.0.0/"
        self.assertTrue(_de_github(base + "SaludBateria-Setup-2.0.0.exe"))
        self.assertFalse(_de_github("http://github.com/JosCB-ax/salud-bateria/releases/download/v2/x.exe"))
        self.assertFalse(_de_github("https://github.com.malo.net/JosCB-ax/salud-bateria/releases/download/x.exe"))
        self.assertFalse(_de_github("https://github.com/otro/repo/releases/download/v1/x.exe"))
        self.assertFalse(_de_github(None))

    def test_suma_del_archivo(self):
        h = "a" * 64
        sumas = f"{h}  SaludBateria-Setup-2.0.0.exe\n{'b' * 64}  otro.dmg\n"
        self.assertEqual(suma_esperada(sumas, "SaludBateria-Setup-2.0.0.exe"), h)
        self.assertIsNone(suma_esperada(sumas, "falta.exe"))
        self.assertIsNone(suma_esperada("xyz  SaludBateria-Setup-2.0.0.exe", "SaludBateria-Setup-2.0.0.exe"))


if __name__ == "__main__":
    unittest.main()
