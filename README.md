# Vehicle Telemetry & Fault Detection System (VTFD)

Two STM32 Nucleo F401RE nodes connected via CAN bus (MCP2515 + MCP2562, 500 kbps).  
Node 1 acquires sensor data (temperature, voltage, current) and transmits CAN frames.  
Node 2 receives frames, applies fault detection logic, and streams telemetry over UART  
to a Python real-time visualization tool.

Designed to mirror decentralized ECU/BMS node architecture used in Formula Student  
Electric vehicles and distributed battery management systems.

---

## Architecture

```
[Sensors] → [Node 1: STM32 F401RE]
                 ADC acquisition (LM35, voltage divider, ACS712)
                 MCP2515 SPI driver (register-level, no HAL)
                 CAN TX @ 500 kbps
                        │
                   [CAN Bus]
                   120Ω termination each end
                        │
            [Node 2: STM32 F401RE]
                 MCP2515 SPI driver (same driver, different SPI instance)
                 CAN RX + frame unpack
                 Fault engine (threshold comparison)
                 UART TX → PC @ 115200 baud
                        │
              [PC: Python]
                 pyserial + matplotlib
                 Real-time plot + CSV log
```

## Repository Structure

```
vtfd/
├── common/
│   ├── can_frame_def.h       # CAN IDs, payload structs, fault bitmasks
│   └── thresholds.h          # Threshold constants + ADC conversion formulas
├── node1_sensor/
│   └── Core/
│       ├── Inc/              # mcp2515.h, adc_sensor.h, can_tx.h
│       └── Src/              # mcp2515.c, adc_sensor.c, can_tx.c
├── node2_ecu/
│   └── Core/
│       ├── Inc/              # mcp2515.h, can_rx.h, fault_engine.h,
│       │                     # uart_telemetry.h, telemetry.h
│       └── Src/              # mcp2515.c, can_rx.c, fault_engine.c,
│                             # uart_telemetry.c
├── pc_tools/
│   ├── mock_serial.py        # Fake UART stream for offline parser dev
│   ├── telemetry_monitor.py  # Live plot + CSV logger
│   └── requirements.txt
└── hardware/
    └── kicad/                # Sensor node carrier PCB (in design)
```

## CAN Frame Specification

| ID    | Name        | Rate     | Payload                                      |
|-------|-------------|----------|----------------------------------------------|
| 0x100 | TEMP_VOLT   | 10 Hz    | B0-1: temp_raw, B2-3: volt_raw, B4-7: 0x00  |
| 0x101 | CURRENT     | 10 Hz    | B0-1: curr_raw, B2-7: 0x00                  |
| 0x200 | FAULT       | on change| B0: fault_flags, B1: fault_count             |

## UART Telemetry Format

```
T,<timestamp_ms>,<can_id_hex>,<val1_raw>,<val2_raw>,<fault_hex>\r\n
```

Example:
```
T,001234,0x100,744,2604,0x00
T,001890,0x101,3779,0,0x00
T,002100,0x100,812,1700,0x03
```

## Hardware

| Component            | Reichelt Article    | Qty |
|----------------------|---------------------|-----|
| STM32 Nucleo F401RE  | NUCLEO F401RE        | 2   |
| MCP2515+MCP2562 module | DEBO CAN MODULE   | 2   |
| LM35DZ temp sensor   | LM 35 DZ            | 1   |
| ACS712-5A current    | DEBO2 SEN STROM     | 1   |
| Breadboard 830       | BREADBOARD1 830     | 2   |
| Resistors (120/330/10k/47k Ω) | 1/4W series | —  |
| Jumper cables        | DEBO CABLE SET      | 1   |

## Status

- [x] MCP2515 SPI driver (register-level, both nodes)
- [x] Node 1: ADC scan acquisition, CAN TX frame packing
- [x] Node 2: CAN RX, fault engine, UART telemetry
- [ ] CubeMX project setup + HAL skeleton
- [ ] Hardware bring-up
- [ ] Python live visualization + mock serial
- [ ] FreeRTOS task restructure (Node 2)
- [ ] Altium carrier PCB

## Stack

C · STM32 HAL · MCP2515 · FreeRTOS · Python · Altium

## Author

Mohammad Arsham — B.Sc. Computer Engineering, University of Duisburg-Essen  
github.com/MoarSHAm
