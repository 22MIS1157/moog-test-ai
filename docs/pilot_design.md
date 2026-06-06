# Pilot Design Selection: Servo Amplifier Control Card

**MoogTestAI — Pilot Design Documentation**
**Prepared by:** Afnaan Ahmed P | M.Tech Software Engineering, VIT Chennai Campus
**Date:** June 2026
**Revision:** 1.0

---

## 1. Executive Summary

This document describes the pilot hardware design selected for demonstrating MoogTestAI's capabilities. The pilot is a **Servo Amplifier Control Card** — a precision electronic module at the heart of Moog's motion control systems. This card was chosen because it is representative of Moog's core product line, exhibits sufficient complexity to meaningfully exercise the AI system, and has clearly defined specifications against which automated test generation can be validated.

The pilot design is used throughout MoogTestAI development for:
- Validating RAG-based specification extraction accuracy
- Demonstrating AI-generated test plans with real parametric data
- Benchmarking signal analysis and fault diagnosis workflows
- Proving the end-to-end pipeline from design document ingestion to actionable test output

---

## 2. What Is a Servo Amplifier?

### 2.1 Functional Overview

A servo amplifier (also called a servo drive) is a power electronics module that converts low-power control signals into high-power drive signals for precision electric motors. It is the critical link between the digital control system (which computes the desired motion trajectory) and the physical actuator (which produces mechanical force or torque).

```
                    Servo Amplifier Control Card
                    ┌──────────────────────────────────┐
                    │                                    │
  Control Signal ──→│  Signal       Gate       Power    │──→ Motor Drive
  (Digital/Analog)  │  Conditioning  Drive     Stage    │    Output
                    │     │           │          │      │
  Feedback ────────→│  ADC/Encoder   PWM     MOSFET/   │
  (Current, Pos.)   │  Interface   Generator  IGBT     │
                    │     │           │       Bridge    │
  Communication ───→│  SPI/EtherCAT  │          │      │
  Bus               │  Protocol      │          │      │
                    │  Handler       │          │      │
                    │     │           │          │      │
                    │  ┌──┴───────────┴──────────┴──┐   │
                    │  │     Microcontroller /       │   │
                    │  │     FPGA Control Core       │   │
                    │  └────────────────────────────┘   │
                    │                                    │
  Power Supply ────→│  DC Bus Input (28V / 270V)        │
                    │                                    │
                    └──────────────────────────────────┘
```

### 2.2 The Role in Moog's Product Ecosystem

Moog's motion control systems serve applications where precision, reliability, and deterministic behavior are non-negotiable:

- **Aerospace flight control:** Actuating control surfaces (ailerons, elevators, rudders) on commercial and military aircraft. A servo amplifier failure here can be catastrophic.
- **Defense systems:** Turret positioning, missile fin actuation, radar gimbal control — all requiring sub-millisecond response times.
- **Industrial automation:** High-precision CNC machining, injection molding, and semiconductor manufacturing equipment.
- **Space systems:** Satellite antenna pointing, solar array drives, and reaction wheel motor control.

The servo amplifier control card is the "brain" of the servo drive — it houses the digital control logic, communication interfaces, and gate drive circuits. The power stage (MOSFETs/IGBTs and associated magnetics) is typically on a separate board but is controlled by this card.

### 2.3 Why Testing Is Critical

Servo amplifier control cards undergo rigorous testing because:

1. **Safety-critical applications:** A manufacturing defect or firmware bug could result in uncontrolled motor behavior in a flight-critical actuator.
2. **High consequence of field failure:** Moog products often operate in environments where maintenance access is limited or impossible (aircraft, submarines, satellites).
3. **Regulatory compliance:** Aerospace products must meet DO-254 (hardware design assurance), MIL-STD-810 (environmental), and MIL-STD-461 (EMI/EMC) requirements.
4. **Tight tolerance margins:** Servo amplifiers operate at the boundary of analog precision and digital control — small parametric drifts can cause instability.

---

## 3. Pilot Selection Rationale

### 3.1 Selection Criteria

The pilot design was selected based on the following criteria, evaluated against Moog's broader product portfolio:

| Criterion | Requirement | Servo Amp Control Card |
|---|---|---|
| Product line relevance | Must represent Moog's core business | ✅ Central to all motion control products |
| Specification complexity | Must have enough parameters to exercise AI test generation | ✅ 50+ testable parameters across electrical, timing, and communication domains |
| Document availability | Design documentation must be available for RAG ingestion | ✅ Design spec, schematic, BOM, and test procedure documents available |
| Test category diversity | Must require multiple test types (not just pass/fail continuity checks) | ✅ Requires functional, parametric, boundary, communication, and environmental testing |
| Scalability indicator | Results should generalize to other Moog products | ✅ Shared architecture with motor controllers, valve drivers, and power modules |
| Defined acceptance criteria | Must have clear pass/fail specifications for validating AI output | ✅ Published acceptance test procedure (ATP) with defined limits |

