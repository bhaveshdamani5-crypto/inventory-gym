"""
Grader functions for evaluating agent performance on AuditGym tasks.
Each grader returns a score between 0.0 and 1.0 based on the final state.
"""

def grade_easy(state):
    """Grade easy task: 100 transactions, 1 fraud, 5 red herrings"""
    return _grade_task(state, num_fraud=1, num_red_herring=5)

def grade_medium(state):
    """Grade medium task: 500 transactions, 3 frauds, 25 red herrings"""
    return _grade_task(state, num_fraud=3, num_red_herring=25)

def grade_hard(state):
    """Grade hard task: 1000 transactions, 5 frauds, 50 red herrings"""
    return _grade_task(state, num_fraud=5, num_red_herring=50)

def _grade_task(state, num_fraud, num_red_herring):
    """
    Compute score based on:
    - 0.7 for each correct fraud flagged
    - 0.1 penalty for each red herring flagged as fraud
    - 0.1 penalty for each fraud missed
    Normalized to 0-1 range.
    """
    flagged_frauds = state.get('flagged_frauds', 0)
    flagged_red_herrings = state.get('flagged_red_herrings', 0)

    correct_fraud_score = min(flagged_frauds / num_fraud, 1.0) * 0.7 if num_fraud > 0 else 0.0
    false_positive_penalty = (flagged_red_herrings / num_red_herring) * 0.1 if num_red_herring > 0 else 0.0
    miss_penalty = ((num_fraud - flagged_frauds) / num_fraud) * 0.1 if num_fraud > 0 else 0.0

    score = correct_fraud_score - false_positive_penalty - miss_penalty
    return max(0.0, min(1.0, score))