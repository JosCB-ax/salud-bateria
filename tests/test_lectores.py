import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from consejos import consejos, diagnostico  # noqa: E402
from consumo import parse_top_macos  # noqa: E402
from lectores import bateria_desde_ioreg, leer_linux, parse_battery_report_xml, parse_ioreg  # noqa: E402

XML_WINDOWS = """<?xml version="1.0" encoding="utf-8"?>
<BatteryReport xmlns="http://schemas.microsoft.com/battery/2012">
  <Batteries>
    <Battery>
      <Id>5B10W13930</Id>
      <Manufacturer>SMP</Manufacturer>
      <Chemistry>LiP</Chemistry>
      <DesignCapacity>57000</DesignCapacity>
      <FullChargeCapacity>48450</FullChargeCapacity>
      <CycleCount>214</CycleCount>
    </Battery>
  </Batteries>
</BatteryReport>"""

IOREG_MAC = """
+-o AppleSmartBattery  <class AppleSmartBattery>
    {
      "ExternalConnected" = Yes
      "AppleRawMaxCapacity" = 4385
      "CycleCount" = 187
      "DesignCapacity" = 4790
      "MaxCapacity" = 100
      "CurrentCapacity" = 76
      "AppleRawCurrentCapacity" = 3330
      "Temperature" = 3071
      "Voltage" = 12735
      "InstantAmperage" = 18446744073709550616
      "IsCharging" = No
      "FullyCharged" = No
      "DeviceName" = "bq40z651"
      "BatteryData" = {"CycleCount"=187,"DesignCapacity"=4790}
    }
"""

TOP_MAC = """Processes: 400 total
COMMAND          POWER
Safari           10.0
Finder           0.1
Processes: 400 total
COMMAND          POWER
Google Chrome He 35.2
Safari           12.4
WindowServer     8.0
"""


class TestLectores(unittest.TestCase):
    def test_windows_xml(self):
        (b,) = parse_battery_report_xml(XML_WINDOWS)
        self.assertEqual(b.capacidad_diseno_mwh, 57000)
        self.assertEqual(b.capacidad_actual_mwh, 48450)
        self.assertEqual(b.ciclos, 214)
        self.assertEqual(b.salud, 85.0)

    def test_macos_ioreg(self):
        d = parse_ioreg(IOREG_MAC)
        self.assertEqual(d["InstantAmperage"], -1000)
        b = bateria_desde_ioreg(d)
        self.assertEqual(b.ciclos, 187)
        self.assertAlmostEqual(b.salud, round(100 * 4385 / 4790, 1), places=0)
        self.assertEqual(b.porcentaje, 76)
        self.assertEqual(b.temperatura_c, 30.7)
        self.assertEqual(b.potencia_w, 12.73)
        self.assertTrue(b.enchufado)

    def test_macos_top(self):
        r = parse_top_macos(TOP_MAC)
        self.assertEqual(r["Google Chrome He"], 35.2)
        self.assertNotIn("Finder", r)

    def _sysfs(self, archivos):
        raiz = tempfile.mkdtemp()
        for disp, valores in archivos.items():
            os.makedirs(os.path.join(raiz, disp))
            for k, v in valores.items():
                with open(os.path.join(raiz, disp, k), "w") as f:
                    f.write(str(v) + "\n")
        return raiz

    def test_linux_energy(self):
        raiz = self._sysfs({
            "AC": {"type": "Mains", "online": 1},
            "BAT0": {"type": "Battery", "status": "Discharging", "capacity": 64,
                     "energy_full_design": 50000000, "energy_full": 41000000,
                     "energy_now": 26240000, "power_now": 8500000, "cycle_count": 402,
                     "manufacturer": "LGC", "model_name": "L19L3PD1", "technology": "Li-poly",
                     "charge_control_end_threshold": 80},
            "hidpp_battery_0": {"type": "Battery", "scope": "Device", "capacity": 50},
        })
        (b,) = leer_linux(raiz)
        self.assertEqual(b.salud, 82.0)
        self.assertEqual(b.ciclos, 402)
        self.assertEqual(b.potencia_w, 8.5)
        self.assertEqual(b.limite_carga, 80)
        self.assertFalse(b.enchufado)
        self.assertEqual(b.estado, "descargando")

    def test_linux_charge(self):
        raiz = self._sysfs({"BAT1": {"type": "Battery", "status": "Full",
                                     "charge_full_design": 4000000, "charge_full": 3000000,
                                     "voltage_min_design": 11400000, "cycle_count": 0}})
        (b,) = leer_linux(raiz)
        self.assertEqual(b.salud, 75.0)
        self.assertAlmostEqual(b.capacidad_diseno_mwh, 45600)
        self.assertIsNone(b.ciclos)  # 0 = el firmware no lo informa
        self.assertEqual(diagnostico(b)[0], "desgastada")
        self.assertTrue(any("80 %" in c for c in consejos(b, [], {})))


if __name__ == "__main__":
    unittest.main()
