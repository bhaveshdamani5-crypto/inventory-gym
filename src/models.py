from pydantic import BaseModel
from typing import List, Dict, Any
import random
from datetime import datetime, timedelta

class Transaction(BaseModel):
    id: int
    amount: float
    date: str
    description: str
    is_fraud: bool = False
    is_red_herring: bool = False
    verified: bool = False
    extra_info: str = ""

class Action(BaseModel):
    message: str

class Observation(BaseModel):
    transactions: List[Dict[str, Any]]
    step_count: int
    echoed_message: str = ""

class ResetResponse(BaseModel):
    observation: Observation

class StepResponse(BaseModel):
    observation: Observation
    reward: float
    done: bool

def generate_transactions(num_total=1000, num_fraud=5, num_red_herring=50):
    transactions = []
    fraud_ids = set(random.sample(range(num_total), num_fraud))
    red_herring_ids = set(random.sample([i for i in range(num_total) if i not in fraud_ids], num_red_herring))

    for i in range(num_total):
        amount = random.uniform(10, 10000)
        date = (datetime.now() - timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d')
        description = f"Transaction {i}"

        is_fraud = i in fraud_ids
        is_red_herring = i in red_herring_ids

        if is_fraud:
            # Synthetic fraud: logical errors
            if random.choice([True, False]):
                amount = -amount  # Negative amount
                description += " (Refund?)"
            else:
                date = (datetime.now() + timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d')  # Future date
                description += " (Future dated)"
        elif is_red_herring:
            # Suspicious but legal
            amount = random.uniform(5000, 10000)  # Large amount
            description += " (Large transfer)"

        transactions.append(Transaction(id=i, amount=amount, date=date, description=description, is_fraud=is_fraud, is_red_herring=is_red_herring))

    return transactions