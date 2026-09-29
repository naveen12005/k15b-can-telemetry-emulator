import time, math, can, cantools

db = cantools.database.load_file("vehicle.dbc")
bus = can.interface.Bus(channel='vcan0', bustype='socketcan')

engine_speed = 1100.0
vehicle_speed = 0.0
coolant_temp = 25.0
target_temp = 88.0
throttle_pos = 0.0
start_time = time.time()

print("Starting Maruti K15B Simulator on vcan0...")
try:
    while True:
        elapsed = time.time() - start_time
        if coolant_temp < target_temp:
            coolant_temp += 0.15
            engine_speed = max(750.0, 1100.0 - (coolant_temp - 25.0) * 5.5)
        else:
            engine_speed = 750.0 + 1200.0 * abs(math.sin(elapsed * 0.2))
            throttle_pos = 5.0 + 20.0 * abs(math.sin(elapsed * 0.2))

        engine_load = 18.0 + (engine_speed / 8000.0) * 35.0
        fuel_flow = (engine_speed * engine_load * 0.0018) / 60.0

        msg = db.get_message_by_name("EngineData")
        data = msg.encode({
            'EngineSpeed': min(8000.0, max(0.0, engine_speed)),
            'VehicleSpeed': vehicle_speed,
            'ThrottlePosition': min(100.0, max(0.0, throttle_pos)),
            'CoolantTemperature': min(215.0, max(-40.0, coolant_temp)),
            'EngineLoad': min(100.0, max(0.0, engine_load)),
            'FuelFlowRate': min(650.0, max(0.0, fuel_flow))
        })
        bus.send(can.Message(arbitration_id=msg.frame_id, data=data, is_extended_id=False))
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nSimulator stopped.")
