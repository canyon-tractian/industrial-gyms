#!/usr/bin/env python3
"""
Training utilities for industrial RL gym environments.

Provides episode logging, reward analysis, curriculum progression,
and standard evaluation protocols across all gym environments.
"""

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Episode recording
# ---------------------------------------------------------------------------

@dataclass
class StepRecord:
    """Record of a single environment step."""
    step: int
    action: Any
    reward: float
    terminated: bool
    truncated: bool
    info: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0


@dataclass
class EpisodeRecord:
    """Full record of an episode."""
    env_id: str
    episode_id: int
    seed: Optional[int]
    steps: List[StepRecord] = field(default_factory=list)
    total_reward: float = 0.0
    total_steps: int = 0
    success: bool = False
    start_time: float = 0.0
    end_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_s(self) -> float:
        return self.end_time - self.start_time

    @property
    def avg_reward(self) -> float:
        return self.total_reward / max(self.total_steps, 1)

    def summary(self) -> Dict[str, Any]:
        return {
            'env_id': self.env_id,
            'episode_id': self.episode_id,
            'total_reward': round(self.total_reward, 4),
            'total_steps': self.total_steps,
            'success': self.success,
            'duration_s': round(self.duration_s, 2),
            'avg_reward': round(self.avg_reward, 4),
        }


class EpisodeLogger:
    """Log episodes for analysis and training data generation."""

    def __init__(self, log_dir: Optional[str] = None):
        self.episodes: List[EpisodeRecord] = []
        self.log_dir = Path(log_dir) if log_dir else None
        if self.log_dir:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        self._current: Optional[EpisodeRecord] = None
        self._episode_counter = 0

    def start_episode(self, env_id: str, seed: Optional[int] = None,
                      metadata: Optional[Dict] = None) -> EpisodeRecord:
        """Start recording a new episode."""
        self._episode_counter += 1
        self._current = EpisodeRecord(
            env_id=env_id,
            episode_id=self._episode_counter,
            seed=seed,
            start_time=time.time(),
            metadata=metadata or {},
        )
        return self._current

    def log_step(self, action: Any, reward: float,
                 terminated: bool, truncated: bool,
                 info: Optional[Dict] = None):
        """Log a single step."""
        if self._current is None:
            raise RuntimeError("No episode started. Call start_episode() first.")
        step = StepRecord(
            step=self._current.total_steps,
            action=_serialize(action),
            reward=reward,
            terminated=terminated,
            truncated=truncated,
            info=_serialize(info or {}),
            timestamp=time.time(),
        )
        self._current.steps.append(step)
        self._current.total_reward += reward
        self._current.total_steps += 1

    def end_episode(self, success: bool = False) -> EpisodeRecord:
        """End the current episode and save it."""
        if self._current is None:
            raise RuntimeError("No episode to end.")
        self._current.end_time = time.time()
        self._current.success = success
        self.episodes.append(self._current)

        if self.log_dir:
            path = self.log_dir / f"episode_{self._current.episode_id:06d}.json"
            with open(path, 'w') as f:
                json.dump(asdict(self._current), f, indent=2, default=str)

        ep = self._current
        self._current = None
        return ep

    def stats(self) -> Dict[str, Any]:
        """Compute aggregate statistics across logged episodes."""
        if not self.episodes:
            return {'num_episodes': 0}

        rewards = [e.total_reward for e in self.episodes]
        steps = [e.total_steps for e in self.episodes]
        successes = [e.success for e in self.episodes]

        return {
            'num_episodes': len(self.episodes),
            'success_rate': sum(successes) / len(successes),
            'avg_reward': sum(rewards) / len(rewards),
            'min_reward': min(rewards),
            'max_reward': max(rewards),
            'avg_steps': sum(steps) / len(steps),
            'total_steps': sum(steps),
        }


# ---------------------------------------------------------------------------
# Evaluation protocol
# ---------------------------------------------------------------------------

