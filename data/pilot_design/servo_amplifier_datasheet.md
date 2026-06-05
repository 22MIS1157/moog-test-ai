# Servo Amplifier Control Card — Design Datasheet
## Part Number: MOOG-SA-4200

### 1. General Description
The MOOG-SA-4200 is a high-performance servo amplifier control card designed for precision motion control applications in aerospace and industrial automation systems. It converts low-power digital control signals from the main controller into high-power drive signals that actuate brushless DC (BLDC) motors and torque motors used in Moog's actuation systems.

### 2. Absolute Maximum Ratings

| Parameter               | Symbol  | Min   | Typ   | Max   | Unit  |
|--------------------------|---------|-------|-------|-------|-------|
| Supply Voltage           | VCC     | 22    | 28    | 36    | V DC  |
| Output Current (per ch)  | Iout    | -     | 5.0   | 8.0   | A     |
| Peak Current (100ms)     | Ipeak   | -     | -     | 15.0  | A     |
| PWM Switching Frequency  | fPWM    | 16    | 20    | 25    | kHz   |
| Operating Temperature    | Topr    | -40   | 25    | +85   | C     |
| Storage Temperature      | Tstr    | -55   | -     | +125  | C     |
| Power Dissipation        | Pd      | -     | -     | 45    | W     |

### 3. Electrical Specifications (VCC = 28V, Topr = 25C)

| Parameter                     | Min    | Typ    | Max    | Unit   |
|-------------------------------|--------|--------|--------|--------|
| Quiescent Current             | -      | 85     | 120    | mA     |
| Output Voltage Swing          | 2.0    | -      | VCC-2  | V      |
| Voltage Regulation            | -      | 0.05   | 0.1    | %      |
| Current Sense Accuracy        | -      | 1.0    | 2.0    | %      |
| Bandwidth (-3dB)              | -      | 2.5    | -      | kHz    |
| Total Harmonic Distortion     | -      | 0.8    | 1.5    | %      |
| Input Impedance               | 10     | -      | -      | kOhm   |
| Common Mode Rejection Ratio   | 60     | 75     | -      | dB     |

### 4. Pin Configuration

| Pin   | Name         | Type      | Description                                |
|-------|--------------|-----------|--------------------------------------------|
| 1     | VCC          | Power     | Main DC power supply input (22-36V)        |
| 2     | GND          | Power     | Ground reference                           |
| 3     | PHASE_A+     | Output    | Motor Phase A positive drive               |
| 4     | PHASE_A-     | Output    | Motor Phase A negative drive               |
| 5     | PHASE_B+     | Output    | Motor Phase B positive drive               |
| 6     | PHASE_B-     | Output    | Motor Phase B negative drive               |
| 7     | PHASE_C+     | Output    | Motor Phase C positive drive               |
| 8     | PHASE_C-     | Output    | Motor Phase C negative drive               |
| 9     | ISENSE_A     | Analog In | Current sense feedback for Phase A         |
| 10    | ISENSE_B     | Analog In | Current sense feedback for Phase B         |
| 11    | ISENSE_C     | Analog In | Current sense feedback for Phase C         |
| 12    | SPI_MOSI     | Digital   | SPI Master-Out Slave-In                    |
| 13    | SPI_MISO     | Digital   | SPI Master-In Slave-Out                    |
| 14    | SPI_CLK      | Digital   | SPI Clock (up to 10 MHz)                   |
| 15    | SPI_CS       | Digital   | SPI Chip Select (active low)               |
| 16    | ENABLE       | Digital   | Amplifier enable (active high)             |
| 17    | FAULT        | Digital   | Fault output (active low, open drain)      |
| 18    | TEMP_SENSE   | Analog In | On-board temperature sensor (NTC)          |
| 19    | ECAT_TX+     | Digital   | EtherCAT transmit positive                 |
| 20    | ECAT_TX-     | Digital   | EtherCAT transmit negative                 |
| 21    | ECAT_RX+     | Digital   | EtherCAT receive positive                  |
| 22    | ECAT_RX-     | Digital   | EtherCAT receive negative                  |

### 5. Functional Block Diagram

```
                   +------------------+
  VCC  ---------> | Power Regulator  | ------> Internal 5V, 3.3V Rails
                   +------------------+
                          |
  SPI Bus  ---------> +------------------+
  EtherCAT  -------> | MCU (ARM Cortex) | ----> PWM Generation
                      +------------------+       |
                          |                      v
  ENABLE  ----------> +------------------+  +------------------+
                      | Gate Driver      |->| H-Bridge MOSFETs |---> PHASE A/B/C
                      +------------------+  +------------------+
                                                  |
  ISENSE A/B/C  <--  +------------------+         |
                     | Current Sense ADC | <-------+
                     +------------------+
                          |
  TEMP_SENSE  -----> +------------------+
                     | Thermal Monitor  | ----> FAULT (if T > 85C)
                     +------------------+
```

### 6. Protection Features
- Over-current protection: Latching fault if Iout > 8.0A sustained for > 50ms
- Over-temperature shutdown: FAULT asserted if junction temperature exceeds 105C
- Under-voltage lockout (UVLO): Card disables if VCC < 18V
- Short-circuit protection: Immediate shutdown on output short detection
- Soft-start: 200ms ramp-up on ENABLE assertion to prevent inrush current

### 7. Communication Interfaces

#### 7.1 SPI Interface
- Mode: SPI Mode 0 (CPOL=0, CPHA=0)
- Max clock: 10 MHz
- Register map: 32 x 16-bit registers for configuration and status readback
- Key registers: PWM_FREQ (0x04), CURRENT_LIMIT (0x08), STATUS (0x10), FAULT_CODE (0x14)

#### 7.2 EtherCAT Interface
- Compliant with IEC 61158 (EtherCAT)
- Supports CoE (CANopen over EtherCAT) profile
- Cycle time: 1ms deterministic
- Object dictionary includes motor parameters, current setpoints, and diagnostic data

### 8. Environmental Compliance
- EMC: MIL-STD-461G compliant (conducted emissions CE102, radiated emissions RE102)
- Vibration: IEC 60068-2-6, 10-2000 Hz, 10g peak
- Shock: IEC 60068-2-27, 40g, 11ms half-sine
- Humidity: 95% RH non-condensing at 40C for 96 hours
