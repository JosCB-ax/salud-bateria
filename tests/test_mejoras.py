import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bandeja import decidir_aviso  # noqa: E402
from consumo import parse_srum_csv  # noqa: E402

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
        self.assertIn("--bandeja", open(ruta).read())
        configuracion.fijar_arranque(False)
        self.assertFalse(configuracion.arranque_activado())


if __name__ == "__main__":
    unittest.main()
