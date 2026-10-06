"""
K15B Engine & Smart Hybrid (SHVS) Powertrain Plant Model
=========================================================
Physical Mean-Value Engine Model (MVEM) for Suzuki / Maruti K15B 1.5L DOHC VVT:
- Displacement: 1,462 cc (4-cylinder, 16-valve)
- Bore x Stroke: 74.0 mm x 85.0 mm
- Compression Ratio: 10.5 : 1
- Peak Power: 77 kW (103.3 bhp) @ 6,000 RPM
- Peak Torque: 138 Nm @ 4,400 RPM
- Hybrid: Dual Battery Smart Hybrid (12V 36Wh Li-Ion + 2.2 kW ISG)

Author: RATHLAVATH NAVEEN (rathlavathnaveen90@gmail.com)
Copyright (c) 2026 RATHLAVATH NAVEEN. All Rights Reserved.
"""

import math
import time

class K15BPowertrainPlant:
    def __init__(self, ambient_temp_c=25.0):
        # Engine physical parameters
        self.displacement_cc = 1462.0
        self.idle_target_warm = 750.0      # Warm idle speed (RPM)
        self.idle_target_cold = 1250.0     # Cold start fast-idle flare (RPM)
        self.thermostat_temp_c = 88.0      # Thermostat opening temperature (deg C)
        self.redline_rpm = 6500.0

        # State variables
        self.engine_speed = self.idle_target_cold
        self.vehicle_speed = 0.0           # km/h
        self.throttle_pos = 0.0            # %
        self.coolant_temp = ambient_temp_c # deg C
        self.intake_air_temp = ambient_temp_c + 3.0 # deg C
        self.map_kpa = 32.0                # Idle vacuum: ~32 kPa
        self.engine_torque = 15.0          # Nm
        self.engine_load = 18.0            # %
        self.fuel_flow_lph = 0.75          # Idle fuel rate: ~0.75 L/h
        self.lambda_afr = 1.000            # Stoichiometric (14.7:1)
        self.spark_advance = 8.0           # deg CA BTDC
        self.knock_retard = 0.0            # deg CA
        self.mil_status = 0                # Malfunction Indicator Lamp

        # SHVS Hybrid Subsystem (12V Dual Battery)
        self.shvs_mode = 0                 # 0=Standby, 1=TorqueAssist, 2=RegenBraking, 3=Charging
        self.isg_torque = 0.0              # Nm (-50 to +50 Nm)
        self.isg_current = 0.0             # Amps
        self.li_ion_soc = 80.0             # % (State of Charge)
        self.li_ion_voltage = 13.8         # Volts
        self.li_ion_temp = ambient_temp_c  # deg C
        self.energy_recovered_kwh = 0.0    # Cumulative regen energy

        # Active Diagnostic Trouble Codes (DTCs)
        self.active_dtcs = []

    def get_k15b_wide_open_throttle_torque(self, rpm):
        """
        Calibrated dynamometer wide-open-throttle (WOT) torque curve for K15B.
        Peak torque: 138 Nm @ 4,400 RPM; 115 Nm @ 2,000 RPM; 122 Nm @ 6,000 RPM.
        """
        rpm_clamped = min(self.redline_rpm, max(600.0, rpm))
        # Quadratic/cubic regression fit for K15B dyno curve
        t_wot = 92.0 + 0.0215 * rpm_clamped - 2.45e-6 * (rpm_clamped ** 2)
        return max(0.0, min(138.0, t_wot))

    def step(self, dt=0.05, throttle_demand_pct=0.0, brake_demand_pct=0.0):
        """
        Advance the physical powertrain model by dt seconds.
        """
        self.throttle_pos = min(100.0, max(0.0, throttle_demand_pct))
        
        # 1. Thermal ODE: Engine Warmup
        if self.coolant_temp < self.thermostat_temp_c:
            # Heat generation proportional to fuel burn minus convective cooling
            q_comb = max(0.5, (self.engine_speed / 1000.0) * (self.engine_load / 50.0))
            self.coolant_temp = min(self.thermostat_temp_c, self.coolant_temp + q_comb * 0.28 * dt)
        else:
            # Thermostat regulation with slight road-load oscillation
            self.coolant_temp = self.thermostat_temp_c + 1.5 * math.sin(time.time() * 0.05)

        # 2. Dynamic Idle & Engine Speed Calculation
        idle_target = self.idle_target_cold if self.coolant_temp < 40.0 else \
                      self.idle_target_warm + (self.idle_target_cold - self.idle_target_warm) * max(0.0, (self.thermostat_temp_c - self.coolant_temp) / 50.0)

        if self.throttle_pos < 1.0:
            # Deceleration or Idle
            if self.vehicle_speed < 1.0:
                # Station idle flare
                self.engine_speed += (idle_target - self.engine_speed) * min(1.0, 2.5 * dt)
                self.vehicle_speed = 0.0
            else:
                # Overrun fuel cutoff
                self.vehicle_speed = max(0.0, self.vehicle_speed - (1.8 + 8.0 * (brake_demand_pct / 100.0)) * dt)
                self.engine_speed = max(idle_target, self.vehicle_speed * 42.0)
        else:
            # Driving under acceleration
            target_rpm = idle_target + (self.throttle_pos / 100.0) * (self.redline_rpm - idle_target)
            self.engine_speed += (target_rpm - self.engine_speed) * min(1.0, 3.2 * dt)
            target_speed = (self.engine_speed / self.redline_rpm) * 185.0
            self.vehicle_speed += (target_speed - self.vehicle_speed) * min(1.0, 0.8 * dt)

        # 3. Manifold Filling Dynamics (MAP)
        target_map = 32.0 + (self.throttle_pos / 100.0) * 68.0  # 32 kPa idle -> 100 kPa WOT
        self.map_kpa += (target_map - self.map_kpa) * min(1.0, 10.0 * dt)

        # 4. Engine Torque & Load
        t_wot = self.get_k15b_wide_open_throttle_torque(self.engine_speed)
        load_factor = (self.map_kpa - 25.0) / 75.0
        self.engine_load = min(100.0, max(12.0, load_factor * 100.0))
        self.engine_torque = min(138.0, max(5.0, t_wot * (self.engine_load / 100.0)))

        # 5. Smart Hybrid (SHVS) Energy Management Control
        if brake_demand_pct > 5.0 and self.vehicle_speed > 12.0:
            # Regenerative Braking Mode
            self.shvs_mode = 2  # Regen
            self.isg_torque = -min(40.0, 15.0 + 25.0 * (brake_demand_pct / 100.0))
            self.isg_current = abs(self.isg_torque) * 1.8
            # Charge Li-ion battery
            if self.li_ion_soc < 98.0:
                self.li_ion_soc += (self.isg_current * dt / (3600.0 * 3.0)) * 100.0
                recovered_kwh = (14.0 * self.isg_current * dt) / (3600.0 * 1000.0)
                self.energy_recovered_kwh += recovered_kwh
            self.li_ion_voltage = min(14.8, 13.8 + 0.015 * self.isg_current)

        elif self.throttle_pos > 60.0 and self.li_ion_soc > 30.0 and self.engine_speed < 4500.0:
            # Torque Assist Mode
            self.shvs_mode = 1  # Torque Assist
            self.isg_torque = min(50.0, 10.0 + 40.0 * ((self.throttle_pos - 60.0) / 40.0))
            self.isg_current = - (self.isg_torque * 1.9)
            # Discharge Li-ion battery
            self.li_ion_soc -= (abs(self.isg_current) * dt / (3600.0 * 3.0)) * 100.0
            self.li_ion_voltage = max(11.8, 13.8 - 0.02 * abs(self.isg_current))

        elif self.li_ion_soc < 65.0 and self.throttle_pos > 15.0:
            # Normal Charging Mode (ISG driven by belt)
            self.shvs_mode = 3  # Charging
            self.isg_torque = -8.0
            self.isg_current = 15.0
            self.li_ion_soc += (self.isg_current * dt / (3600.0 * 3.0)) * 100.0
            self.li_ion_voltage = 14.1
        else:
            # Standby Mode
            self.shvs_mode = 0  # Standby
            self.isg_torque = 0.0
            self.isg_current = 0.0
            self.li_ion_voltage = 13.4 + 0.01 * (self.li_ion_soc - 50.0)

        # 6. Fuel Flow Rate (Brake Specific Fuel Consumption BSFC map)
        power_kw = (self.engine_torque * 2.0 * math.pi * self.engine_speed) / 60000.0
        # Typical BSFC for K15B ~ 245 g/kWh at best efficiency
        bsfc_g_kwh = 245.0 + 80.0 * abs((self.engine_speed - 2800.0) / 3500.0) ** 2
        fuel_flow_gps = (power_kw * bsfc_g_kwh) / 3600.0
        # Fuel density ~ 745 g/L
        self.fuel_flow_lph = max(0.65, (fuel_flow_gps * 3600.0) / 745.0)

        # 7. Ignition & Air-Fuel Ratio
        self.lambda_afr = 0.92 if self.throttle_pos > 85.0 else 1.000
        self.spark_advance = 8.0 + (self.engine_speed / 1000.0) * 4.5 - (self.engine_load / 100.0) * 5.0
        self.knock_retard = 2.5 if (self.engine_load > 85.0 and self.coolant_temp > 95.0) else 0.0

        return self.get_telemetry_dict()

    def get_telemetry_dict(self):
        """Returns physical state representation."""
        return {
            'EngineSpeed': round(self.engine_speed, 2),
            'VehicleSpeed': round(self.vehicle_speed, 1),
            'ThrottlePosition': round(self.throttle_pos, 1),
            'CoolantTemperature': round(self.coolant_temp, 1),
            'EngineLoad': round(self.engine_load, 1),
            'FuelFlowRate': round(self.fuel_flow_lph, 2),
            'EngineTorque': round(self.engine_torque, 1),
            'ManifoldAirPressure': round(self.map_kpa, 0),
            'IntakeAirTemperature': round(self.intake_air_temp, 1),
            'LambdaAirFuelRatio': round(self.lambda_afr, 3),
            'SparkAdvance': round(self.spark_advance, 1),
            'KnockRetard': round(self.knock_retard, 1),
            'ISG_OperationalMode': self.shvs_mode,
            'ISG_TorqueAssist': round(self.isg_torque, 1),
            'ISG_Current': round(self.isg_current, 1),
            'LiIon_BatterySOC': round(self.li_ion_soc, 1),
            'LiIon_BatteryVoltage': round(self.li_ion_voltage, 1),
            'LiIon_BatteryTemp': round(self.li_ion_temp, 1),
            'EnergyRecoveredTotal': round(self.energy_recovered_kwh, 5),
            'MIL_Status': 1 if len(self.active_dtcs) > 0 else 0
        }

    def process_obd2_request(self, service_mode, pid):
        """
        Processes standard SAE J1979 OBD-II diagnostic requests:
        - Mode 01: Current Powertrain Diagnostic Data
        - Mode 03: Request Stored Diagnostic Trouble Codes (DTCs)
        - Mode 04: Clear Diagnostic Trouble Codes
        """
        resp = {
            'Resp_ServiceMode': service_mode + 0x40,  # Positive response (+0x40)
            'Resp_PID': pid,
            'Resp_DataA': 0, 'Resp_DataB': 0, 'Resp_DataC': 0, 'Resp_DataD': 0
        }

        if service_mode == 0x01:
            if pid == 0x04:  # Calculated Engine Load (A * 100 / 255 %)
                resp['Resp_DataA'] = int((self.engine_load / 100.0) * 255.0)
            elif pid == 0x05: # Engine Coolant Temperature (A - 40 deg C)
                resp['Resp_DataA'] = int(self.coolant_temp + 40.0)
            elif pid == 0x0B: # Intake Manifold Absolute Pressure (A kPa)
                resp['Resp_DataA'] = int(self.map_kpa)
            elif pid == 0x0C: # Engine RPM ((256A + B) / 4)
                raw_rpm = int(self.engine_speed * 4.0)
                resp['Resp_DataA'] = (raw_rpm >> 8) & 0xFF
                resp['Resp_DataB'] = raw_rpm & 0xFF
            elif pid == 0x0D: # Vehicle Speed (A km/h)
                resp['Resp_DataA'] = int(self.vehicle_speed)
            elif pid == 0x11: # Throttle Position (A * 100 / 255 %)
                resp['Resp_DataA'] = int((self.throttle_pos / 100.0) * 255.0)
        elif service_mode == 0x03:
            # Report active DTCs (e.g. P0118 = 0x0118, P0300 = 0x0300)
            if len(self.active_dtcs) > 0:
                first_dtc = self.active_dtcs[0]
                resp['Resp_DataA'] = (first_dtc >> 8) & 0xFF
                resp['Resp_DataB'] = first_dtc & 0xFF
        elif service_mode == 0x04:
            # Clear DTCs
            self.active_dtcs.clear()
            self.mil_status = 0

        return resp
