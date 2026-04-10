---
title: AuditGym-v1
emoji: 🔍
colorFrom: indigo
colorTo: purple
sdk: streamlit
sdk_version: "1.28.0"
python_version: "3.11"
app_file: app.py
pinned: false
---

# AuditGym-v1

A real-world OpenEnv environment simulating forensic audit of transaction datasets to detect synthetic fraud.

## Project Structure

```
your-repo/
├── app.py                 # Hugging Face Space entrypoint (Streamlit)
├── requirements.txt       # Dependencies
├── README.md             # This file
├── demo.py               # Sample episode demo
├── inference.py          # Baseline inference script
├── openenv.yaml          # OpenEnv configuration
├── Dockerfile            # Container setup
├── src/
│   ├── __init__.py
│   ├── env.py            # OpenEnv environment implementation
│   ├── models.py         # Pydantic models
│   └── grader.py         # Evaluation/grading logic
└── assets/               # Static assets (if any)
```

## Description

AuditGym-v1 presents an AI agent with a dataset of financial transactions containing hidden fraudulent activities. The agent must use query, verify, and flag actions to identify all fraudulent transactions while minimizing false positives.

### Key Features

- **Real-world task**: Forensic fraud detection in financial data
- **Progressive difficulty**: Easy (100 transactions), Medium (500), Hard (1000)
- **Meaningful rewards**: High precision for correct fraud detection, penalties for errors
- **Partial progress signals**: Rewards for each correct action

## Action Space

Actions are natural language commands:

- `query amount > 5000` - Filter transactions by criteria
- `verify id 123` - Get cross-reference information
- `flag id 123` - Mark transaction as fraudulent

## Observation Space

Returns current filtered transaction list with:

- id, amount, date, description
- verified status and extra info (after verification)

## Tasks

1. **Easy**: 100 transactions, 1 fraud, 5 red herrings
2. **Medium**: 500 transactions, 3 frauds, 25 red herrings
3. **Hard**: 1000 transactions, 5 frauds, 50 red herrings

## Setup

### Prerequisites

- Python 3.11+
- Docker
- OpenAI API access

### Installation

```bash
pip install -r requirements.txt
```

### Environment Variables

Set the following before running:

- `API_BASE_URL`: LLM API endpoint (default: https://api.openai.com/v1)
- `MODEL_NAME`: Model identifier (default: gpt-4)
- `HF_TOKEN`: API key
- `TASK_NAME`: Task variant (audit-easy, audit-medium, audit-hard)

### Running Locally

```bash
# Run demo
python demo.py

# Run inference
python inference.py
```

### Docker

```bash
docker build -t auditgym .
docker run -e API_BASE_URL=... -e MODEL_NAME=... -e HF_TOKEN=... -e TASK_NAME=audit-easy auditgym
```

## Baseline Scores

Baseline inference using GPT-4 on standard task configurations:

| Task | Score | Steps | Correct Frauds | False Positives |
|------|-------|-------|----------------|-----------------|
| Easy (1 fraud) | 0.95-1.00 | 3-8 | 1/1 | 0-1 |
| Medium (3 frauds) | 0.75-0.90 | 10-20 | 2-3/3 | 1-3 |
| Hard (5 frauds) | 0.60-0.85 | 15-30 | 3-5/5 | 2-5 |

**Scoring Formula**: `score = sum(rewards) / max_possible_reward`, normalized to [0.0, 1.0]

**Reward Breakdown**:
- Correct fraud detection: +0.95
- Correct clear (non-fraud): +0.70
- Query action: +0.10
- False positive: +0.05
- Step penalty: -0.02

## Submission

This project is structured for OpenEnv Hackathon submission with:

- OpenEnv-compliant async environment
- Structured logging in inference script
- Deterministic graders for evaluation
- HF Space-ready app.py
- Complete documentation

Deploy to Hugging Face Spaces for the `/reset` endpoint validation.
