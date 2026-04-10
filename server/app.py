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

# Ensure src namespace is discoverable from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inventory_gym.env import InventoryGymEnv
from inventory_gym.models import Action
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# AI Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
API_KEY = os.getenv("HF_TOKEN")

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
    return r"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>InventoryGym-v1 | Supply Intelligence Elite</title>
        
        <!-- UI Libraries -->
        <script src="https://cdn.jsdelivr.net/npm/plotly.js-dist@2.27.0/plotly.min.js"></script>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
        <script src="https://unpkg.com/lucide@latest"></script>
        <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
        
        <style>
            :root {
                --primary: #3b82f6; --primary-light: #60a5fa; --primary-glow: rgba(59, 130, 246, 0.4);
                --accent: #f43f5e; --success: #10b981; --warning: #f59e0b;
                --bg: #020617; --card-bg: rgba(7, 13, 31, 0.7); --border: rgba(255, 255, 255, 0.05);
            }
            body { 
                font-family: 'Outfit', sans-serif; background: var(--bg); color: #f1f5f9; overflow-x: hidden;
                background: radial-gradient(circle at 50% 50%, #0c122b 0%, #020617 100%);
            }
            body::before {
                content: ""; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
                z-index: 100; pointer-events: none; background-size: 100% 2px, 3px 100%;
            }
            h1, h2, h3, .font-heading { font-family: 'Space Grotesk', sans-serif; letter-spacing: -0.02em; }
            .glass-panel { 
                background: var(--card-bg); backdrop-filter: blur(24px); border: 1px solid var(--border); 
                box-shadow: 0 4px 24px -1px rgba(0, 0, 0, 0.2); transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); 
            }
            .glass-panel:hover { border-color: rgba(59, 130, 246, 0.2); box-shadow: 0 0 40px -10px rgba(59, 130, 246, 0.15); }
            .cyber-btn {
                position: relative; background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
                border: 1px solid rgba(255,255,255,0.05); transition: all 0.3s ease; overflow: hidden;
            }
            .cyber-btn:hover { background: #1e293b; border-color: var(--primary); transform: translateY(-2px); box-shadow: 0 10px 20px -10px var(--primary-glow); }
            .cyber-btn::after {
                content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
                background: linear-gradient(transparent, rgba(255,255,255,0.05), transparent); transform: rotate(45deg);
                transition: 0.5s; pointer-events: none;
            }
            .cyber-btn:hover::after { left: 100%; }
            .pulse-online { width: 10px; height: 10px; background: var(--success); border-radius: 50%; box-shadow: 0 0 15px var(--success); animation: pulse 2s infinite; }
            @keyframes pulse { 0% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.6); opacity: 0.4; } 100% { transform: scale(1); opacity: 1; } }
            .custom-scrollbar::-webkit-scrollbar { width: 4px; }
            .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
            .node-link { stroke-dasharray: 10; animation: flow 15s linear infinite; opacity: 0.3; }
            @keyframes flow { from { stroke-dashoffset: 200; } to { stroke-dashoffset: 0; } }
            #shock-banner { 
                position: fixed; top: 0; left: 0; width: 100%; z-index: 1000; display: none; 
                background: linear-gradient(90deg, #f43f5e, #be123c, #f43f5e); background-size: 200% auto;
                color: white; text-align: center; padding: 12px; font-weight: 800; letter-spacing: 4px; 
                text-transform: uppercase; animation: banner-slide 2s linear infinite; box-shadow: 0 4px 30px rgba(244, 63, 94, 0.4);
            }
            @keyframes banner-slide { 0% { background-position: 0% center; } 100% { background-position: 200% center; } }
            .gradient-text { background: linear-gradient(to right, #fff, #94a3b8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            .ai-news-item { border-left: 2px solid var(--primary); background: linear-gradient(90deg, rgba(59, 130, 246, 0.05), transparent); }
            
            /* Tactical UI Overhaul */
            .tactical-grid {
                background-size: 50px 50px;
                background-image: linear-gradient(to right, rgba(59, 130, 246, 0.05) 1px, transparent 1px), linear-gradient(to bottom, rgba(59, 130, 246, 0.05) 1px, transparent 1px);
            }
            .radar-bg { background: radial-gradient(circle at center, rgba(59, 130, 246, 0.15) 0%, transparent 60%); }
            .pulse-ring { border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 50%; position: absolute; animation: ring-pulse 4s cubic-bezier(0.1, 0.5, 0.9, 1) infinite; }
            @keyframes ring-pulse { 0% { transform: scale(0.1); opacity: 1; border-width: 3px; } 100% { transform: scale(3.5); opacity: 0; border-width: 1px; } }
            .hologram-map { filter: invert(1) opacity(0.2) drop-shadow(0 0 20px rgba(59,130,246,0.8)); mix-blend-screen: screen; }
        </style>
    </head>
    <body class="min-h-screen flex flex-col">
        <div id="shock-banner">SYSTEMIC SHOCK DETECTED - LOGISTICS CALIBRATION REQUIRED</div>
        <div class="fixed inset-0 bg-black/40 z-[-1]"></div>
        
        <!-- Top Navigation -->
        <nav class="glass-panel border-b px-8 py-4 flex justify-between items-center sticky top-0 z-50">
            <div class="flex items-center gap-4">
                <div class="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/20">
                    <i data-lucide="activity" class="text-white w-6 h-6"></i>
                </div>
                <div>
                    <h1 class="text-xl font-bold tracking-tight text-white">InventoryGym <span class="text-blue-500 font-normal italic">Elite</span></h1>
                    <div class="flex items-center gap-2">
                        <div class="pulse-online"></div>
                        <span class="text-[10px] uppercase tracking-widest text-blue-400 font-bold">Strategic Nexus Active</span>
                    </div>
                </div>
            </div>
            
            <div class="hidden md:flex gap-10">
                <div class="text-center group" title="Environmental, Social, and Governance Score">
                    <p class="text-[9px] text-emerald-500 uppercase font-bold tracking-widest mb-1">ESG Sustainability</p>
                    <p id="top-esg" class="text-base font-bold text-emerald-400">0.99</p>
                </div>
                <div class="h-8 w-[1px] bg-slate-800"></div>
                <div class="text-center group" title="Official Hackathon Grade">
                    <p class="text-[9px] text-amber-500 uppercase font-bold tracking-widest mb-1">Inference Grade</p>
                    <p id="top-score" class="text-lg font-bold text-amber-400">0.01</p>
                </div>
                <div class="h-8 w-[1px] bg-slate-800"></div>
                <div class="text-center group">
                    <p class="text-[9px] text-slate-500 uppercase font-bold tracking-widest mb-1">Global Fulfillment</p>
                    <p id="top-sl" class="text-base font-bold text-blue-400">100.0%</p>
                </div>
                <div class="h-8 w-[1px] bg-slate-800"></div>
                <div class="text-center group">
                    <p class="text-[9px] text-rose-500 uppercase font-bold tracking-widest mb-1">Carbon Footprint (g/CO2)</p>
                    <p id="top-carbon" class="text-base font-bold text-rose-400">0</p>
                </div>
            </div>

            <div class="flex gap-4">
                <button onclick="resetEnv()" class="p-3 hover:bg-white/10 rounded-xl transition-all text-slate-400"><i data-lucide="rotate-ccw" class="w-5 h-5"></i></button>
                <div class="w-10 h-10 rounded-xl border border-white/10 bg-white/5 flex items-center justify-center overflow-hidden"><img src="https://api.dicebear.com/7.x/bottts-neutral/svg?seed=StrategyAlpha&backgroundColor=3b82f6" alt="AI Agent"></div>
            </div>
        </nav>

        <main class="flex-grow p-6 grid grid-cols-12 gap-6 max-w-[1800px] mx-auto w-full">
            <div class="col-span-12 xl:col-span-8 space-y-6">
                <div class="glass-panel rounded-3xl p-8 h-[450px] relative overflow-hidden group border border-blue-500/20 tactical-grid shadow-[inset_0_0_100px_rgba(0,0,0,0.8)] bg-[#020617]">
                    <div class="absolute inset-0 radar-bg pointer-events-none"></div>
                    
                    <!-- Radar Pulsing Rings -->
                    <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
                        <div class="w-[200px] h-[200px] pulse-ring" style="animation-delay: 0s"></div>
                        <div class="w-[200px] h-[200px] pulse-ring" style="animation-delay: 1.33s"></div>
                        <div class="w-[200px] h-[200px] pulse-ring" style="animation-delay: 2.66s"></div>
                    </div>

                    <div class="absolute inset-0 flex items-center justify-center p-12 mt-12 pointer-events-none hologram-map">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/e/ec/World_map_blank_without_borders.svg" class="w-full h-full object-contain opacity-30">
                    </div>
                    <div class="absolute inset-0 flex items-center justify-center p-12 mt-12">
                        <svg viewBox="0 0 800 400" id="network-svg" class="w-full h-full drop-shadow-[0_0_10px_rgba(59,130,246,1)]">
                            <defs>
                                <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                                    <feGaussianBlur stdDeviation="4" result="blur"/>
                                    <feComposite in="SourceGraphic" in2="blur" operator="over"/>
                                </filter>
                            </defs>
                            <g transform="translate(400, 350)" filter="url(#glow)"><circle r="8" fill="#3b82f6" class="animate-pulse" /><circle r="16" fill="none" stroke="#3b82f6" stroke-width="2" class="pulse-online"/><text y="-18" text-anchor="middle" fill="#60a5fa" font-size="11" font-family="Space Grotesk" font-weight="bold" letter-spacing="2">GLOBAL SUPPLIER</text></g>
                            <g id="map-links"></g><g id="map-nodes"></g>
                        </svg>
                    </div>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6" id="warehouse-grid"></div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="glass-panel rounded-3xl p-6 relative overflow-hidden"><h3 class="text-xs font-bold text-slate-400 uppercase tracking-widest mb-6">Aggregate Demand Trend</h3><div id="demand-chart" style="height: 250px;"></div></div>
                    <div class="glass-panel rounded-3xl p-6 relative overflow-hidden"><h3 class="text-xs font-bold text-slate-400 uppercase tracking-widest mb-6">Inventory Stockpile Matrix</h3><div id="inventory-chart" style="height: 250px;"></div></div>
                </div>
            </div>
            <div class="col-span-12 xl:col-span-4 space-y-6 flex flex-col h-full">
                <div class="glass-panel rounded-3xl p-8 cyber-border border-white/10 shadow-blue-900/10">
                    <h3 class="text-xl font-bold mb-8 flex items-center gap-3 text-white"><i data-lucide="target" class="text-blue-400"></i> Decision Console</h3>
                    <div class="space-y-6">
                        <div class="grid grid-cols-2 gap-4">
                            <div class="space-y-2"><label class="text-[10px] font-bold text-slate-500 uppercase">Input Node</label><select id="action-origin" class="w-full bg-slate-900/50 border border-white/10 rounded-xl p-3 text-sm text-white outline-none"><option value="-1">Global Supplier</option></select></div>
                            <div class="space-y-2"><label class="text-[10px] font-bold text-slate-500 uppercase">Output Node</label><select id="action-dest" class="w-full bg-slate-900/50 border border-white/10 rounded-xl p-3 text-sm text-white outline-none"></select></div>
                        </div>
                        <div class="space-y-4"><label class="text-[10px] font-bold text-slate-500 uppercase flex justify-between">Volume Allocation <span id="qty-disp" class="text-blue-400 font-bold text-lg">500</span></label><input type="range" id="action-qty" min="0" max="2500" step="50" value="500" class="w-full accent-blue-500 cursor-pointer h-1.5 bg-slate-800 rounded-lg appearance-none" oninput="document.getElementById('qty-disp').innerText = this.value"></div>
                        <div class="grid grid-cols-2 gap-4">
                            <button onclick="runStep('normal')" class="cyber-btn py-4 rounded-2xl font-bold text-slate-400">Standard Plan</button>
                            <button onclick="runStep('expedited')" class="py-4 bg-gradient-to-br from-blue-600 to-indigo-700 hover:scale-[1.02] active:scale-[0.98] rounded-2xl font-bold transition-all shadow-xl shadow-blue-500/20 text-white">Rush Execute</button>
                        </div>
                        <button onclick="getAISuggestion()" class="w-full py-4 bg-blue-500/10 hover:bg-blue-500/15 border border-blue-500/20 group rounded-2xl font-bold transition-all text-blue-400 flex items-center justify-center gap-3">
                            <i data-lucide="brain-circuit" class="w-4 h-4 group-hover:rotate-12 transition-transform"></i> Query OpenEnv Model
                        </button>
                    </div>
                </div>
                <div id="market-news-container" class="glass-panel rounded-3xl p-6 border-blue-500/30 shadow-blue-500/5 hidden">
                    <div class="flex items-center justify-between mb-4 pb-2 border-b border-white/5">
                        <div class="flex items-center gap-3">
                            <i data-lucide="cpu" class="text-blue-400 w-4 h-4"></i>
                            <h4 class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Neural Intelligence Hub</h4>
                        </div>
                        <span class="text-[9px] text-blue-500 font-bold">QWEN-72B-GENAI</span>
                    </div>
                    <div id="market-news" class="space-y-4"></div>
                </div>
                <div class="glass-panel rounded-3xl p-8 flex-grow flex flex-col min-h-[400px] border-white/5 overflow-hidden">
                    <h3 class="text-xs font-bold text-slate-400 uppercase tracking-widest mb-6 flex items-center gap-3"><span class="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span> Neural Inference Stream</h3>
                    <div id="terminal" class="flex-grow overflow-y-auto custom-scrollbar space-y-4 pr-2"></div>
                    <div class="mt-8 pt-6 border-t border-white/5 flex justify-between items-center"><div class="flex items-center gap-3"><div class="w-32 h-1 bg-slate-800 rounded-full overflow-hidden"><div id="step-progress" class="h-full bg-blue-500 transition-all duration-700"></div></div><span class="text-xs font-mono font-bold text-slate-400" id="step-counter">00 / 100</span></div></div>
                </div>
            </div>
        </main>
        <script>
            let chartData = { step: [], demand: [], cost: [], sl: [] };
            async function resetEnv() {
                const res = await fetch('/reset', { method: 'POST' }); const data = await res.json();
                chartData = { step: [], demand: [], cost: [], sl: [] }; document.getElementById('terminal').innerHTML = '';
                log('Strategic session initiated.', 'info'); updateUI(data.observation);
            }
            async function runStep(priority) {
                const action = { dest_warehouse: parseInt(document.getElementById('action-dest').value), origin_warehouse: parseInt(document.getElementById('action-origin').value), quantity: parseFloat(document.getElementById('action-qty').value), priority: priority };
                const res = await fetch('/step', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(action) }); const data = await res.json();
                if (data.done) log('Simulation Objective Achieved.', 'success');
                else {
                    const r = data.reward;
                    if (r > 0.3) log(`Optimal Strategic Execute: +${r.toFixed(2)}`, 'success');
                    else if (r >= 0) log(`Steady Performance: +${r.toFixed(2)}`, 'info');
                    else log(`Operational Friction: ${r.toFixed(2)}`, 'warn');
                }
                updateUI(data.observation, data.reward);
            }
            async function getAISuggestion() {
                log('Querying HF Intelligence Hub...', 'info');
                const res = await fetch('/suggest', { method: 'POST' });
                const data = await res.json();
                if (data.error) log('Neural Hub Offline: ' + data.error, 'warn');
                else {
                    log('LLM STRATEGIC REASONING: ' + data.reasoning, 'success');
                    log('INFERRED COMMAND: ' + data.command, 'info');
                    // Autofill the form
                    const parts = data.command.split(' ');
                    if (parts[0] === 'order') {
                        document.getElementById('action-origin').value = '-1';
                        document.getElementById('action-dest').value = parts[1];
                        document.getElementById('action-qty').value = parts[2];
                        document.getElementById('qty-disp').innerText = parts[2];
                    } else if (parts[0] === 'transfer') {
                        document.getElementById('action-origin').value = parts[1];
                        document.getElementById('action-dest').value = parts[2];
                        document.getElementById('action-qty').value = parts[3];
                        document.getElementById('qty-disp').innerText = parts[3];
                    }
                }
            }
            function log(msg, type) {
                const terminal = document.getElementById('terminal'); const div = document.createElement('div'); div.className = 'flex gap-4'; let color = 'text-blue-400';
                if (type === 'success') color = 'text-emerald-400'; if (type === 'warn') color = 'text-rose-400';
                div.innerHTML = `<div class="pt-0.5"><div class="w-1.5 h-1.5 rounded-full mt-1.5 ${type==='warn'?'bg-rose-500':(type==='success'?'bg-emerald-500':'bg-blue-500')}"></div></div><div><p class="text-xs ${color} font-medium">${msg}</p></div>`;
                terminal.prepend(div); if (terminal.children.length > 25) terminal.removeChild(terminal.lastChild);
            }
            function updateUI(obs, reward = 0) {
                lucide.createIcons(); 
                animateCounter('top-esg', obs.sustainability_score, '');
                animateCounter('top-carbon', obs.carbon_footprint, ''); 
                animateCounter('top-sl', obs.service_level * 100, '', '%');
                animateCounter('top-score', obs.compliance_score, '');
                document.getElementById('step-counter').innerText = `${obs.current_step.toString().padStart(2, '0')} / 100`;
                document.getElementById('step-progress').style.width = `${obs.current_step}%`;
                if (obs.last_action && obs.last_action.includes('SHOCK')) { document.getElementById('shock-banner').style.display = 'block'; document.getElementById('shock-banner').innerText = obs.last_action; }
                else { document.getElementById('shock-banner').style.display = 'none'; }
                
                if (obs.market_intel && obs.market_intel.length > 0) {
                    const container = document.getElementById('market-news-container');
                    container.classList.remove('hidden');
                    const newsList = document.getElementById('market-news');
                    obs.market_intel.forEach(msg => {
                        const div = document.createElement('div');
                        div.className = 'text-sm font-medium text-slate-200 p-3 bg-blue-500/10 rounded-xl border border-blue-500/10 animate-pulse';
                        div.innerText = msg;
                        newsList.prepend(div);
                        if (newsList.children.length > 3) newsList.removeChild(newsList.lastChild);
                    });
                }
                
                if (document.getElementById('action-dest').options.length === 0) {
                    obs.warehouses.forEach(w => {
                        const opt = document.createElement('option'); opt.value = w.id; opt.innerText = w.name; document.getElementById('action-dest').appendChild(opt);
                        const opt2 = document.createElement('option'); opt2.value = w.id; opt2.innerText = w.name; document.getElementById('action-origin').appendChild(opt2);
                    });
                }
                document.getElementById('warehouse-grid').innerHTML = obs.warehouses.map(w => {
                    const c = w.utilization > 0.8 ? 'rose' : (w.utilization < 0.2 ? 'amber' : 'blue');
                    return `<div class="glass-panel rounded-2xl p-6 border-white/5 stat-card">
                        <div class="flex justify-between mb-6"><div><h4 class="font-bold text-sm text-white">${w.name}</h4><span class="text-[10px] text-slate-500 uppercase font-bold">${w.location}</span></div><div class="px-2 py-0.5 rounded bg-${c}-500/10 text-[9px] font-bold text-${c}-400 border border-${c}-500/20">${(w.utilization*100).toFixed(0)}%</div></div>
                        <div class="flex justify-between items-end mb-2"><div><p class="text-[9px] text-slate-500 uppercase font-bold">Stock level</p><p class="text-xl font-bold text-white">${w.inventory.toFixed(0)}</p></div><p class="text-[10px] text-slate-500">/ ${w.capacity}</p></div>
                        <div class="w-full h-1 bg-white/5 rounded-full overflow-hidden"><div class="h-full bg-${c}-500 transition-all duration-700" style="width: ${w.utilization*100}%"></div></div>
                    </div>`;
                }).join('');
                let linkHtml = '', nodeHtml = '';
                obs.warehouses.forEach((w, i) => {
                    const coords = [
                        {x: 390, y: 100}, // London Hub
                        {x: 680, y: 140}, // Tokyo Delta
                        {x: 540, y: 190}, // Mumbai Nexus
                        {x: 240, y: 130}, // Brooklyn Edge 
                        {x: 410, y: 110}  // Frankfurt Core
                    ][i % 5];
                    const tx = coords.x; const ty = coords.y;
                    linkHtml += `<path d="M 400 350 C 400 250, ${tx} 200, ${tx} ${ty}" stroke="rgba(59, 130, 246, 0.6)" stroke-width="2" fill="none" class="node-link" filter="url(#glow)" />`;
                    nodeHtml += `<g transform="translate(${tx}, ${ty})" filter="url(#glow)"><circle r="20" fill="rgba(59,130,246,0.05)" stroke="${w.utilization > 0.8 ? '#f43f5e' : '#3b82f6'}" stroke-width="1.5" stroke-dasharray="3 3" /><circle r="7" fill="${w.utilization > 0.8 ? '#f43f5e' : '#60a5fa'}" class="animate-pulse" /><text x="25" y="4" fill="${w.utilization > 0.8 ? '#fecdd3' : '#eff6ff'}" font-size="11" font-family="Space Grotesk" font-weight="bold" letter-spacing="1.5" text-shadow="0 0 10px rgba(0,0,0,1)">${w.name}</text></g>`;
                });
                document.getElementById('map-links').innerHTML = linkHtml; document.getElementById('map-nodes').innerHTML = nodeHtml;
                chartData.step.push(obs.current_step); chartData.demand.push(obs.forecasted_demand.reduce((acc, f) => acc + f.next_5_steps[0], 0));
                chartData.cost.push(obs.total_cost); chartData.sl.push(obs.service_level);
                const layout = { 
                    margin: { t: 5, b: 30, l: 40, r: 10 }, 
                    paper_bgcolor: 'rgba(0,0,0,0)', 
                    plot_bgcolor: 'rgba(0,0,0,0)', 
                    font: { color: '#94a3b8', size: 9, family: 'Space Grotesk' }, 
                    xaxis: { type: 'category', gridcolor: 'rgba(255,255,255,0.02)', zeroline: false }, 
                    yaxis: { gridcolor: 'rgba(255,255,255,0.02)', zeroline: false } 
                };
                const config = { responsive: true, displayModeBar: false };
                Plotly.react('demand-chart', [{ x: chartData.step, y: chartData.demand, type: 'scatter', line: { color: '#3b82f6', width: 2, shape: 'spline' }, fill: 'tozeroy', fillcolor: 'rgba(59, 130, 246, 0.05)' }], layout, config);
                Plotly.react('inventory-chart', [{ x: obs.warehouses.map(w => w.name), y: obs.warehouses.map(w => w.inventory), type: 'bar', marker: { color: '#3b82f6' }, opacity: 0.8 }], layout, config);
            }
            function animateCounter(id, target, prefix = '', suffix = '') {
                const el = document.getElementById(id); const current = parseFloat(el.innerText.replace(/[^\d.-]/g, '')) || 0;
                gsap.to({ val: current }, { val: target, duration: 1.2, ease: "power2.out", onUpdate: function() { 
                    let v = this.targets()[0].val;
                    if (id.includes('score') || id.includes('esg')) el.innerText = v.toFixed(2);
                    else if (id.includes('sl')) el.innerText = v.toFixed(1) + '%';
                    else el.innerText = prefix + v.toFixed(0) + suffix;
                } });
            }
            window.onload = resetEnv; lucide.createIcons();
        </script>
    </body>
    </html>
    """

def main():
    """Entry point for OpenEnv multi-mode routing"""
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
