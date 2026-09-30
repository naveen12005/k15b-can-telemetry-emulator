[![K15B CAN Telemetry Pipeline](https://github.com/naveen12005/k15b-can-telemetry-emulator/actions/workflows/ci_pipeline.yml/badge.svg)](https://github.com/naveen12005/k15b-can-telemetry-emulator/actions/workflows/ci_pipeline.yml)

# K15B Engine CAN Telemetry Emulator & Diagnostic Pipeline

An automotive telemetry emulator modeling real-time CAN bus messaging for the Maruti Suzuki / Suzuki K15B 1.5L naturally aspirated powertrain. The system broadcasts SAE J1979 / OBD-II standard frames via SocketCAN and executes automated continuous integration asserting CAN matrix encoding fidelity and physical scaling invariants.

---

## 1. System Architecture

```text
+-------------------------------------------------------------+
|                K15B ECU Emulator (Sender)                   |
|   - Simulates realistic engine load, RPM, and cooling dynamics |
|   - Encodes frames strictly per vehicle.dbc                 |
|   - Transmits CAN 0x100 (256) at 20 Hz periodic intervals  |
+-------------------------------+-------------------------------+
                                 |
                    CAN IE 0x100: EngineData
            (EngineSpeed, VehicleSpeed, CoolantTemp,
             ThrottlePos, EngineLoad, FuelFlowRate)
                                 v
    ======================= vcan0 =======================
                                 v
+-------------------------------+-------------------------------+
|            Telemetry Display Node (Receiver)                |
|   - Asynchronous SocketCAN listener                         |
|   - Real-time bitmask extraction and physical decoding      |
|   - Continuous terminal HUD instrumentation                 |
+-------------------------------------------------------------+
```

---

## 2. CAN Matrix Signals (`vehicle.dbc`)

| Signal Name | Start Bit | Length | Byte Order | Factor | Offset | Physical Range | Unit |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
|**EngineSpeed** | 0 | 16 | Little Endian | 0.25 | 0 | 0 to 8000 | rpm |
| **VehicleSpeed** | 16 | 8 | Little Endian | 1 | 0 | 0 to 220 | km/h |
| **ThrottlePosition** | 24 | 8 | Little Endian | 0.5 | 0 | 0 to 100 | % d
| **CoolantTemperature** | 32 | 8 | Little Endian | 1 | -40 | -40 to 150 |  deg C |
| **EngineLoad** | 40 | 8 | Little Endian | 0.5 | 0 | 0 to 100 | % d
| **FuelFlowRate** | 48 | 16 | Little Endian | 0.01 | 0 | 0 to 50 | L/h |

---

## 3. Verification & CI/CD Invariants

The automated verification suite asserts:
1. **DBC-Structural Integrity:** Verification of message ID `px100` and byte length constraints (8 bytes DLC).
2. **Quantization & Encoding Fidelity:** Zero bit-drift validation across integer and floating-point conversions.
3. **Physical Boundary Invariants:** Boundary validation across engine load and coolant temperature ranges.

```bash
# Run Telemetry Test Suite
python3 -m unittest -v test_pipeline.py
```