### 3.2 Why Not Other Candidates?

Several alternative pilot designs were considered:

| Alternative | Reason Not Selected |
|---|---|
| Power supply module | Too simple — mostly DC voltage/current checks. Wouldn't exercise the AI's ability to handle complex multi-domain testing. |
| Digital communication card | Too narrow — primarily protocol-level testing (EtherCAT, MIL-STD-1553) with limited analog/power parameters. |
| Complete servo drive assembly (box-level) | Too complex for initial pilot — introduces mechanical, thermal, and system integration variables that would obscure the AI evaluation. Better as a Phase 2 target. |
| FPGA mezzanine card | Limited test parameters — primarily configuration verification and basic I/O checks. |

The servo amplifier control card occupies the "sweet spot" — complex enough to demonstrate genuine AI value, but scoped enough to validate within the internship timeline.

---

## 4. Key Specifications of the Pilot Design

### 4.1 Electrical Specifications

| Parameter | Specification | Test Relevance |
|---|---|---|
| Input supply voltage | 28V DC ± 4V (MIL-STD-704 compatible) | Power supply rejection, brownout behavior |
| High-voltage DC bus | Up to 270V DC | Isolation testing, overvoltage protection |
| Control signal input range | ±10V analog / 16-bit digital | ADC linearity, offset, gain error |
| PWM output frequency | 10 kHz – 40 kHz (configurable) | Switching frequency accuracy, duty cycle resolution |
| PWM resolution | 12-bit minimum (0.024% duty cycle) | Minimum pulse width, dead-time accuracy |
| Maximum output current (gate drive) | 2A peak per channel | Rise/fall time, thermal performance under load |
| Current sense accuracy | ±0.5% of full scale | Shunt resistor tolerance, ADC accuracy |
| Power dissipation | < 5W at nominal operating point | Thermal characterization, derating curves |

### 4.2 Timing & Performance Specifications

| Parameter | Specification | Test Relevance |
|---|---|---|
| Control loop bandwidth | > 2 kHz | Frequency response verification |
| Current loop update rate | 40 kHz (25 µs period) | ISR execution time, jitter measurement |
| Command-to-output latency | < 50 µs | Latency measurement under various loads |
| PWM dead-time | 200 ns – 2 µs (configurable) | Dead-time accuracy, shoot-through prevention |
| Startup time (power-on to operational) | < 500 ms | Boot sequence timing, initialization checks |
| Watchdog timeout | 10 ms ± 1 ms | Timeout accuracy, fault response |

### 4.3 Communication Interfaces

| Interface | Specification | Test Relevance |
|---|---|---|
| SPI (configuration) | 10 MHz, Mode 0 (CPOL=0, CPHA=0) | Protocol compliance, data integrity at max clock |
| EtherCAT (fieldbus) | 100 Mbps, CoE/FoE support | Distributed clock sync, PDO mapping, mailbox protocol |
| UART (debug) | 115200 baud, 8N1 | Diagnostic data streaming, firmware update path |
| GPIO (discrete I/O) | 8 inputs / 4 outputs, 3.3V logic | Logic level thresholds, input hysteresis |
| Encoder input | Differential RS-422, up to 16 MHz | Signal integrity, noise immunity, interpolation accuracy |

### 4.4 Environmental Specifications

| Parameter | Specification | Standard |
|---|---|---|
| Operating temperature | -40°C to +85°C | MIL-STD-810H, Method 501.7 / 502.7 |
| Storage temperature | -55°C to +125°C | MIL-STD-810H, Method 501.7 / 502.7 |
| Vibration (random) | 10 g RMS, 20–2000 Hz | MIL-STD-810H, Method 514.8 |
| Shock | 40 g, 11 ms half-sine | MIL-STD-810H, Method 516.8 |
| Humidity | 95% RH, non-condensing | MIL-STD-810H, Method 507.6 |
| Altitude | Up to 70,000 ft (unpressurized) | MIL-STD-810H, Method 500.6 |
| EMI emissions | MIL-STD-461G, RE102 | Radiated emissions, 10 kHz – 18 GHz |
| EMI susceptibility | MIL-STD-461G, RS103 | Radiated susceptibility, 2 MHz – 40 GHz |

---

## 5. Test Categories for the Pilot

The servo amplifier control card requires testing across five distinct categories. MoogTestAI is designed to generate test procedures for each of these categories from the design specification documents.

### 5.1 Functional Testing

Validates that the card performs its intended functions correctly under nominal conditions.

