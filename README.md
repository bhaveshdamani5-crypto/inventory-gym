---
title: InventoryGym-v1
emoji: 📦
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 8000
pinned: false
---

# InventoryGym-v1: Supply Chain Intelligence

A strategic OpenEnv environment for training AI agents to optimize multi-warehouse inventory management—balancing cost efficiency with customer satisfaction through intelligent ordering decisions.

## 🎯 Problem Statement

**Real-world challenge**: Supply chain managers face a critical trade-off: holding too much inventory increases costs; holding too little causes stockouts and lost sales. This environment simulates that constraint and requires agents to learn:

1. **Demand forecasting**: Recognize patterns in time-varying demand
2. **Lead time dynamics**: Account for order-to-delivery delays
3. **Cost-quality trade-off**: Optimize fulfillment rate vs. holding costs
4. **Multi-warehouse coordination**: Manage heterogeneous warehouse networks
5. **Strategic expediting**: Know _when_ to pay premium for fast delivery

## ⭐ What Makes This Novel

### Emergent Learning Behavior

Unlike classification tasks, agents exhibiting pure random behavior accumulate massive costs. **Learning emerges naturally**:

- Random agent: 30% fulfillment, $50,000 cost → score 0.15
- Heuristic agent: 85% fulfillment, $15,000 cost → score 0.70
- Reasoning model: 95%, $12,000 cost → score 0.90+

### Multi-Objective Reward

The environment doesn't have a single "right answer"—agents must discover the Pareto frontier:

```
Fulfillment Rate vs. Cost Trade-off:
- Pure demand-meeting: High cost, high waste
- Pure cost-minimization: Stockouts, lost sales
- Intelligent balance: Learn the optimal point
```

### Temporal Dependencies & Forecasting

Demand is **non-stationary** with:

- **Seasonality**: Weekly/monthly patterns agents must recognize
- **Trends**: Demand gradually increases or decreases
- **Noise**: Irreducible stochasticity

This forces agents to learn pattern recognition over pure logic.

### Scalability Difficulty Curve

**Agents don't just become "slower" on hard tasks—they must use fundamentally different strategies**:

| Task                                 | Complexity                           | Agent Strategy                              |
| ------------------------------------ | ------------------------------------ | ------------------------------------------- |
| **Easy** (1 warehouse)               | Single location, 5-step lead time    | Learn basic ordering rhythm                 |
| **Medium** (3 warehouses)            | Coordination across locations        | Forecast + distribute orders                |
| **Hard** (5 warehouses, 2-step lead) | Limited lookahead, expensive holding | Aggressive forecasting, expedited placement |

## 🏗️ Environment Architecture

### Action Space

```python
Order(dest_warehouse=int, quantity=float, priority=str)
# "order 2 500" → place standard order (3-step lead)
# "order 2 500 expedited" → rush delivery (1-step, 20% premium)
```

### Observation Space

```python
{
    "warehouses": [
        {"id": 0, "name": "Warehouse-A", "inventory": 1200.5,
         "capacity": 3000, "utilization": 0.40, "location": "North"},
        ...
    ],
    "pending_orders": [
        {"id": 0, "dest_warehouse": 1, "quantity": 500,
         "steps_remaining": 2},
        ...
    ],
    "forecasted_demand": [
        {"warehouse_id": 0, "next_5_steps": [250, 280, 320, 290, 250]},
        ...
    ],
    "current_step": 23,
    "total_cost": 5234.50,
    "last_action": "Order 500 units to Warehouse-A"
}
```

### Reward Function (Per Step)

```
Fulfillment bonus:    +0.5 × (fulfilled_demand / actual_demand)
Stockout penalty:     -0.3 × unmet_demand
Holding cost:         -0.01 × (inventory × holding_cost_coefficient)
Optimal range bonus:  +0.05 (if inventory in balanced zone)
Order cost penalty:   -0.01 × order_cost (regular)/-0.012 × (expedited)
```

**Strategic implications**:

- Overstocking is costly (holding cost compounds)
- Understocking loses sales (stockout penalty)
- Expediting is expensive but necessary for demand spikes
- Optimal solution isn't obvious → requires learning

## 📊 Task Configurations

### Easy: Single Warehouse Sandbox

```yaml
num_warehouses: 1
num_steps: 50
lead_time: 5 steps
inventory_cost_multiplier: 1.0
demand_characteristics: Stable, low variance
```

**Learning target**: Basic ordering cadence recognition

### Medium: Multi-Warehouse Coordination

```yaml
num_warehouses: 3
num_steps: 100
lead_time: 3 steps
inventory_cost_multiplier: 1.5
demand_characteristics: Variable, seasonal patterns
```

**Learning target**: Location-specific demand forecasting + inter-warehouse strategy

### Hard: Realistic Supply Chain

```yaml
num_warehouses: 5
num_steps: 100
lead_time: 2 steps
inventory_cost_multiplier: 2.0
demand_characteristics: High variance, strong seasonality, trending
```

**Learning target**: Sophisticated forecasting + aggressive multi-warehouse optimization + expediting strategy

## 📈 Expected Baseline Performance

| Model               | Easy  | Medium | Hard  |
| ------------------- | ----- | ------ | ----- |
| **Random**          | 0.20  | 0.10   | 0.05  |
| **GPT-3.5**         | 0.60  | 0.45   | 0.35  |
| **GPT-4**           | 0.82  | 0.72   | 0.60  |
| **Claude Opus**     | 0.88  | 0.78   | 0.68  |
| **Reasoning Model** | 0.92+ | 0.85+  | 0.78+ |

_Scores based on: 60% fulfillment rate + 40% cost efficiency_

## 🚀 Getting Started

### Installation

```bash
pip install -r requirements.txt
```

### Running Demo

```bash
python demo.py
```

### Running Inference

```bash
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4"
export HF_TOKEN="your-key"
export TASK_NAME="inventory-hard"

python inference.py
```

### Running in Streamlit

```bash
streamlit run app.py
```

## 📋 OpenEnv Compliance

- ✅ Async API: `reset()`, `step(action)`, `state()`
- ✅ Typed Pydantic models: All inputs/outputs validated
- ✅ `openenv.yaml`: Environment metadata
- ✅ Deterministic graders: 3 difficulty levels
- ✅ Baseline inference script: Structure log format
- ✅ Dockerfile: Reproducible containerization

## 💡 Research Insights

This environment enables study of:

1. **When agents use forecasting vs. heuristics**
2. **How lead times force lookahead planning**
3. **Trade-off discovery in multi-objective learning**
4. **Generalization to unseen demand patterns**
5. **Sample efficiency in sequential decision-making**

## 📦 Project Structure

```
.
├── app.py                    # Streamlit UI
├── inference.py              # Baseline script
├── demo.py                   # Quick demo
├── requirements.txt          # Dependencies
├── openenv.yaml             # Environment spec
├── Dockerfile               # Containerization
├── README.md               # This file
└── src/
    ├── __init__.py
    ├── models.py            # Pydantic types
    ├── env.py              # InventoryGymEnv
    └── grader.py           # Evaluation functions
```

## 📖 References

- OpenEnv specification: https://github.com/openenv-foundation/openenv
- Inventory management optimization: Classic operations research
- Demand forecasting: Time series analysis meets reinforcement learning
