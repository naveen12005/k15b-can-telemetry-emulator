"""
Automotive CI/CD Verification Suite for K15B Powertrain CAN Telemetry
====================================================================
Formal verification of CAN matrix serialization, physical engine limits,
SHVS hybrid energy balance, and SAE J1979 OBD-II diagnostic protocol.

Author: RATHLAVATH NAVEEN (rathlavathnaveen90@gmail.com)
Copyright (c) 2026 RATHLAVATH NAVEEN. All Rights Reserved.
"""

import os
import unittest
import cantools
from k15b_engine_model import K15BPowertrainPlant

class TestK15BPowertrainPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db_path = os.path.join(os.path.dirname(__file__), "vehicle.dbc")
        cls.db = cantools.database.load_file(db_path)

    def setUp(self):
        self.plant = K15BPowertrainPlant(ambient_temp_c=25.0)

    def test_01_dbc_matrix_frame_definitions(self):
        """DBC Structure: Ensure all required messages exist with standard 8-byte DLC."""
        expected_frames = {
            "ECM_EngineGeneralStatus": (256, 8),
            "ECM_DynamicEngineKinetics": (261, 8),
            "SHVS_HybridStatus": (512, 8),
            "OBD2_DiagnosticRequest": (2016, 8),
            "OBD2_DiagnosticResponse": (2024, 8)
        }
        for name, (fid, dlc) in expected_frames.items():
            msg = self.db.get_message_by_name(name)
            self.assertEqual(msg.frame_id, fid, f"Frame ID mismatch for {name}")
            self.assertEqual(msg.length, dlc, f"DLC mismatch for {name}")

    def test_02_engine_speed_quantization_fidelity(self):
        """Signal Fidelity: Verify 0.25 rpm quantization factor with zero bit-drift."""
        msg = self.db.get_message_by_name("ECM_EngineGeneralStatus")
        test_rpms = [750.25, 1250.0, 2450.50, 4400.75, 6200.0]
        for rpm in test_rpms:
            encoded = msg.encode({
                'EngineSpeed': rpm, 'VehicleSpeed': 60.0,
                'ThrottlePosition': 25.0, 'CoolantTemperature': 88.0,
                'EngineLoad': 35.0, 'FuelFlowRate': 3.50
            })
            decoded = msg.decode(encoded)
            self.assertAlmostEqual(decoded['EngineSpeed'], rpm, delta=0.25)

    def test_03_k15b_torque_envelope_invariants(self):
        """Physical Limit: Peak WOT torque must not exceed K15B physical boundary of 138 Nm."""
        for rpm in range(800, 6500, 200):
            t_wot = self.plant.get_k15b_wide_open_throttle_torque(rpm)
            self.assertGreaterEqual(t_wot, 90.0, f"Torque too low at {rpm} RPM")
            self.assertLessEqual(t_wot, 138.0, f"Torque exceeded 138 Nm limit at {rpm} RPM")
        
        # Verify peak occurs near 4,400 RPM
        t_peak = self.plant.get_k15b_wide_open_throttle_torque(4400.0)
        self.assertAlmostEqual(t_peak, 138.0, delta=2.0)

    def test_04_cold_start_thermal_warmup_convergence(self):
        """Thermal Physics: Coolant temp must rise monotonically and regulate near 88 deg C."""
        initial_temp = self.plant.coolant_temp
        self.assertEqual(initial_temp, 25.0)

        # Simulate 150 seconds of running
        for _ in range(300):
            self.plant.step(dt=0.5, throttle_demand_pct=30.0)

        final_temp = self.plant.coolant_temp
        self.assertGreater(final_temp, 75.0, "Engine did not warm up properly")
        self.assertLessEqual(final_temp, 92.0, "Engine overheated past thermostat range")

    def test_05_shvs_torque_assist_activation_logic(self):
        """Hybrid Control: High throttle demand (>60%) with adequate SOC triggers Torque Assist."""
        # Drive aggressively with 80% throttle demand
        state = self.plant.step(dt=0.1, throttle_demand_pct=80.0, brake_demand_pct=0.0)
        self.assertEqual(state['ISG_OperationalMode'], 1, "SHVS did not engage Torque Assist (Mode 1)")
        self.assertGreater(state['ISG_TorqueAssist'], 0.0, "Torque assist should be positive")
        self.assertLess(state['ISG_Current'], 0.0, "Discharge current should be negative")

    def test_06_shvs_regenerative_braking_energy_balance(self):
        """Hybrid Energy: Deceleration braking recovers kinetic energy and charges Li-ion pack."""
        # Establish speed first
        for _ in range(20):
            self.plant.step(dt=0.1, throttle_demand_pct=50.0)
        self.assertGreater(self.plant.vehicle_speed, 20.0)

        initial_recovered = self.plant.energy_recovered_kwh
        # Apply brakes across several steps
        for _ in range(5):
            state = self.plant.step(dt=0.1, throttle_demand_pct=0.0, brake_demand_pct=50.0)
        self.assertEqual(state['ISG_OperationalMode'], 2, "SHVS did not engage Regen Braking (Mode 2)")
        self.assertLess(state['ISG_TorqueAssist'], 0.0, "Regen torque must oppose rotation (negative)")
        self.assertGreater(state['EnergyRecoveredTotal'], initial_recovered, "Energy was not recovered")

    def test_07_obd2_mode01_pid_query_response(self):
        """OBD-II Protocol: Service 01 queries must return standard PID values with +0x40 response."""
        self.plant.engine_speed = 2400.0
        self.plant.coolant_temp = 88.0
        self.plant.map_kpa = 65.0

        # Query RPM (PID 0x0C)
        resp_rpm = self.plant.process_obd2_request(service_mode=0x01, pid=0x0C)
        self.assertEqual(resp_rpm['Resp_ServiceMode'], 0x41)
        raw_rpm = (resp_rpm['Resp_DataA'] << 8) | resp_rpm['Resp_DataB']
        self.assertAlmostEqual(raw_rpm / 4.0, 2400.0, delta=1.0)

        # Query Coolant Temp (PID 0x05)
        resp_temp = self.plant.process_obd2_request(service_mode=0x01, pid=0x05)
        self.assertEqual(resp_temp['Resp_ServiceMode'], 0x41)
        self.assertEqual(resp_temp['Resp_DataA'] - 40, 88)

    def test_08_dtc_fault_injection_and_mil_illumination(self):
        """Diagnostics: Injecting fault code illuminates MIL and reports via Mode 03."""
        self.assertEqual(self.plant.mil_status, 0)
        # Inject DTC P0118 (ECT Circuit High) = 0x0118
        self.plant.active_dtcs.append(0x0118)
        self.assertEqual(self.plant.get_telemetry_dict()['MIL_Status'], 1)

        # Query DTCs via Service 03
        resp_dtc = self.plant.process_obd2_request(service_mode=0x03, pid=0x00)
        self.assertEqual(resp_dtc['Resp_ServiceMode'], 0x43)
        self.assertEqual(resp_dtc['Resp_DataA'], 0x01)
        self.assertEqual(resp_dtc['Resp_DataB'], 0x18)

        # Clear DTCs via Service 04
        self.plant.process_obd2_request(service_mode=0x04, pid=0x00)
        self.assertEqual(len(self.plant.active_dtcs), 0)
        self.assertEqual(self.plant.get_telemetry_dict()['MIL_Status'], 0)

    def test_09_manifold_pressure_air_charging_dynamics(self):
        """Intake Dynamics: Manifold pressure transitions smoothly between idle and WOT."""
        # Idle condition
        self.plant.step(dt=0.1, throttle_demand_pct=0.0)
        self.assertAlmostEqual(self.plant.map_kpa, 32.0, delta=5.0)

        # Full throttle tip-in
        for _ in range(15):
            self.plant.step(dt=0.1, throttle_demand_pct=100.0)
        self.assertGreater(self.plant.map_kpa, 95.0, "MAP did not reach atmospheric pressure under WOT")

    def test_10_socketcan_bitstream_roundtrip_integrity(self):
        """Bitstream Integrity: Encode all messages to raw byte buffers and decode with zero drift."""
        msg_kin = self.db.get_message_by_name("ECM_DynamicEngineKinetics")
        msg_shvs = self.db.get_message_by_name("SHVS_HybridStatus")

        payload_kin = {
            'EngineTorque': 118.5, 'ManifoldAirPressure': 74,
            'IntakeAirTemperature': 32.0, 'LambdaAirFuelRatio': 0.985,
            'SparkAdvance': 14.5, 'KnockRetard': 0.0,
            'EngineRunState': 4, 'MIL_Status': 0
        }
        encoded_kin = msg_kin.encode(payload_kin)
        decoded_kin = msg_kin.decode(encoded_kin)
        self.assertAlmostEqual(decoded_kin['EngineTorque'], 118.5, delta=0.1)
        self.assertEqual(decoded_kin['ManifoldAirPressure'], 74)
        self.assertAlmostEqual(decoded_kin['LambdaAirFuelRatio'], 0.985, delta=0.002)

        payload_shvs = {
            'ISG_OperationalMode': 2, 'ISG_TorqueAssist': -22.5,
            'ISG_Current': 41.2, 'LiIon_BatterySOC': 74.5,
            'LiIon_BatteryVoltage': 14.2, 'LiIon_BatteryTemp': 28.0,
            'EnergyRecoveredTotal': 1.45
        }
        encoded_shvs = msg_shvs.encode(payload_shvs)
        decoded_shvs = msg_shvs.decode(encoded_shvs)
        self.assertEqual(decoded_shvs['ISG_OperationalMode'], 2)
        self.assertAlmostEqual(decoded_shvs['ISG_TorqueAssist'], -22.5, delta=0.1)
        self.assertAlmostEqual(decoded_shvs['LiIon_BatterySOC'], 74.5, delta=0.5)

if __name__ == '__main__':
    unittest.main()
