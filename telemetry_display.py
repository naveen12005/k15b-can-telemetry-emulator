import can, cantools

db = cantools.database.load_file("vehicle.dbc")
bus = can.interface.Bus(channel='vcan0', bustype='socketcan')

print("=" * 65)
print("MARUTI K15B POWERTRAIN CAN MONITOR (vcan0)")
print("=" * 65)
print(f"{'RPM':>8} | {'Speed(km/h)':>12} | {'Coolant(°C)':>12} | {'Load(%)':>8} | {'Fuel(L/h)':>10}")
print("-" * 65)

try:
    while True:
        msg = bus.recv()
        if msg and msg.arbitration_id == 256:
            decoded = db.decode_message(msg.arbitration_id, msg.data)
            print(f"{decoded['EngineSpeed']:8.1f} | {decoded['VehicleSpeed']:12.1f} | {decoded['CoolantTemperature']:12.1f} | {decoded['EngineLoad']:8.1f} | {decoded['FuelFlowRate']:10.2f}", end='\r')
except KeyboardInterrupt:
    print("\nMonitor stopped.")
