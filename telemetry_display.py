"""
K15B CAN Telemetry Live Terminal HUD & Diagnostic Monitor
==========================================================
Decodes incoming SocketCAN broadcast frames per vehicle.dbc and renders
an automotive dashboard with engine gauges, hybrid power flow, and OBD-II status.

Author: RATHLAVATH NAVEEN (rathlavathnaveen90@gmail.com)
Copyright (c) 2026 RATHLAVATH NAVEEN. All Rights Reserved.
"""

import os
import sys
import time
import can
import cantools

def render_bar(val, max_val, length=20):
    ratio = min(1.0, max(0.0, val / max_val))
    filled = int(round(ratio * length))
    return "█" * filled + "░" * (length - filled)

def main():
    db_path = os.path.join(os.path.dirname(__file__), "vehicle.dbc")
    db = cantools.database.load_file(db_path)

    try:
        bus = can.interface.Bus(channel='vcan0', interface='socketcan')
    except Exception:
        bus = can.interface.Bus(channel='virtual_k15b', interface='virtual')

    print("=" * 80)
    print("MARUTI SUZUKI K15B POWERTRAIN & SHVS TELEMETRY MONITOR (SocketCAN)")
    print("Listening on vcan0 | Press Ctrl+C to stop")
    print("=" * 80)

    cached_state = {
        'EngineSpeed': 0.0, 'VehicleSpeed': 0.0, 'ThrottlePosition': 0.0,
        'CoolantTemperature': 25.0, 'EngineLoad': 0.0, 'FuelFlowRate': 0.0,
        'EngineTorque': 0.0, 'ManifoldAirPressure': 32.0, 'IntakeAirTemperature': 28.0,
        'LambdaAirFuelRatio': 1.0, 'SparkAdvance': 8.0, 'KnockRetard': 0.0,
        'ISG_OperationalMode': 0, 'ISG_TorqueAssist': 0.0, 'ISG_Current': 0.0,
        'LiIon_BatterySOC': 80.0, 'LiIon_BatteryVoltage': 13.8, 'EnergyRecoveredTotal': 0.0,
        'MIL_Status': 0
    }

    mode_labels = {
        0: "STANDBY",
        1: "⚡ TORQUE ASSIST (+ISG)",
        2: "🔋 REGEN BRAKING (CHARGE)",
        3: "🔌 CRUISING CHARGE",
        4: "🛑 IDLE STOP-START (ISS)"
    }

    last_render = 0.0

    try:
        while True:
            msg = bus.recv(timeout=0.1)
            if msg:
                if msg.arbitration_id in (256, 261, 512):
                    decoded = db.decode_message(msg.arbitration_id, msg.data)
                    cached_state.update(decoded)

            now = time.time()
            if now - last_render >= 0.1:  # 10 Hz refresh
                last_render = now
                rpm = cached_state['EngineSpeed']
                speed = cached_state['VehicleSpeed']
                torque = cached_state['EngineTorque']
                ect = cached_state['CoolantTemperature']
                soc = cached_state['LiIon_BatterySOC']
                mode_code = int(cached_state.get('ISG_OperationalMode', 0))
                mode_str = mode_labels.get(mode_code, "UNKNOWN")
                fuel = cached_state['FuelFlowRate']

                rpm_bar = render_bar(rpm, 6500.0, 16)
                speed_bar = render_bar(speed, 180.0, 16)
                soc_bar = render_bar(soc, 100.0, 16)

                hud = (
                    f"\r[K15B DUAL-JET VVT] RPM: [{rpm_bar}] {rpm:4.0f} rpm | "
                    f"Speed: [{speed_bar}] {speed:4.1f} km/h | "
                    f"Torque: {torque:4.1f} Nm | "
                    f"ECT: {ect:4.1f}°C | "
                    f"SHVS: {mode_str:<22} | "
                    f"Li-Ion SOC: [{soc_bar}] {soc:4.1f}% | "
                    f"Fuel: {fuel:4.2f} L/h "
                )
                sys.stdout.write(hud)
                sys.stdout.flush()

    except KeyboardInterrupt:
        print("\n[INFO] Monitor terminated.")

if __name__ == "__main__":
    main()
