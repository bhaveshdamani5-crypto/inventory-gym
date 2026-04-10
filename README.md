---
title: InventoryGym
emoji: 📦
colorFrom: indigo
colorTo: purple
sdk: docker
---

# InventoryGym-v1: Supply Chain Intelligence

### 🚀 Quick Links
- **GitHub**: [inventory-gym](https://github.com/bhaveshdamani5-crypto/inventory-gym)
- **API Status**: This Space serves the OpenEnv REST API on port 7860.
- **Grader**: Deterministic Supply Chain Grader (Cost vs Service Level).

### 📋 OpenEnv Compliance
- ✅ Async API: `reset()`, `step()`, `state()`
- ✅ Score Clamping: (0.01 - 0.99)
- ✅ Baseline: Compliant `inference.py`

### 🏗️ Getting Started
```bash
# Run locally
uvicorn app:app --port 7860
```