def evaluate_env(env, agent_fn, n_episodes: int = 10,
                 max_steps: int = 200, seed: int = 42,
                 verbose: bool = False) -> Dict[str, Any]:
    """Standard evaluation protocol for any gym environment.

    Args:
        env: A gym environment with reset()/step()
        agent_fn: Callable(obs, info) -> action
        n_episodes: Number of evaluation episodes
        max_steps: Maximum steps per episode
        seed: Base random seed
        verbose: Print episode summaries

    Returns:
        Dict with aggregate metrics
    """
    logger = EpisodeLogger()

    for ep in range(n_episodes):
        ep_seed = seed + ep
        obs, info = env.reset(seed=ep_seed)
        logger.start_episode(
            env_id=getattr(env, 'env_id', type(env).__name__),
            seed=ep_seed,
        )

        for step in range(max_steps):
            action = agent_fn(obs, info)
            obs, reward, terminated, truncated, info = env.step(action)
            logger.log_step(action, reward, terminated, truncated, info)

            if terminated or truncated:
                break

        success = info.get('success', False) if isinstance(info, dict) else False
        record = logger.end_episode(success=success)

        if verbose:
            print(f"  Episode {ep+1}/{n_episodes}: "
                  f"reward={record.total_reward:.2f}, "
                  f"steps={record.total_steps}, "
                  f"success={record.success}")

    stats = logger.stats()
    if verbose:
        print(f"\n  Aggregate: {stats}")
    return stats


# ---------------------------------------------------------------------------
# Curriculum manager
# ---------------------------------------------------------------------------

class CurriculumManager:
    """Manages progression through increasingly difficult environments.

    Tracks performance per environment and suggests when to advance.
    """

    def __init__(self, curriculum: Dict[str, Dict[str, Any]],
                 advance_threshold: float = 0.7,
                 min_episodes: int = 10):
        """
        Args:
            curriculum: Dict with level keys and 'envs' list values
            advance_threshold: Success rate required to advance
            min_episodes: Minimum episodes at a level before advancing
        """
        self.curriculum = curriculum
        self.advance_threshold = advance_threshold
        self.min_episodes = min_episodes
        self.current_level_idx = 0
        self.levels = list(curriculum.keys())
        self.performance: Dict[str, List[bool]] = {}

    @property
    def current_level(self) -> str:
        return self.levels[self.current_level_idx]

    @property
    def current_envs(self) -> List[str]:
        return self.curriculum[self.current_level]['envs']

    def record_result(self, env_id: str, success: bool):
        """Record the result of an episode."""
        self.performance.setdefault(env_id, []).append(success)

    def should_advance(self) -> bool:
        """Check if the agent should advance to the next curriculum level."""
        if self.current_level_idx >= len(self.levels) - 1:
            return False

        for env_id in self.current_envs:
            results = self.performance.get(env_id, [])
            if len(results) < self.min_episodes:
                return False
            recent = results[-self.min_episodes:]
            if sum(recent) / len(recent) < self.advance_threshold:
                return False
        return True

    def advance(self) -> bool:
        """Advance to next level if ready. Returns True if advanced."""
        if self.should_advance():
            self.current_level_idx += 1
            return True
        return False

    def status(self) -> Dict[str, Any]:
        """Get current curriculum status."""
        level_status = {}
        for env_id in self.current_envs:
            results = self.performance.get(env_id, [])
            level_status[env_id] = {
                'episodes': len(results),
                'success_rate': sum(results) / max(len(results), 1),
                'ready': (len(results) >= self.min_episodes and
                         sum(results[-self.min_episodes:]) / self.min_episodes >= self.advance_threshold),
            }
        return {
            'current_level': self.current_level,
            'level_index': self.current_level_idx,
            'total_levels': len(self.levels),
            'envs': level_status,
            'ready_to_advance': self.should_advance(),
        }


# ---------------------------------------------------------------------------
# SFT data generation
# ---------------------------------------------------------------------------