**Key Test Areas:**
- PWM generation accuracy (frequency, duty cycle, dead-time)
- Current control loop response (step response, steady-state error)
- ADC conversion accuracy (linearity, offset, gain)
- DAC output accuracy (if applicable)
- Watchdog timer operation (timeout detection, fault assertion)
- Power-on reset and initialization sequence
- Firmware version verification and integrity check

### 5.2 Boundary & Stress Testing

Verifies behavior at the limits of specified operating parameters and slightly beyond.

**Key Test Areas:**
- Input voltage extremes (24V low-line, 32V high-line for 28V nominal)
- Maximum current loading on gate drive outputs
- PWM duty cycle extremes (0.1% and 99.9%)
- ADC performance at full-scale positive and negative inputs
- Communication bus at maximum clock frequency and cable length
- Clock frequency tolerance at temperature extremes
- Operation at minimum and maximum supply current

### 5.3 Communication Protocol Testing

Validates all digital communication interfaces for protocol compliance, data integrity, and error handling.

**Key Test Areas:**
- SPI register read/write verification (all configurable registers)
- SPI clock stretching and chip-select timing
- EtherCAT state machine transitions (INIT → PRE-OP → SAFE-OP → OP)
- EtherCAT distributed clock synchronization accuracy
- UART framing error detection and recovery
- GPIO input debouncing and output drive strength
- Encoder interface signal integrity at maximum frequency

### 5.4 Environmental Testing

Validates that the card meets performance specifications across the full range of environmental conditions.

**Key Test Areas:**
- Functional verification at -40°C, +25°C, and +85°C
- Parametric measurement drift across temperature range
- Thermal shutdown threshold verification
- Vibration survivability (random and sinusoidal profiles)
- Mechanical shock withstand capability
- Humidity exposure and insulation resistance
- EMI emissions compliance (conducted and radiated)
- EMI susceptibility verification

### 5.5 Fault Injection & Recovery Testing

Validates that the card detects, reports, and safely responds to fault conditions.

**Key Test Areas:**
- Overvoltage detection and shutdown
- Overcurrent protection activation
- Over-temperature shutdown and recovery hysteresis
- Communication timeout detection (watchdog)
- Motor phase open/short detection
- Power supply sequencing violations
- Firmware corruption detection (CRC/checksum validation)
- Graceful degradation under partial power loss

---

## 6. How MoogTestAI Uses This Pilot

### 6.1 Document Ingestion

The following design documents for the servo amplifier control card are ingested into MoogTestAI's RAG pipeline:

1. **Design Specification (PDF)** — Contains all electrical, timing, and environmental specifications listed above. This is the primary source document for test plan generation.
2. **Schematic (PDF export)** — Circuit-level detail for understanding signal paths, component values, and test point locations.
3. **Bill of Materials (CSV/PDF)** — Component list with part numbers, values, and tolerances.
4. **Acceptance Test Procedure (PDF)** — Existing manual test procedure used as a reference baseline for AI-generated plans.

### 6.2 AI Deliverables for This Pilot

MoogTestAI generates the following deliverables from the ingested pilot design documents:

| Deliverable | Description | Source Data |
|---|---|---|
| **Test Plan** | Comprehensive test procedure with steps, parameters, expected results, and equipment list | Design spec + schematic |
| **Signal Analysis** | Interpretation of waveform data against expected behavior | Design spec + test results |
| **Risk Assessment Matrix** | Prioritized risk identification using FMEA-style severity/occurrence/detection scoring | Design spec + BOM |
| **Debug Report** | Root cause analysis and corrective action recommendations for test failures | Design spec + failure symptoms |
| **Boundary Analysis** | Identification of critical parameter boundaries and recommended guard bands | Design spec |

### 6.3 Validation Strategy

The AI-generated test plans are validated against the existing manual acceptance test procedure by:

1. **Coverage comparison:** Do the AI-generated tests cover all parameters in the manual ATP?
2. **Specification accuracy:** Are voltage, current, and timing values consistent with the design spec?
3. **Completeness check:** Does the AI identify test cases that the manual procedure missed?
4. **Practical feasibility:** Are the generated test steps executable with available equipment?

---

## 7. Generalization Path

The servo amplifier control card pilot is designed to establish patterns that generalize to Moog's broader product portfolio:

| Future Target | Shared Architecture Elements |
|---|---|
| Brushless motor controller | PWM generation, current sensing, communication interfaces |
| Electrohydraulic valve driver | Analog control, current loop, fault detection |
| Power distribution unit | Voltage regulation, protection circuits, monitoring |
| Sensor interface card | ADC accuracy, signal conditioning, protocol handling |
| Safety monitoring module | Watchdog, fault injection, redundancy verification |

The ingestion pipeline, agent architecture, and MCP tool interfaces built for the pilot are designed to work with any hardware design document — the domain-specific knowledge comes from the documents themselves, not from hardcoded logic.

---

*Document Version: 1.0 | Last Updated: June 2026*
