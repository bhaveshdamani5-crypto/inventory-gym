import asyncio
import os
from openai import OpenAI
from src.env import AuditGymEnv
from models import Action

# Configuration
TASK_NAME = os.getenv("TASK_NAME", "audit-hard")
BENCHMARK = "AuditGym-v1"
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4")
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("OPENAI_API_KEY")
MAX_STEPS = 100
TEMPERATURE = 0.7
MAX_TOKENS = 200
IMAGE_NAME = "auditgym:latest"

# Task configurations
TASK_CONFIGS = {
    "audit-easy": {"num_total": 100, "num_fraud": 1, "num_red_herring": 5, "max_steps": 50},
    "audit-medium": {"num_total": 500, "num_fraud": 3, "num_red_herring": 25, "max_steps": 100},
    "audit-hard": {"num_total": 1000, "num_fraud": 5, "num_red_herring": 50, "max_steps": 200}
}

config = TASK_CONFIGS.get(TASK_NAME, TASK_CONFIGS["audit-hard"])
MAX_TOTAL_REWARD = config["num_fraud"] * 0.95
SUCCESS_SCORE_THRESHOLD = 0.8

SYSTEM_PROMPT = """
You are an expert forensic auditor. Your task is to identify all fraudulent transactions in the dataset.

Transactions have: id, amount, date, description, verified (bool), extra_info (string).

Actions you can take (respond with one command per step):
- Query: "query amount > 5000" (filters to transactions with amount > 5000)
- Verify: "verify id 123" (gets cross-reference info for transaction 123)
- Flag: "flag id 123" (marks transaction 123 as fraudulent and removes it from view)

Rewards:
- Correct fraud flag: +0.95
- False positive (red herring): +0.05
- Correct clear: +0.70
- Step penalty: -0.02
- Query: +0.10

Goal: Flag all 5 frauds. Fraud indicators: negative amounts or future dates.

Respond with exactly one action command.
"""

def log_start(task: str, env: str, model: str):
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: str = None):
    error_str = f" error={error}" if error else ""
    print(f"[STEP] step={step} action={action!r} reward={reward:+.2f} done={done}{error_str}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: list):
    print(f"[END] success={success} steps={steps} score={score:.3f} rewards={rewards}", flush=True)

def get_model_message(client: OpenAI, step: int, echoed_message: str, last_reward: float, history: list) -> str:
    transactions_text = "\n".join([f"ID {t['id']}: Amount {t['amount']:.2f}, Date {t['date']}, Desc {t['description']}, Verified {t['verified']}, Info {t['extra_info']}" for t in echoed_message.get('transactions', [])]) if isinstance(echoed_message, dict) else "No transactions"

    history_text = "\n".join(history[-5:])  # last 5

    user_prompt = f"""
Current step: {step}
Last reward: {last_reward:+.2f}
History:
{history_text}

Current transactions:
{transactions_text}

Your action:
"""

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
        text = (completion.choices[0].message.content or "").strip()
        return text if text else "query amount > 5000"
    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}", flush=True)
        return "query amount > 5000"

async def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    env = AuditGymEnv(**config)

    history: List[str] = []
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)

    try:
        result = await env.reset()
        last_echoed = result.observation.dict()  # or something
        last_reward = 0.0

        for step in range(1, MAX_STEPS + 1):
            if result.done:
                break

            message = get_model_message(client, step, last_echoed, last_reward, history)

            result = await env.step(Action(message=message))
            obs = result.observation

            reward = result.reward or 0.0
            done = result.done
            error = None

            rewards.append(reward)
            steps_taken = step
            last_echoed = obs.dict()
            last_reward = reward

            log_step(step=step, action=message, reward=reward, done=done, error=error)

            history.append(f"Step {step}: {message!r} -> reward {reward:+.2f}")

            if done:
                break

        score = sum(rewards) / MAX_TOTAL_REWARD if MAX_TOTAL_REWARD > 0 else 0.0
        score = min(max(score, 0.0), 1.0)
        success = score >= SUCCESS_SCORE_THRESHOLD

    finally:
        try:
            await env.close()
        except Exception as e:
            print(f"[DEBUG] env.close() error: {e}", flush=True)
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

if __name__ == "__main__":
    asyncio.run(main())