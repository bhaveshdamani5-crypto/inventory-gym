#!/usr/bin/env python3
"""
Demo script for InventoryGym-v1 OpenEnv environment
Runs one sample episode demonstrating inventory management decisions
"""

import asyncio
from inventory_gym.env import InventoryGymEnv
from inventory_gym.models import Action

async def main():
    print("InventoryGym-v1 Demo: Supply Chain Management")
    print("=" * 60)

    # Create environment for hard task: 5 warehouses, complex demand
    env = InventoryGymEnv(num_warehouses=5, num_steps=20, lead_time=2, inventory_penalty_factor=2.0)

    # Reset
    result = await env.reset()
    print(f"\nInitial state:")
    print(f"  Warehouses: {len(result.observation.warehouses)}")
    print(f"  Total inventory: {sum(w['inventory'] for w in result.observation.warehouses):.0f} units")
    print(f"  Total cost: ${result.observation.total_cost:.2f}")

    # Simulate ordering decisions (agent learns to balance cost and demand)
    total_reward = 0.0
    sample_actions = [
        {"dest_warehouse": 0, "quantity": 300, "priority": "normal"},
        {"dest_warehouse": 1, "quantity": 250, "priority": "normal"},
        {"dest_warehouse": 2, "quantity": 400, "priority": "expedited"},  # Rush order
        {"dest_warehouse": 0, "quantity": 200, "priority": "normal"},
        {"dest_warehouse": 3, "quantity": 350, "priority": "normal"},
        {"dest_warehouse": 4, "quantity": 300, "priority": "normal"},
    ]

    for i, action_dict in enumerate(sample_actions, 1):
        action = Action(**action_dict)
        result = await env.step(action)
        
        reward = result.reward
        total_reward += reward
        
        inventory_levels = [f"{w['inventory']:.0f}" for w in result.observation.warehouses]
        print(f"\n[Step {i}]")
        print(f"  Action: Order {action.quantity:.0f} units to Warehouse-{chr(65+action.dest_warehouse)} ({action.priority})")
        print(f"  Reward: {reward:+.2f}")
        print(f"  Inventory levels: {inventory_levels}")
        print(f"  Pending orders: {len(result.observation.pending_orders)}")
        print(f"  Cost: ${result.observation.total_cost:.2f}")
        
        if result.done:
            break

    print(f"\n{'='*60}")
    print(f"Episode Summary:")
    print(f"  Total steps: {i}")
    print(f"  Total reward: {total_reward:.2f}")
    
    state = await env.state()
    print(f"  Final cost: ${result.observation.total_cost:.2f}")
    print(f"  Carbon Footprint: {result.observation.carbon_footprint:.0f} g/CO2")

    await env.close()
    print(f"\nDemo complete!")

if __name__ == "__main__":
    asyncio.run(main())