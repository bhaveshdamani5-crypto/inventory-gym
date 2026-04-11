"""
Grader functions for evaluating agent performance on InventoryGym tasks.
Evaluates the trade-off between Supply Chain Stability (Service Level) and Cost Efficiency.

Phase 2 Compliance:
- All graders have default state=None parameter for reflection testing
- Returns float scores between 0.0 and 1.0 (clamped to [0.01, 0.99])
- Compatible with parameterless validation checks
"""

def grade_easy(trajectory=None):
    """
    Easy: 1 Warehouse. Baseline for learning basic replenishment.
    Requires >92% Service Level and stable costs.
    """
    trajectory = trajectory or {}
    return _compute_composite_score(
        trajectory,
        target_sl=0.92,
        cost_budget=15000.0,
        sl_weight=0.7
    )

def grade_medium(trajectory=None):
    """
    Medium: 3 Warehouses. Coordination and basic forecasting needed.
    Requires >88% Service Level across network.
    """
    trajectory = trajectory or {}
    return _compute_composite_score(
        trajectory,
        target_sl=0.88,
        cost_budget=40000.0,
        sl_weight=0.6
    )

def grade_hard(trajectory=None):
    """
    Hard: 5 Warehouses + Volatile Demand. Advanced optimization required.
    Requires resilient strategy against demand shocks.
    """
    trajectory = trajectory or {}
    return _compute_composite_score(
        trajectory,
        target_sl=0.85,
        cost_budget=80000.0,
        sl_weight=0.5 # Cost efficiency becomes more critical here
    )

def _compute_composite_score(trajectory, target_sl, cost_budget, sl_weight):
    """
    Compute 0.0-1.0 score based on Service Level and Cost Efficiency.
    """
    actual_sl = trajectory.get('service_level', 0.0)
    total_cost = trajectory.get('total_cost', 1e9)
    
    # 1. Service Level Score (Exponential decay below target)
    if actual_sl >= target_sl:
        sl_score = 1.0
    else:
        # Heavily penalize failing to meet service level targets
        sl_score = (actual_sl / target_sl) ** 2
    
    # 2. Cost Efficiency Score
    # Linear scaling: 1.0 if at budget, higher if under, lower if over
    # But we cap it to reward significant savings
    cost_ratio = cost_budget / max(total_cost, 1.0)
    cost_score = min(1.2, cost_ratio) # Bonus score for extreme efficiency
    # Normalize to 0-1
    cost_score = max(0.0, min(1.0, cost_score))
    
    # 3. Composite with weighted average
    final_score = (sl_weight * sl_score) + ((1 - sl_weight) * cost_score)
    
    # Penalty for early termination (if applicable) or extreme failure
    if actual_sl < 0.3:
        final_score *= 0.5
        
    # CLAMP: Ensure score is strictly between 0.01 and 0.99 per hackathon rules
    # This ensures :.2f rounding never results in 0.00 or 1.00
    return max(0.01, min(0.99, float(final_score)))