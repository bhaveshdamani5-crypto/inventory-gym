import asyncio
import os
import json
from typing import List
from openai import OpenAI
from dotenv import load_dotenv
import argparse

# Load local .env file if it exists
load_dotenv()
from inventory_gym.env import InventoryGymEnv
from inventory_gym.models import Action

parser = argparse.ArgumentParser()
parser.add_argument("--task", type=str, default=None)
parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-72B-Instruct")
args = parser.parse_args()

# Configuration from Environment Variables
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = args.model
API_KEY = os.getenv("HF_TOKEN")

TASK_NAME = args.task
BENCHMARK = "InventoryGym-v1"

# Task Mapping
CONFIGS = {
    "inventory-easy": {"num_warehouses": 1, "num_steps": 50, "lead_time": 5},
    "inventory-medium": {"num_warehouses": 3, "num_steps": 100, "lead_time": 4},
    "inventory-hard": {"num_warehouses": 5, "num_steps": 100, "lead_time": 3}
}

config = CONFIGS.get(TASK_NAME, CONFIGS["inventory-medium"])
MAX_STEPS = config["num_steps"]

SYSTEM_PROMPT = """
You are the AEGIS Supply Intelligence Agent.
GOAL: Maintain a 96%+ Service Level while minimizing holding costs.

STRATEGY:
- Safety Stock = (Forecasted Demand for 5 steps) * 1.5. 
- If Current Inventory < Safety Stock -> ORDER immediately.
- Use 'expedited' if a SHOCK is active or inventory is < 10% capacity.
- Use 'transfer' to balance stock from Over-filled nodes to Under-filled nodes.

COMMANDS:
1. 'order <dest_id> <qty> [priority]'
2. 'transfer <from_id> <to_id> <qty> [priority]'

REASONING:
- Pay close attention to 'market_intel'. If news suggests a shock in a region, PROACTIVELY stockpile or transship stock away from affected nodes.
- 'expedited' shipping is critical during shocks.

STRICT OUTPUT: Respond ONLY with the command.
"""

def log_start(task: str, env: str, model: str):
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: str = "null"):
    done_str = "true" if done else "false"
    error_str = error if error is not None and error != "" else "null"
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_str} error={error_str}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]):
    success_str = "true" if success else "false"
    clamped_score = max(0.01, min(0.99, score))
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={success_str} steps={steps} score={clamped_score:.2f} rewards={rewards_str}", flush=True)

async def run_task(task_name: str, client: OpenAI):
    """Run a single task and log the results."""
    config = CONFIGS.get(task_name, CONFIGS["inventory-medium"])
    MAX_STEPS = config["num_steps"]
    
    env = InventoryGymEnv(**config, difficulty=task_name)
    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)
    
    rewards = []
    steps_taken = 0
    success = False
    score = 0.0

    try:
        reset_resp = await env.reset()
        obs = reset_resp.observation

        for step in range(1, MAX_STEPS + 1):
            # --- Strict AI decision logic ---
            state_summary = {
                "cycle": obs.current_step,
                "nodes": obs.warehouses,
                "forecast": obs.forecasted_demand,
                "pending": obs.pending_orders,
                "market_intel": obs.market_intel,
                "last_event": obs.last_action
            }
            
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"State: {json.dumps(state_summary)}"}
                    ],
                    max_tokens=30,
                    temperature=0
                )
                action_text = response.choices[0].message.content.strip().lower()
            except Exception as e:
                print(f"STRICT ERROR: AI Model failed to respond: {e}")
                break

            # Parse action logic 
            parts = action_text.replace(",", "").split()
            dest_id, origin_id, qty, priority = 0, -1, 0.0, "normal"
            
            try:
                if "order" in parts:
                    dest_id = int(parts[1])
                    qty = float(parts[2])
                    if len(parts) > 3: priority = parts[3] if parts[3] in ["normal", "expedited"] else "normal"
                elif "transfer" in parts:
                    origin_id = int(parts[1])
                    dest_id = int(parts[2])
                    qty = float(parts[3])
                    if len(parts) > 4: priority = parts[4] if parts[4] in ["normal", "expedited"] else "normal"
                else:
                    # Fallback to no-op
                    pass 
            except Exception:
                pass 

            action = Action(dest_warehouse=dest_id, origin_warehouse=origin_id, quantity=qty, priority=priority)
            step_resp = await env.step(action)
            obs = step_resp.observation
            
            reward = step_resp.reward
            rewards.append(reward)
            steps_taken = step
            
            log_step(step=step, action=action_text, reward=reward, done=step_resp.done)
            if step_resp.done: break

        final_state = await env.state()
        score = final_state.get("service_level", 0.0)
        success = score >= 0.85 

    finally:
        await env.close()
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

async def main():
    if not API_KEY:
        print("CRITICAL ERROR: HF_TOKEN was not found.")
        return

    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    
    # If a specific task is provided, run only that. Otherwise run all for validation.
    if args.task and args.task in CONFIGS:
        await run_task(args.task, client)
    else:
        for task_name in CONFIGS.keys():
            await run_task(task_name, client)

if __name__ == "__main__":
    asyncio.run(main())