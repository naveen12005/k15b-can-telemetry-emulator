import unittest, cantools

class TestK15BPowertrainPipeline(unittest.TestCase):
    def setUp(self):
        self.db = cantools.database.load_file("vehicle.dbc")

    def test_dbc_signal_definitions(self):
        msg = self.db.get_message_by_name("EngineData")
        self.assertEqual(msg.frame_id, 256)
        self.assertEqual(msg.length, 8)

    def test_engine_speed_encoding_fidelity(self):
        msg = self.db.get_message_by_name("EngineData")
        encoded = msg.encode({
            'EngineSpeed': 2450.25, 'VehicleSpeed': 45.0,
            'ThrottlePosition': 18.5, 'CoolantTemperature': 88.0,
            'EngineLoad': 32.0, 'FuelFlowRate': 4.12
        })
        decoded = msg.decode(encoded)
        self.assertAlmostEqual(decoded['EngineSpeed'], 2450.25, delta=0.25)
        self.assertAlmostEqual(decoded['CoolantTemperature'], 88.0, delta=1.0)

if __name__ == '__main__':
    unittest.main()
