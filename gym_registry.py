#!/usr/bin/env python3
"""
Industrial Simulation Gym Registry
====================================

Unified registry that discovers and loads all industrial RL gym environments
across FANUC, ABB, Siemens, and OMRON repos.

Usage:
    from gym_registry import GymRegistry

    registry = GymRegistry()
    registry.list_envs()                    # Show all available environments
    env = registry.make('fanuc/commissioning')  # Create an environment
    obs, info = env.reset()
    obs, reward, term, trunc, info = env.step(action)
"""

import importlib
import importlib.util
import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Repo discovery
# ---------------------------------------------------------------------------

_REPO_BASE = Path(__file__).resolve().parent.parent  # one level up from industrial-gyms/

_REPO_MAP = {
    'fanuc': {
        'path': _REPO_BASE / 'fanuc-robots',
        'module': 'emulators.fanuc_gym',
        'envs': {
            'commissioning': 'FanucCommissioningEnv',
            'troubleshooting': 'FanucTroubleshootingEnv',
            'production': 'FanucProductionEnv',
            'motion_tuning': 'FanucMotionTuningEnv',
        },
        'description': 'FANUC industrial robots — 289 models, KAREL/TP interpreter',
    },
    'abb': {
        'path': _REPO_BASE / 'abb-robots',
        'module': 'emulators.abb_gym',
        'envs': {
            'programming': 'ABBProgrammingEnv',
            'tuning': 'ABBTuningEnv',
            'fault_recovery': 'ABBFaultRecoveryEnv',
            'cell_config': 'ABBCellConfigEnv',
        },
        'description': 'ABB industrial robots — 1,074 models, RAPID interpreter',
    },
    'siemens': {
        'path': _REPO_BASE / 'siemens-plc',
        'module': 'emulators.siemens_gym',
        'envs': {
            'programming': 'S7ProgrammingEnv',
            'pid_tuning': 'S7PIDTuningEnv',
            'diagnostics': 'S7DiagnosticsEnv',
            'commissioning': 'S7CommissioningEnv',
            'process_control': 'S7ProcessControlEnv',
        },
        'description': 'Siemens S7 PLCs — STL/SCL compilers, PID, plant models',
    },
    'omron': {
        'path': _REPO_BASE / 'omron-plc',
        'module': 'emulators.omron_gym',
        'envs': {
            'programming': 'OmronProgrammingEnv',
            'troubleshooting': 'OmronTroubleshootingEnv',
            'process_control': 'OmronProcessControlEnv',
            'network': 'OmronNetworkConfigEnv',
            'ladder_debug': 'OmronLadderDebugEnv',
            'process': 'OmronProcessEnv',
            'motion_control': 'OmronMotionControlEnv',
        },
        'description': 'OMRON PLCs — 46 opcodes, 452 instructions, CX-One data',
    },
}


# ---------------------------------------------------------------------------
# Environment metadata
# ---------------------------------------------------------------------------