def episode_to_sft_conversation(record: EpisodeRecord,
                                 system_prompt: str = "") -> List[Dict[str, str]]:
    """Convert a successful episode into an SFT training conversation.

    Generates a multi-turn conversation where the assistant's actions
    are the training targets.

    Args:
        record: A completed episode record
        system_prompt: System prompt for the conversation

    Returns:
        List of message dicts with 'role' and 'content' keys
    """
    messages = []
    if system_prompt:
        messages.append({'role': 'system', 'content': system_prompt})

    # Initial observation as user message
    messages.append({
        'role': 'user',
        'content': f"Environment: {record.env_id}\n"
                   f"Task: Complete the industrial workflow.\n"
                   f"Initial state:\n{json.dumps(record.metadata.get('initial_obs', {}), indent=2)}"
    })

    for step in record.steps:
        # Assistant action
        messages.append({
            'role': 'assistant',
            'content': f"Action: {json.dumps(step.action)}\n"
                       f"Reasoning: Based on the current state, I chose this action to progress the task."
        })

        # Environment response as user message (if not the last step)
        if step.step < record.total_steps - 1:
            messages.append({
                'role': 'user',
                'content': f"Result: reward={step.reward:.3f}\n"
                           f"State: {json.dumps(step.info, indent=2, default=str)}"
            })

    return messages


def generate_sft_dataset(episodes: List[EpisodeRecord],
                          output_path: str,
                          min_reward: float = 0.0,
                          success_only: bool = True):
    """Generate an SFT dataset from successful episodes.

    Args:
        episodes: List of episode records
        output_path: Path to write JSONL output
        min_reward: Minimum total reward to include
        success_only: Only include successful episodes
    """
    count = 0
    with open(output_path, 'w') as f:
        for ep in episodes:
            if success_only and not ep.success:
                continue
            if ep.total_reward < min_reward:
                continue

            conv = episode_to_sft_conversation(ep)
            f.write(json.dumps({
                'messages': conv,
                'env_id': ep.env_id,
                'total_reward': ep.total_reward,
                'total_steps': ep.total_steps,
            }, default=str) + '\n')
            count += 1

    print(f"Generated {count} SFT examples from {len(episodes)} episodes → {output_path}")


# ---------------------------------------------------------------------------
# Reward analysis
# ---------------------------------------------------------------------------

def analyze_rewards(episodes: List[EpisodeRecord]) -> Dict[str, Any]:
    """Analyze reward distribution across episodes."""
    if not episodes:
        return {}

    rewards_per_step = {}
    for ep in episodes:
        for step in ep.steps:
            rewards_per_step.setdefault(step.step, []).append(step.reward)

    step_stats = {}
    for step_idx in sorted(rewards_per_step.keys()):
        vals = rewards_per_step[step_idx]
        step_stats[step_idx] = {
            'mean': sum(vals) / len(vals),
            'min': min(vals),
            'max': max(vals),
            'count': len(vals),
        }

    total_rewards = [ep.total_reward for ep in episodes]
    return {
        'total_reward': {
            'mean': sum(total_rewards) / len(total_rewards),
            'min': min(total_rewards),
            'max': max(total_rewards),
            'std': _std(total_rewards),
        },
        'per_step': step_stats,
        'num_episodes': len(episodes),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _serialize(obj: Any) -> Any:
    """Make an object JSON-serializable."""
    if hasattr(obj, 'tolist'):
        return obj.tolist()
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize(v) for v in obj]
    return obj


def _std(values: List[float]) -> float:
    """Standard deviation."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return variance ** 0.5


if __name__ == '__main__':
    print("Training utilities loaded.")
    print(f"  EpisodeLogger — record and analyze episodes")
    print(f"  evaluate_env — standard evaluation protocol")
    print(f"  CurriculumManager — curriculum-based training progression")
    print(f"  generate_sft_dataset — convert episodes to SFT training data")
    print(f"  analyze_rewards — reward distribution analysis")
