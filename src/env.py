import asyncio
import re
from typing import List, Dict, Any
from .models import Transaction, Action, Observation, ResetResponse, StepResponse, generate_transactions

class AuditGymEnv:
    def __init__(self, num_total=1000, num_fraud=5, num_red_herring=50, max_steps=1000):
        self.num_total = num_total
        self.num_fraud = num_fraud
        self.num_red_herring = num_red_herring
        self.max_steps = max_steps

    async def reset(self) -> ResetResponse:
        self.transactions = generate_transactions(self.num_total, self.num_fraud, self.num_red_herring)
        self.current_view = self.transactions[:]
        self.step_count = 0
        self.flagged_frauds = set()
        self.flagged_red_herrings = set()
        self.flagged_clears = set()
        self.last_message = ""
        obs = self._get_obs()
        return ResetResponse(observation=obs)

    async def step(self, action: Action) -> StepResponse:
        self.step_count += 1
        reward = -0.02  # step penalty

        message = action.message.lower().strip()
        self.last_message = action.message
        done = False

        if "query" in message:
            # Parse query, e.g., "query amount > 5000"
            match = re.search(r'query\s+(\w+)\s*([<>=]+)\s*(\d+(?:\.\d+)?)', message)
            if match:
                field, op, value = match.groups()
                value = float(value)
                if field == "amount":
                    if op == ">":
                        self.current_view = [t for t in self.current_view if t.amount > value]
                    elif op == "<":
                        self.current_view = [t for t in self.current_view if t.amount < value]
                    reward += 0.10
        elif "verify" in message:
            # Parse verify, e.g., "verify id 0"
            match = re.search(r'verify\s+id\s+(\d+)', message)
            if match:
                id_val = int(match.group(1))
                if 0 <= id_val < len(self.transactions) and any(t.id == id_val for t in self.current_view):
                    t = next(t for t in self.current_view if t.id == id_val)
                    t.verified = True
                    if t.is_fraud:
                        t.extra_info = "Cross-reference: Anomalous activity detected"
                    elif t.is_red_herring:
                        t.extra_info = "Cross-reference: Large but legitimate transaction"
                    else:
                        t.extra_info = "Cross-reference: Standard transaction"
        elif "flag" in message:
            # Parse flag, e.g., "flag id 0"
            match = re.search(r'flag\s+id\s+(\d+)', message)
            if match:
                id_val = int(match.group(1))
                if 0 <= id_val < len(self.transactions) and any(t.id == id_val for t in self.current_view):
                    t = next(t for t in self.current_view if t.id == id_val)
                    self.current_view = [tx for tx in self.current_view if tx.id != id_val]
                    if t.is_fraud:
                        reward += 0.95
                        self.flagged_frauds.add(id_val)
                    elif t.is_red_herring:
                        reward += 0.05
                        self.flagged_red_herrings.add(id_val)
                    else:
                        reward += 0.70
                        self.flagged_clears.add(id_val)

        if len(self.flagged_frauds) == self.num_fraud:
            done = True

        if self.step_count >= self.max_steps:
            done = True

        obs = self._get_obs()
        return StepResponse(observation=obs, reward=reward, done=done)

    async def state(self) -> Dict[str, Any]:
        return {
            "flagged_frauds": len(self.flagged_frauds),
            "flagged_red_herrings": len(self.flagged_red_herrings),
            "flagged_clears": len(self.flagged_clears),
            "step_count": self.step_count,
            "done": len(self.flagged_frauds) == self.num_fraud or self.step_count >= self.max_steps
        }

    def _get_obs(self) -> Observation:
        transactions = [t.dict() for t in self.current_view]
        return Observation(transactions=transactions, step_count=self.step_count, echoed_message=self.last_message)

    @classmethod
    async def from_docker_image(cls, image_name: str):
        # For simplicity, just instantiate
        return cls()

    async def close(self):
        pass