ENV_METADATA = {
    # FANUC
    'fanuc/commissioning': {
        'name': 'FanucCommissioningEnv',
        'category': 'workflow',
        'difficulty': 'hard',
        'action_type': 'discrete',
        'description': 'Commission a FANUC robot cell from scratch — power on, master, set frames, teach, program, test run',
        'skills': ['system_operation', 'configuration', 'sequencing'],
    },
    'fanuc/troubleshooting': {
        'name': 'FanucTroubleshootingEnv',
        'category': 'diagnostics',
        'difficulty': 'hard',
        'action_type': 'discrete',
        'description': 'Diagnose and recover from FANUC servo/motion/system alarms using real alarm codes',
        'skills': ['fault_diagnosis', 'error_interpretation', 'recovery_procedures'],
    },
    'fanuc/production': {
        'name': 'FanucProductionEnv',
        'category': 'operation',
        'difficulty': 'medium',
        'action_type': 'mixed',
        'description': 'Run pick-and-place production with part misalignment, gripper slip, conveyor variation',
        'skills': ['process_optimization', 'disturbance_handling', 'quality_control'],
    },
    'fanuc/motion_tuning': {
        'name': 'FanucMotionTuningEnv',
        'category': 'tuning',
        'difficulty': 'medium',
        'action_type': 'continuous',
        'description': 'Optimize FANUC motion parameters — speed, acceleration, CNT zone, payload',
        'skills': ['parameter_tuning', 'trajectory_optimization', 'tradeoff_analysis'],
    },
    # ABB
    'abb/programming': {
        'name': 'ABBProgrammingEnv',
        'category': 'programming',
        'difficulty': 'hard',
        'action_type': 'text',
        'description': 'Write RAPID programs to accomplish robot tasks — pick-place, welding, palletizing',
        'skills': ['code_generation', 'robot_programming', 'motion_planning'],
    },
    'abb/tuning': {
        'name': 'ABBTuningEnv',
        'category': 'tuning',
        'difficulty': 'medium',
        'action_type': 'continuous',
        'description': 'Tune ABB speeddata/zonedata/AccSet for optimal cycle time vs path accuracy',
        'skills': ['parameter_tuning', 'motion_dynamics', 'tradeoff_analysis'],
    },
    'abb/fault_recovery': {
        'name': 'ABBFaultRecoveryEnv',
        'category': 'diagnostics',
        'difficulty': 'hard',
        'action_type': 'discrete',
        'description': 'Diagnose and recover from ABB 50xxx/20xxx errors, SafeMove violations, collisions',
        'skills': ['fault_diagnosis', 'error_interpretation', 'state_machine_operation'],
    },
    'abb/cell_config': {
        'name': 'ABBCellConfigEnv',
        'category': 'workflow',
        'difficulty': 'hard',
        'action_type': 'discrete',
        'description': 'Configure multi-robot ABB cell — work objects, tools, I/O mapping, coordination',
        'skills': ['system_architecture', 'configuration', 'dependency_management'],
    },
    # Siemens
    'siemens/programming': {
        'name': 'S7ProgrammingEnv',
        'category': 'programming',
        'difficulty': 'hard',
        'action_type': 'text',
        'description': 'Write STL/SCL PLC programs from I/O specifications — logic, timers, counters, math',
        'skills': ['code_generation', 'plc_programming', 'logic_design'],
    },
    'siemens/pid_tuning': {
        'name': 'S7PIDTuningEnv',
        'category': 'tuning',
        'difficulty': 'hard',
        'action_type': 'continuous',
        'description': 'Tune cascade/ratio PID loops on plants with dead time, nonlinearity, noise',
        'skills': ['pid_tuning', 'process_dynamics', 'control_theory'],
    },
    'siemens/diagnostics': {
        'name': 'S7DiagnosticsEnv',
        'category': 'diagnostics',
        'difficulty': 'hard',
        'action_type': 'discrete',
        'description': 'Diagnose sensor/actuator/network faults from PLC diagnostic buffer and I/O values',
        'skills': ['fault_diagnosis', 'signal_analysis', 'systematic_troubleshooting'],
    },
    'siemens/commissioning': {
        'name': 'S7CommissioningEnv',
        'category': 'workflow',
        'difficulty': 'medium',
        'action_type': 'discrete',
        'description': 'Commission S7 PLC — select CPU, configure I/O, assign addresses, download, test',
        'skills': ['system_operation', 'hardware_configuration', 'sequencing'],
    },
    'siemens/process_control': {
        'name': 'S7ProcessControlEnv',
        'category': 'operation',
        'difficulty': 'hard',
        'action_type': 'mixed',
        'description': 'Operate a batch process plant — fill, heat, mix, drain with safety interlocks',
        'skills': ['batch_control', 'alarm_management', 'process_optimization'],
    },
    # OMRON
    'omron/programming': {
        'name': 'OmronProgrammingEnv',
        'category': 'programming',
        'difficulty': 'hard',
        'action_type': 'continuous',
        'description': 'Write OMRON instruction-list (ladder) programs by selecting mnemonics and operands',
        'skills': ['code_generation', 'plc_programming', 'ladder_logic'],
    },
    'omron/troubleshooting': {
        'name': 'OmronTroubleshootingEnv',
        'category': 'diagnostics',
        'difficulty': 'medium',
        'action_type': 'continuous',
        'description': 'Diagnose and fix OMRON PLC faults — wrong addresses, stuck I/O, communication errors',
        'skills': ['fault_diagnosis', 'debugging', 'logic_analysis'],
    },
    'omron/process': {
        'name': 'OmronProcessControlEnv',
        'category': 'operation',
        'difficulty': 'medium',
        'action_type': 'continuous',
        'description': 'Operate a conveyor production line with stations, disturbances, and fault injection',
        'skills': ['process_operation', 'fault_recovery', 'throughput_optimization'],
    },
    'omron/network': {
        'name': 'OmronNetworkConfigEnv',
        'category': 'workflow',
        'difficulty': 'medium',
        'action_type': 'continuous',
        'description': 'Configure OMRON fieldbus network — EtherNet/IP, DeviceNet, node addressing, I/O mapping',
        'skills': ['network_configuration', 'fieldbus_setup', 'addressing'],
    },
    'omron/ladder_debug': {
        'name': 'OmronLadderDebugEnv',
        'category': 'diagnostics',
        'difficulty': 'medium',
        'action_type': 'continuous',
        'description': 'Find and fix bugs in OMRON ladder programs — wrong addresses, missing interlocks, timing errors',
        'skills': ['debugging', 'code_review', 'logic_analysis'],
    },
    'omron/process': {
        'name': 'OmronProcessEnv',
        'category': 'operation',
        'difficulty': 'medium',
        'action_type': 'continuous',
        'description': 'Operate 4-station conveyor line — load, drill, press, unload with jams and tool wear',
        'skills': ['process_operation', 'fault_recovery', 'throughput_optimization'],
    },
    'omron/motion_control': {
        'name': 'OmronMotionControlEnv',
        'category': 'tuning',
        'difficulty': 'hard',
        'action_type': 'continuous',
        'description': 'Tune 2-axis servo system — position/velocity gains, feedforward, following error minimization',
        'skills': ['servo_tuning', 'motion_control', 'dynamics_analysis'],
    },
}


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class GymRegistry:
    """Central registry for all industrial RL gym environments."""

    def __init__(self):
        self._loaded_modules: Dict[str, Any] = {}

    def list_envs(self, category: Optional[str] = None,
                  vendor: Optional[str] = None,
                  difficulty: Optional[str] = None,
                  action_type: Optional[str] = None) -> List[Dict[str, str]]:
        """List available environments with optional filtering.

        Args:
            category: Filter by category (programming, tuning, diagnostics, workflow, operation)
            vendor: Filter by vendor (fanuc, abb, siemens, omron)
            difficulty: Filter by difficulty (easy, medium, hard)
            action_type: Filter by action type (discrete, continuous, text, mixed)

        Returns:
            List of dicts with env_id, name, category, difficulty, description
        """
        results = []
        for env_id, meta in ENV_METADATA.items():
            v = env_id.split('/')[0]
            if vendor and v != vendor:
                continue
            if category and meta['category'] != category:
                continue
            if difficulty and meta['difficulty'] != difficulty:
                continue
            if action_type and meta['action_type'] != action_type:
                continue
            results.append({
                'env_id': env_id,
                'vendor': v,
                **meta,
            })
        return results

    def list_vendors(self) -> List[Dict[str, str]]:
        """List available vendors with descriptions and env counts."""
        return [
            {
                'vendor': k,
                'description': v['description'],
                'num_envs': len(v['envs']),
                'available': v['path'].exists(),
            }
            for k, v in _REPO_MAP.items()
        ]

    def list_categories(self) -> Dict[str, List[str]]:
        """List environment categories and which envs belong to each."""
        cats: Dict[str, List[str]] = {}
        for env_id, meta in ENV_METADATA.items():
            cats.setdefault(meta['category'], []).append(env_id)
        return cats

    def list_skills(self) -> Dict[str, List[str]]:
        """List all skills and which envs train them."""
        skills: Dict[str, List[str]] = {}
        for env_id, meta in ENV_METADATA.items():
            for skill in meta.get('skills', []):
                skills.setdefault(skill, []).append(env_id)
        return skills

    def _load_module(self, vendor: str) -> Any:
        """Dynamically load the gym module for a vendor.

        Uses subprocess isolation to avoid sys.path collisions between repos
        that have identically-named modules (e.g., robot_emulator.py in both
        FANUC and ABB repos).

        For in-process use, loads the module directly — but only one vendor's
        gym can be active per process due to module name collisions. Use
        make_subprocess() for cross-vendor work in a single process.
        """
        if vendor in self._loaded_modules:
            return self._loaded_modules[vendor]

        config = _REPO_MAP[vendor]
        repo_path = config['path']
        module_name = config['module']

        if not repo_path.exists():
            raise FileNotFoundError(
                f"Repo not found at {repo_path}. "
                f"Clone the {vendor} repo to that location."
            )

        # Clean up any conflicting modules from other repos
        # (e.g., robot_emulator from FANUC vs ABB)
        for mod_name in list(sys.modules.keys()):
            if mod_name in ('robot_emulator', 'rapid_interpreter',
                            'karel_interpreter', 'plc_emulator',
                            's7_plc_emulator'):
                del sys.modules[mod_name]

        # Put this repo's path at the front of sys.path
        repo_str = str(repo_path)
        emulator_str = str(repo_path / 'emulators')
        # Remove any other repo paths that might conflict
        for other_vendor, other_config in _REPO_MAP.items():
            if other_vendor != vendor:
                other_str = str(other_config['path'])
                other_emu = str(other_config['path'] / 'emulators')
                if other_str in sys.path:
                    sys.path.remove(other_str)
                if other_emu in sys.path:
                    sys.path.remove(other_emu)

        if emulator_str not in sys.path:
            sys.path.insert(0, emulator_str)
        if repo_str not in sys.path:
            sys.path.insert(0, repo_str)

        # Also remove cached emulator modules
        for mod_name in list(sys.modules.keys()):
            if mod_name.startswith('emulators.'):
                del sys.modules[mod_name]

        try:
            mod = importlib.import_module(module_name)
            self._loaded_modules[vendor] = mod
            return mod
        except ImportError as e:
            raise ImportError(
                f"Could not load {module_name} from {repo_path}: {e}"
            ) from e

    def make(self, env_id: str, **kwargs) -> Any:
        """Create an environment instance.

        Args:
            env_id: Environment ID in 'vendor/env_name' format
                    (e.g., 'fanuc/commissioning', 'siemens/pid_tuning')
            **kwargs: Additional keyword arguments passed to the env constructor

        Returns:
            An environment instance with reset()/step()/render()/close()
        """
        if '/' not in env_id:
            raise ValueError(
                f"Invalid env_id '{env_id}'. Use 'vendor/env_name' format "
                f"(e.g., 'fanuc/commissioning'). "
                f"Call list_envs() to see available environments."
            )

        vendor, env_name = env_id.split('/', 1)

        if vendor not in _REPO_MAP:
            raise ValueError(
                f"Unknown vendor '{vendor}'. "
                f"Available: {', '.join(_REPO_MAP.keys())}"
            )

        config = _REPO_MAP[vendor]
        if env_name not in config['envs']:
            raise ValueError(
                f"Unknown env '{env_name}' for vendor '{vendor}'. "
                f"Available: {', '.join(config['envs'].keys())}"
            )

        class_name = config['envs'][env_name]
        mod = self._load_module(vendor)
        env_class = getattr(mod, class_name)
        return env_class(**kwargs)

    def env_info(self, env_id: str) -> Dict[str, Any]:
        """Get detailed metadata about an environment."""
        if env_id not in ENV_METADATA:
            raise ValueError(f"Unknown env_id '{env_id}'")
        vendor = env_id.split('/')[0]
        config = _REPO_MAP[vendor]
        meta = ENV_METADATA[env_id]
        return {
            'env_id': env_id,
            'vendor': vendor,
            'repo_path': str(config['path']),
            'available': config['path'].exists(),
            **meta,
        }


