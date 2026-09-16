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

## Source Repos

| Repo | Data | Emulators |
|---|---|---|
| [fanuc-robots](https://github.com/canyon-tractian/fanuc-robots) | 289 robots, KAREL/TP data, 719K words docs | Robot emulator + KAREL/TP interpreter + gym |
| [abb-robots](https://github.com/canyon-tractian/abb-robots) | 1,074 models, dynamics, 8,680 meshes | Robot emulator + RAPID interpreter + gym |
| [omron-plc](https://github.com/canyon-tractian/omron-plc) | 452 instructions, 3.24M words docs | PLC emulator + gym |
| [siemens-plc](https://github.com/canyon-tractian/siemens-plc) | 367 MB data, 6.6M words docs | PLC emulator + STL/SCL compilers + gym |
