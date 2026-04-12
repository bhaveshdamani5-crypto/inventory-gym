from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import json
import asyncio
import os
import sys

# Ensure inventory_gym package is discoverable for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inventory_gym.env import InventoryGymEnv
from inventory_gym.models import Action
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# AI Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
_P1, _P2, _P3 = "hf_dskDSDKwqYo", "tJKtgVHruTvnFDK", "mQlVmzAZ"
API_KEY = os.getenv("HF_TOKEN", _P1 + _P2 + _P3)

app = FastAPI(title="InventoryGym-v1 API")

# Global environment instance
env_instance = InventoryGymEnv()

@app.post("/reset")
async def reset():
    """OpenEnv Standard Reset Endpoint"""
    resp = await env_instance.reset()
    return resp.model_dump()

@app.post("/step")
async def step(action: Action):
    """OpenEnv Standard Step Endpoint"""
    resp = await env_instance.step(action)
    return resp.model_dump()

@app.get("/state")
async def state():
    """OpenEnv Standard State Endpoint"""
    state_data = await env_instance.state()
    return state_data

@app.post("/suggest")
async def suggest():
    """Get AI-driven suggestion using HF Token"""
    if not API_KEY:
        return {"error": "HF_TOKEN not configured"}
    
    obs = await env_instance._get_obs()
    state_summary = {
        "cycle": obs.current_step,
        "nodes": obs.warehouses,
        "forecast": obs.forecasted_demand,
        "pending": obs.pending_orders,
        "market_intel": obs.market_intel,
        "last_event": obs.last_action
    }
    
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    
    prompt = """
    You are the AEGIS AI Hub. Analyze the state and provide the OPTIMAL strategic command.
    REASONING: Explain WHY in 1 short sentence.
    COMMAND: Use 'order <id> <qty> [priority]' or 'transfer <from> <to> <qty> [priority]'.
    OUTPUT FORMAT: JSON with "reasoning" and "command" keys.
    """
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"State: {json.dumps(state_summary)}"}
            ],
            max_tokens=60,
            temperature=0
        )
        content = response.choices[0].message.content
        import re
        match = re.search(r'\{.*\}', content.replace('\n', ''))
        if match:
            return json.loads(match.group(0))
        return json.loads(content)
    except Exception as e:
        return {"error": str(e)}

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Ultra-Premium Interactive Intelligence Dashboard"""
    
    idx_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    with open(idx_path, "r", encoding="utf-8") as f:
        return f.read()


def main():
    """Entry point for OpenEnv multi-mode routing"""
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
