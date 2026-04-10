#!/usr/bin/env python3
"""
Demo script for AuditGym-v1 OpenEnv environment.
Runs one sample episode with predefined actions to demonstrate the environment.
"""

import asyncio
from src.env import AuditGymEnv
from src.models import Action

async def main():
    print("AuditGym-v1 Demo")
    print("=" * 50)

    # Create environment for hard task
    env = AuditGymEnv(num_total=1000, num_fraud=5, num_red_herring=50, max_steps=10)  # Short for demo

    # Reset
    result = await env.reset()
    print(f"Initial observation: {len(result.observation.transactions)} transactions")
    print(f"Step count: {result.observation.step_count}")

    # Sample actions
    actions = [
        "query amount > 5000",
        "verify id 0",
        "flag id 0",
        "query amount < 0",  # Look for negative amounts (fraud)
        "verify id 1",
        "flag id 1"
    ]

    total_reward = 0.0
    for i, action_msg in enumerate(actions, 1):
        print(f"\nStep {i}: Action = {action_msg}")
        result = await env.step(Action(message=action_msg))
        reward = result.reward
        total_reward += reward
        print(f"Reward: {reward:+.2f}, Done: {result.done}")
        print(f"Remaining transactions: {len(result.observation.transactions)}")
        state = await env.state()
        print(f"Flagged frauds: {state['flagged_frauds']}")

        if result.done:
            break

    print(f"\nEpisode finished. Total reward: {total_reward:.2f}")
    state = await env.state()
    print(f"Final state: {state}")

    await env.close()

if __name__ == "__main__":
    asyncio.run(main())