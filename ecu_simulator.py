"""
Maruti K15B 1.5L Powertrain & Smart Hybrid (SHVS) CAN Bus Telemetry Simulator
=============================================================================
Simulates real-time multi-node broadcast on SocketCAN (vcan0) per vehicle.dbc:
- 0x100 (20 Hz): Primary Engine General Status
- 0x105 (50 Hz): Dynamic Combustion Kinetics & MAP
- 0x200 (20 Hz): SHVS Hybrid ISG & Li-Ion Battery Telemetry
- 0x7E8 (Event): ISO 15765-4 / SAE J1979 OBD-II Diagnostic Response

Author: RATHLAVATH NAVEEN (rathlavathnaveen90@gmail.com)
Copyright (c) 2026 RATHLAVATH NAVEEN. All Rights Reserved.
"""

import os
import sys
import time
import math
import can
import cantools
from k15b_engine_model import K15BPowertrainPlant

def get_can_bus(channel='vcan0'):
    """Initializes SocketCAN interface, falling back to a virtual bus if unavailable."""
    try:
        return can.interface.Bus(channel=channel, interface='socketcan')
    except Exception as e:
        return can.interface.Bus(channel='virtual_k15b', interface='virtual')

def run_simulation(duration_sec=None, live_hud=True):
    db_path = os.path.join(os.path.dirname(__file__), "vehicle.dbc")
    db = cantools.database.load_file(db_path)
    bus = get_can_bus('vcan0')
    plant = K15BPowertrainPlant(ambient_temp_c=25.0)

    print("=" * 80)
    print("MARUTI SUZUKI K15B 1.5L VVT POWERTRAIN & SHVS TELEMETRY SIMULATOR")
    print("Broadcasting on CAN bus per ISO 11898 / SAE J1939 (vehicle.dbc)")
    print("=" * 80)

    msg_eng_gen = db.get_message_by_name("ECM_EngineGeneralStatus")
    msg_eng_kin = db.get_message_by_name("ECM_DynamicEngineKinetics")
    msg_shvs    = db.get_message_by_name("SHVS_HybridStatus")

    start_time = time.time()
    last_20hz_time = 0.0
    last_50hz_time = 0.0
    dt = 0.02  # 50 Hz base tick (20 ms)

    try:
        while True:
            current_time = time.time()
            elapsed = current_time - start_time

            if duration_sec and elapsed >= duration_sec:
                print(f"\n[INFO] Simulation completed target duration of {duration_sec:.1f}s.")
                break

            # Synthetic Drive-Cycle Profile:
            # 0-10s: Cold Idle Warmup
            # 10-25s: Moderate acceleration (tip-in)
            # 25-40s: Hard acceleration (SHVS Torque Assist active)
            # 40-55s: Deceleration & Regenerative Braking
            # 55-70s: Warm cruising
            phase = elapsed % 70.0
            if phase < 10.0:
                throttle = 0.0
                brake = 0.0
            elif phase < 25.0:
                throttle = 25.0 + 15.0 * math.sin((phase - 10.0) * 0.4)
                brake = 0.0
            elif phase < 40.0:
                throttle = 80.0 + 15.0 * math.sin((phase - 25.0) * 0.5)  # Hard acceleration
                brake = 0.0
            elif phase < 55.0:
                throttle = 0.0
                brake = 45.0 + 20.0 * math.sin((phase - 40.0) * 0.3)     # Strong Regen Braking
            else:
                throttle = 35.0
                brake = 0.0

            # Step physical plant
            state = plant.step(dt=dt, throttle_demand_pct=throttle, brake_demand_pct=brake)

            # 50 Hz Transmission: Dynamic Engine Kinetics (0x105)
            if current_time - last_50hz_time >= 0.02:
                data_kin = msg_eng_kin.encode({
                    'EngineTorque': min(200.0, max(0.0, state['EngineTorque'])),
                    'ManifoldAirPressure': min(255, max(0, int(state['ManifoldAirPressure']))),
                    'IntakeAirTemperature': min(215.0, max(-40.0, state['IntakeAirTemperature'])),
                    'LambdaAirFuelRatio': min(4.0, max(0.0, state['LambdaAirFuelRatio'])),
                    'SparkAdvance': min(63.5, max(-64.0, state['SparkAdvance'])),
                    'KnockRetard': min(25.5, max(0.0, state['KnockRetard'])),
                    'EngineRunState': 4 if throttle > 50 else (3 if state['CoolantTemperature'] > 80 else 2),
                    'MIL_Status': state['MIL_Status']
                })
                bus.send(can.Message(arbitration_id=msg_eng_kin.frame_id, data=data_kin, is_extended_id=False))
                last_50hz_time = current_time

            # 20 Hz Transmission: General Status (0x100) & SHVS (0x200)
            if current_time - last_20hz_time >= 0.05:
                # 0x100
                data_gen = msg_eng_gen.encode({
                    'EngineSpeed': min(8000.0, max(0.0, state['EngineSpeed'])),
                    'VehicleSpeed': min(250.0, max(0.0, state['VehicleSpeed'])),
                    'ThrottlePosition': min(100.0, max(0.0, state['ThrottlePosition'])),
                    'CoolantTemperature': min(215.0, max(-40.0, state['CoolantTemperature'])),
                    'EngineLoad': min(100.0, max(0.0, state['EngineLoad'])),
                    'FuelFlowRate': min(650.0, max(0.0, state['FuelFlowRate']))
                })
                bus.send(can.Message(arbitration_id=msg_eng_gen.frame_id, data=data_gen, is_extended_id=False))

                # 0x200 SHVS
                data_shvs = msg_shvs.encode({
                    'ISG_OperationalMode': state['ISG_OperationalMode'],
                    'ISG_TorqueAssist': min(50.0, max(-50.0, state['ISG_TorqueAssist'])),
                    'ISG_Current': min(100.0, max(-100.0, state['ISG_Current'])),
                    'LiIon_BatterySOC': min(100.0, max(0.0, state['LiIon_BatterySOC'])),
                    'LiIon_BatteryVoltage': min(25.0, max(0.0, state['LiIon_BatteryVoltage'])),
                    'LiIon_BatteryTemp': min(100.0, max(-40.0, state['LiIon_BatteryTemp'])),
                    'EnergyRecoveredTotal': min(655.0, max(0.0, state['EnergyRecoveredTotal']))
                })
                bus.send(can.Message(arbitration_id=msg_shvs.frame_id, data=data_shvs, is_extended_id=False))
                last_20hz_time = current_time

                if live_hud:
                    mode_names = ["Standby", "Torque Assist", "Regen Braking", "Charging"]
                    mode_str = mode_names[state['ISG_OperationalMode']] if state['ISG_OperationalMode'] < 4 else "ISS"
                    sys.stdout.write(
                        f"\r[T={elapsed:5.1f}s] RPM: {state['EngineSpeed']:4.0f} | Speed: {state['VehicleSpeed']:4.1f} km/h | "
                        f"Torque: {state['EngineTorque']:4.1f} Nm | MAP: {state['ManifoldAirPressure']:3.0f} kPa | "
                        f"ECT: {state['CoolantTemperature']:4.1f}°C | SHVS: {mode_str:<14} | "
                        f"SOC: {state['LiIon_BatterySOC']:4.1f}% | Fuel: {state['FuelFlowRate']:4.2f} L/h "
                    )
                    sys.stdout.flush()

            time.sleep(dt)

    except KeyboardInterrupt:
        print("\n[INFO] Simulator interrupted by user. Exiting cleanly.")

if __name__ == "__main__":
    dur = float(sys.argv[1]) if len(sys.argv) > 1 else None
    run_simulation(duration_sec=dur, live_hud=True)
