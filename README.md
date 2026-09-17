# Industrial Simulation Gyms

RL training environments for industrial automation — built from real product data extracted from Siemens TIA Portal V14, FANUC ROBOGUIDE, ABB RobotStudio, and OMRON CX-One.

**Goal**: Train LLM agents on realistic multi-step industrial workflows that SOTA models cannot do today — not fact recall, but agentic system operation: commissioning equipment, writing programs, tuning control loops, diagnosing faults, and running production.

## Environments

### Robot Gyms

| Environment | What the Agent Learns | Vendor | Key Challenge |
|---|---|---|---|
| `FanucCommissioningEnv` | Commission a new robot cell from scratch | FANUC | Multi-step workflow with dependencies |
| `FanucTroubleshootingEnv` | Diagnose and recover from robot faults | FANUC | Alarm interpretation → corrective action |
| `FanucProductionEnv` | Run production with disturbances | FANUC | Adaptive decision-making under uncertainty |
| `FanucMotionTuningEnv` | Optimize cycle time vs accuracy | FANUC | Multi-objective tradeoff |
| `ABBProgrammingEnv` | Write RAPID programs for tasks | ABB | Code generation with physical constraints |
| `ABBTuningEnv` | Tune speed/zone/acceleration | ABB | Real robot dynamics tradeoffs |
| `ABBFaultRecoveryEnv` | Recover from motion/system errors | ABB | Error code interpretation + recovery |
| `ABBCellConfigEnv` | Configure multi-robot cell | ABB | System architecture decisions |

### PLC Gyms

| Environment | What the Agent Learns | Vendor | Key Challenge |
|---|---|---|---|
| `S7ProgrammingEnv` | Write STL/SCL PLC programs | Siemens | Code synthesis with hardware constraints |
| `S7PIDTuningEnv` | Tune cascade/ratio PID loops | Siemens | Process dynamics + interaction effects |
| `S7DiagnosticsEnv` | Diagnose plant faults | Siemens | Fault isolation from noisy observations |
| `S7CommissioningEnv` | Commission PLC from scratch | Siemens | Configuration workflow with ordering |
| `S7ProcessControlEnv` | Operate a batch process plant | Siemens | Sequence management + alarm response |
| `OmronProgrammingEnv` | Write ladder logic programs | OMRON | Visual programming synthesis |
| `OmronLadderDebugEnv` | Debug buggy PLC programs | OMRON | Logic error localization |
| `OmronProcessEnv` | Operate conveyor production line | OMRON | Throughput optimization + fault recovery |
| `OmronMotionControlEnv` | Configure and tune servo axes | OMRON | Servo dynamics + tuning |
| `OmronNetworkEnv` | Configure fieldbus network | OMRON | Network topology + addressing |

## What Makes These Different

These aren't toy environments. They're built from:
- **Real product data**: DH parameters, motor specs, gear ratios from actual robots
- **Real instruction sets**: 172 STL instructions, 452 OMRON instructions, full KAREL/RAPID/SCL languages
- **Real error codes**: Actual alarm codes and diagnostic messages from each vendor
- **Real workflows**: Multi-step procedures matching what engineers do on real equipment
- **Real physics**: Forward/inverse kinematics, Jacobian dynamics, PID control theory, nonlinear plant models

The observation spaces match what an operator actually sees (teach pendant displays, HMI screens, diagnostic buffers). The action spaces match what an operator actually does (button presses, parameter edits, program modifications).

## Source Repos — Proprietary Data (VM-Extracted)

| Repo | Data | Key Moat Assets |
|---|---|---|
| [fanuc-robots](https://github.com/canyon-tractian/fanuc-robots) | 50MB, 30 JSON, 6,894 raw programs | 6,980 system vars, 269 builtins, 2,133 TP programs, 39,276 instructions |
| [abb-robots](https://github.com/canyon-tractian/abb-robots) | 34MB, 78 JSON | 1,458 drive params, 1,074 robot models, dynamics |
| [omron-plc](https://github.com/canyon-tractian/omron-plc) | 85MB, 25 JSON | **21,314 drive params**, 5,554 devices, 191 error codes, 492 EDS devices |
| [siemens-plc](https://github.com/canyon-tractian/siemens-plc) | 420MB+, 48 JSON | **2,114 SINAMICS params**, 5,869 TIA diagnostics, 13 GSDML profiles |
| [schneider-data](https://github.com/canyon-tractian/schneider-data) | 14MB, 20 JSON | 22,669 VFD params across 17 products |
| [kuka-data](https://github.com/canyon-tractian/kuka-data) | 2MB, 10 JSON | WorkVisual machine data, drive configs, robot catalog |

## Quarantined Repos — Web-Sourced (NOT Moat)

| Repo | Data | Notes |
|---|---|---|
| [public-docs-quarantine](https://github.com/canyon-tractian/public-docs-quarantine) | Rockwell, Mitsubishi, KUKA KRL | Web research — SOTA gets 85%+ on this |
| [rockwell-data](https://github.com/canyon-tractian/rockwell-data) | 223 instructions, 47 CIP objects | Public Logix 5000 docs |
| [mitsubishi-data](https://github.com/canyon-tractian/mitsubishi-data) | 400+ MELSEC instructions | Public GX Works docs |

## Benchmark Moat — Drive Parameter Recall

| Vendor | Parameters | SOTA Accuracy | Source |
|---|---|---|---|
| Schneider ATV71/ATV340 | 22,669 | ~60% fail on long-tail | DTM exports |
| OMRON 3G3/MX2/R88 | 21,314 | **0% for servo addresses** | CX-Drive VM |
| SINAMICS G120/S120 | 2,114 | ~60% fail on long-tail | TIA Portal VM |
| ABB ACS880 | 1,458 | ~60% fail on long-tail | Drive Composer |
| **Total** | **47,555** | | |
