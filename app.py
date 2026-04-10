from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import json
import asyncio

# Import our environment
from src.env import InventoryGymEnv
from src.models import Action

app = FastAPI(title="InventoryGym-v1 API")

# Global environment instance (for demo/validation purposes)
# In a real multi-user scenario, we'd use session IDs
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

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Premium Interactive Dashboard for Judges"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>InventoryGym-v1 Dashboard</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            body { font-family: 'Outfit', sans-serif; background: #020617; color: #f8fafc; }
            .glass { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1); }
            .gradient-text { background: linear-gradient(90deg, #38bdf8 0%, #818cf8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        </style>
    </head>
    <body class="p-8">
        <div class="max-w-7xl mx-auto">
            <header class="mb-12 flex justify-between items-center">
                <div>
                    <h1 class="text-5xl font-extrabold gradient-text mb-2">InventoryGym-v1</h1>
                    <p class="text-slate-400 text-lg">OpenEnv Supply Chain Intelligence Benchmark</p>
                </div>
                <div class="text-right">
                    <span class="px-4 py-2 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 font-bold">Round 2 Ready</span>
                </div>
            </header>

            <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12" id="kpis">
                <div class="glass p-6 rounded-2xl">
                    <p class="text-slate-400 text-xs uppercase tracking-widest font-bold mb-1">Service Level</p>
                    <h2 class="text-3xl font-bold" id="kpi-sl">--%</h2>
                </div>
                <div class="glass p-6 rounded-2xl">
                    <p class="text-slate-400 text-xs uppercase tracking-widest font-bold mb-1">Total Cost</p>
                    <h2 class="text-3xl font-bold" id="kpi-cost">$0</h2>
                </div>
                <div class="glass p-6 rounded-2xl">
                    <p class="text-slate-400 text-xs uppercase tracking-widest font-bold mb-1">Active Nodes</p>
                    <h2 class="text-3xl font-bold" id="kpi-nodes">--</h2>
                </div>
                <div class="glass p-6 rounded-2xl">
                    <p class="text-slate-400 text-xs uppercase tracking-widest font-bold mb-1">Current Step</p>
                    <h2 class="text-3xl font-bold" id="kpi-step">0/100</h2>
                </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div class="lg:col-span-2 glass p-8 rounded-3xl">
                    <div id="chart-main" class="w-full" style="height: 450px;"></div>
                </div>
                <div class="glass p-8 rounded-3xl">
                    <h3 class="text-xl font-bold mb-6">Interactive Sandbox</h3>
                    <div class="space-y-6">
                        <div>
                            <label class="block text-sm font-medium text-slate-400 mb-2">Warehouse Node</label>
                            <select id="node-sel" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-blue-500 outline-none">
                                <option value="0">Node A (North)</option>
                                <option value="1">Node B (South)</option>
                                <option value="2">Node C (Central)</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-slate-400 mb-2">Replenishment Quantity</label>
                            <input type="number" id="qty-val" value="200" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white outline-none">
                        </div>
                        <button onclick="runStep()" class="w-full py-4 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl font-bold text-lg hover:from-blue-500 hover:to-indigo-500 transition-all shadow-lg shadow-blue-500/20">Execute Strategy</button>
                        <button onclick="resetEnv()" class="w-full py-2 text-slate-500 hover:text-white transition-colors">Reset Episode</button>
                    </div>
                </div>
            </div>
        </div>

        <script>
            async function resetEnv() {
                const res = await fetch('/reset', { method: 'POST' });
                const data = await res.json();
                updateUI(data.observation);
            }

            async function runStep() {
                const action = {
                    dest_warehouse: parseInt(document.getElementById('node-sel').value),
                    quantity: parseFloat(document.getElementById('qty-val').value),
                    priority: 'normal'
                };
                const res = await fetch('/step', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(action)
                });
                const data = await res.json();
                updateUI(data.observation);
            }

            function updateUI(obs) {
                document.getElementById('kpi-sl').innerText = (obs.service_level * 100).toFixed(1) + '%';
                document.getElementById('kpi-cost').innerText = '$' + obs.total_cost.toLocaleString();
                document.getElementById('kpi-nodes').innerText = obs.warehouses.length;
                document.getElementById('kpi-step').innerText = obs.current_step + '/100';

                const x = obs.warehouses.map(w => w.name);
                const y = obs.warehouses.map(w => w.inventory);
                const colors = obs.warehouses.map(w => w.utilization > 0.8 ? '#ef4444' : '#38bdf8');

                Plotly.newPlot('chart-main', [{
                    x: x, y: y, type: 'bar',
                    marker: { color: colors },
                    text: y.map(v => v.toFixed(0) + ' units'), textposition: 'auto',
                }], {
                    title: { text: 'Real-time Node Inventory', font: { color: '#f8fafc' } },
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    font: { color: '#94a3b8' },
                    yaxis: { range: [0, 4000], gridcolor: '#1e293b' },
                    xaxis: { gridcolor: '#1e293b' }
                });
            }

            resetEnv();
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