# ---------------------------------------------------------------------------
# Curriculum — structured training progression
# ---------------------------------------------------------------------------

CURRICULUM = {
    'beginner': {
        'description': 'Start with basic tuning and simple operations',
        'envs': [
            'fanuc/motion_tuning',
            'abb/tuning',
            'omron/process',
            'siemens/commissioning',
        ],
    },
    'intermediate': {
        'description': 'Programming and diagnostics — write code, debug, diagnose',
        'envs': [
            'omron/programming',
            'omron/troubleshooting',
            'siemens/programming',
            'siemens/pid_tuning',
            'fanuc/production',
            'abb/fault_recovery',
        ],
    },
    'advanced': {
        'description': 'Complex multi-step workflows and system-level tasks',
        'envs': [
            'fanuc/commissioning',
            'fanuc/troubleshooting',
            'abb/programming',
            'abb/cell_config',
            'siemens/diagnostics',
            'siemens/process_control',
            'omron/network',
        ],
    },
}


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------

def make(env_id: str, **kwargs) -> Any:
    """Convenience function — creates a GymRegistry and makes the environment."""
    return GymRegistry().make(env_id, **kwargs)


def list_envs(**kwargs) -> List[Dict[str, str]]:
    """Convenience function — list all environments."""
    return GymRegistry().list_envs(**kwargs)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    """Print all available environments."""
    reg = GymRegistry()

    print("=" * 80)
    print("INDUSTRIAL SIMULATION GYM REGISTRY")
    print("=" * 80)

    print(f"\n{'Vendors':}")
    print("-" * 60)
    for v in reg.list_vendors():
        status = "✓" if v['available'] else "✗"
        print(f"  [{status}] {v['vendor']:10s} — {v['num_envs']} envs — {v['description']}")

    print(f"\n{'Environments':}")
    print("-" * 80)
    for env in reg.list_envs():
        print(f"  {env['env_id']:30s} [{env['difficulty']:6s}] [{env['action_type']:10s}] "
              f"{env['category']:12s}")
        print(f"    {env['description']}")

    print(f"\n{'Categories':}")
    print("-" * 60)
    for cat, envs in reg.list_categories().items():
        print(f"  {cat:15s}: {', '.join(envs)}")

    print(f"\n{'Skills':}")
    print("-" * 60)
    for skill, envs in sorted(reg.list_skills().items()):
        print(f"  {skill:30s}: {len(envs)} envs — {', '.join(envs)}")

    print(f"\n{'Curriculum':}")
    print("-" * 60)
    for level, info in CURRICULUM.items():
        print(f"\n  {level.upper()}: {info['description']}")
        for eid in info['envs']:
            meta = ENV_METADATA[eid]
            print(f"    → {eid:30s} {meta['description'][:50]}...")

    # Try to instantiate one env from each vendor
    print(f"\n{'Smoke Tests':}")
    print("-" * 60)
    test_envs = [
        'fanuc/motion_tuning',
        'abb/tuning',
        'siemens/pid_tuning',
        'omron/programming',
    ]
    for env_id in test_envs:
        vendor = env_id.split('/')[0]
        try:
            env = reg.make(env_id)
            result = env.reset()
            # Handle both (obs, info) and obs-only return conventions
            if isinstance(result, tuple):
                obs = result[0]
            else:
                obs = result
            obs_shape = getattr(obs, 'shape', type(obs).__name__)
            print(f"  ✓ {env_id:30s} — reset OK, obs type={type(obs).__name__}({obs_shape})")
            if hasattr(env, 'close'):
                env.close()
        except FileNotFoundError:
            print(f"  ✗ {env_id:30s} — repo not found")
        except ImportError as e:
            print(f"  ✗ {env_id:30s} — import error: {e}")
        except Exception as e:
            print(f"  ✗ {env_id:30s} — error: {e}")

    print(f"\nTotal: {len(ENV_METADATA)} environments across {len(_REPO_MAP)} vendors")


if __name__ == '__main__':
    main()
