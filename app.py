from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import json
import asyncio
import os

# Import our environment
from src.env import InventoryGymEnv
from src.models import Action

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

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Ultra-Premium Interactive Intelligence Dashboard"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>InventoryGym-v1 | Supply Intelligence Elite</title>
        
        <!-- UI Libraries -->
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
        <script src="https://unpkg.com/lucide@latest"></script>
        <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
        
        <style>
            :root {
                --primary: #3b82f6; --primary-glow: rgba(59, 130, 246, 0.4);
                --accent: #f43f5e; --success: #10b981;
                --bg: #020617; --card-bg: rgba(15, 23, 42, 0.75); --border: rgba(255, 255, 255, 0.08);
            }
            body { 
                font-family: 'Outfit', sans-serif; background: var(--bg); color: #f1f5f9; overflow-x: hidden;
                background-image: url('https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=2000&q=80');
                background-size: cover; background-attachment: fixed; background-position: center;
            }
            h1, h2, h3, .font-heading { font-family: 'Space Grotesk', sans-serif; }
            .glass-panel { background: var(--card-bg); backdrop-filter: blur(20px); border: 1px solid var(--border); box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8); }
            .cyber-border { position: relative; overflow: hidden; }
            .cyber-border::after { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px; background: linear-gradient(90deg, transparent, var(--primary), transparent); animation: scan 3s linear infinite; }
            @keyframes scan { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } }
            .stat-card:hover { transform: translateY(-4px) scale(1.02); border-color: var(--primary-glow); background: rgba(15, 23, 42, 0.9); }
            .pulse-online { width: 8px; height: 8px; background: var(--success); border-radius: 50%; box-shadow: 0 0 10px var(--success); animation: pulse 2s infinite; }
            @keyframes pulse { 0% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.5); opacity: 0.5; } 100% { transform: scale(1); opacity: 1; } }
            .custom-scrollbar::-webkit-scrollbar { width: 4px; }
            .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
            .custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
            .node-link { stroke-dasharray: 10; animation: flow 20s linear infinite; transition: stroke 0.5s ease; }
            @keyframes flow { from { stroke-dashoffset: 200; } to { stroke-dashoffset: 0; } }
            .btn-hover:hover { box-shadow: 0 0 20px var(--primary-glow); }
            #shock-banner { position: fixed; top: 0; left: 0; width: 100%; z-index: 1000; display: none; background: rgba(244, 63, 94, 0.9); color: white; text-align: center; padding: 10px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase; animation: blink 1s infinite; }
            @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
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
                <div class="text-center group" title="Internal AI Reinforcement (Goal: Positive Trend)">
                    <p class="text-[9px] text-slate-500 uppercase font-bold tracking-widest mb-1">AI Reward</p>
                    <p id="top-reward" class="text-base font-bold text-emerald-400">0</p>
                </div>
                <div class="h-8 w-[1px] bg-slate-800"></div>
                <div class="text-center group" title="Official Hackathon Grade">
                    <p class="text-[9px] text-amber-500 uppercase font-bold tracking-widest mb-1">Final Score</p>
                    <p id="top-score" class="text-lg font-bold text-amber-400">0.01</p>
                </div>
                <div class="h-8 w-[1px] bg-slate-800"></div>
                <div class="text-center group">
                    <p class="text-[9px] text-slate-500 uppercase font-bold tracking-widest mb-1">Fulfillment %</p>
                    <p id="top-sl" class="text-base font-bold text-blue-400">100.0%</p>
                </div>
                <div class="h-8 w-[1px] bg-slate-800"></div>
                <div class="text-center group">
                    <p class="text-[9px] text-slate-500 uppercase font-bold tracking-widest mb-1">System Cost</p>
                    <p id="top-cost" class="text-base font-bold text-slate-300">$0</p>
                </div>
            </div>

            <div class="flex gap-4">
                <button onclick="resetEnv()" class="p-3 hover:bg-white/10 rounded-xl transition-all text-slate-400"><i data-lucide="rotate-ccw" class="w-5 h-5"></i></button>
                <div class="w-10 h-10 rounded-xl border border-white/10 bg-white/5 flex items-center justify-center overflow-hidden"><img src="https://api.dicebear.com/7.x/bottts-neutral/svg?seed=StrategyAlpha&backgroundColor=3b82f6" alt="AI Agent"></div>
            </div>
        </nav>

        <main class="flex-grow p-6 grid grid-cols-12 gap-6 max-w-[1800px] mx-auto w-full">
            <div class="col-span-12 xl:col-span-8 space-y-6">
                <div class="glass-panel rounded-3xl p-8 h-[450px] relative overflow-hidden group border border-white/5">
                    <div class="absolute top-8 left-8 z-10"><div class="flex items-center gap-3 mb-1"><span class="p-2 bg-blue-500/10 rounded-lg"><i data-lucide="globe" class="text-blue-400 w-5 h-5"></i></span><h3 class="text-xl font-bold">Network Topology Flow</h3></div></div>
                    <div class="absolute inset-0 flex items-center justify-center p-12 mt-12">
                        <svg viewBox="0 0 800 400" id="network-svg" class="w-full h-full drop-shadow-2xl">
                            <defs><filter id="glow"><feGaussianBlur stdDeviation="4" result="blur"/><feComposite in="SourceGraphic" in2="blur" operator="over"/></filter></defs>
                            <g transform="translate(100, 200)" filter="url(#glow)"><circle r="6" fill="white" /><text y="35" text-anchor="middle" fill="white" font-size="10" font-family="Space Grotesk" font-weight="bold">SUPPLIER</text></g>
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
                            <button onclick="runStep('normal')" class="btn-hover py-4 bg-white/5 hover:bg-white/10 rounded-2xl font-bold transition-all border border-white/5 text-slate-300">Standard Plan</button>
                            <button onclick="runStep('expedited')" class="btn-hover py-4 bg-gradient-to-br from-blue-600 to-indigo-700 hover:from-blue-500 rounded-2xl font-bold transition-all shadow-xl text-white">Rush Execute</button>
                        </div>
                    </div>
                </div>
                <div class="glass-panel rounded-3xl p-8 flex-grow flex flex-col min-h-[450px] border-white/5 overflow-hidden">
                    <h3 class="text-xs font-bold text-slate-400 uppercase tracking-widest mb-6 flex items-center gap-3"><span class="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span> Intelligence Stream</h3>
                    <div id="terminal" class="flex-grow overflow-y-auto custom-scrollbar space-y-4 pr-2"></div>
                    <div class="mt-8 pt-6 border-t border-white/5 flex justify-between items-center"><div class="flex items-center gap-3"><div class="w-32 h-1 bg-slate-800 rounded-full overflow-hidden"><div id="step-progress" class="h-full bg-blue-500 transition-all duration-700"></div></div><span class="text-xs font-mono font-bold text-slate-400" id="step-counter">00 / 100</span></div></div>
                </div>
            </div>
        </main>
        <script>
            let history = { step: [], demand: [], cost: [], sl: [] };
            async function resetEnv() {
                const res = await fetch('/reset', { method: 'POST' }); const data = await res.json();
                history = { step: [], demand: [], cost: [], sl: [] }; document.getElementById('terminal').innerHTML = '';
                log('Strategic session initiated.', 'info'); updateUI(data.observation);
            }
            async function runStep(priority) {
                const action = { dest_warehouse: parseInt(document.getElementById('action-dest').value), origin_warehouse: parseInt(document.getElementById('action-origin').value), quantity: parseFloat(document.getElementById('action-qty').value), priority: priority };
                const res = await fetch('/step', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(action) }); const data = await res.json();
                if (data.done) log('Simulation Objective Achieved.', 'success');
                else {
                    const r = data.reward;
                    if (r > 1.5) log(`Excellent Execute: +${r.toFixed(1)}`, 'success');
                    else if (r > 0) log(`Steady Performance: +${r.toFixed(1)}`, 'info');
                    else log(`High Friction: ${r.toFixed(1)}`, 'warn');
                }
                updateUI(data.observation, data.reward);
            }
            function log(msg, type) {
                const terminal = document.getElementById('terminal'); const div = document.createElement('div'); div.className = 'flex gap-4'; let color = 'text-blue-400';
                if (type === 'success') color = 'text-emerald-400'; if (type === 'warn') color = 'text-rose-400';
                div.innerHTML = `<div class="pt-0.5"><div class="w-1.5 h-1.5 rounded-full mt-1.5 ${type==='warn'?'bg-rose-500':(type==='success'?'bg-emerald-500':'bg-blue-500')}"></div></div><div><p class="text-xs ${color} font-medium">${msg}</p></div>`;
                terminal.prepend(div); if (terminal.children.length > 25) terminal.removeChild(terminal.lastChild);
            }
            function updateUI(obs, reward = 0) {
                lucide.createIcons(); animateCounter('top-reward', reward, reward >= 0 ? '+' : '');
                animateCounter('top-cost', obs.total_cost, '$'); animateCounter('top-sl', obs.service_level * 100, '', '%');
                const slScore = obs.service_level >= 0.88 ? 1.0 : Math.pow(obs.service_level / 0.88, 2);
                const costBudget = 40000; const costScore = Math.min(1.0, costBudget / Math.max(obs.total_cost, 1));
                const clamped = Math.max(0.01, Math.min(0.99, (0.6 * slScore) + (0.4 * costScore)));
                animateCounter('top-score', clamped, '');
                document.getElementById('step-counter').innerText = `${obs.current_step.toString().padStart(2, '0')} / 100`;
                document.getElementById('step-progress').style.width = `${obs.current_step}%`;
                if (obs.last_action && obs.last_action.includes('SHOCK')) { document.getElementById('shock-banner').style.display = 'block'; document.getElementById('shock-banner').innerText = obs.last_action; }
                else { document.getElementById('shock-banner').style.display = 'none'; }
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
                    const tx = 350 + (i % 2 === 0 ? 0 : 250); const ty = 80 + i * 80;
                    linkHtml += `<path d="M 120 200 C 200 200, 250 ${ty}, ${tx} ${ty}" stroke="rgba(59, 130, 246, 0.4)" stroke-width="1.5" fill="none" class="node-link" />`;
                    nodeHtml += `<g transform="translate(${tx}, ${ty})"><circle r="12" fill="rgba(255,255,255,0.05)" stroke="${w.utilization > 0.8 ? '#f43f5e' : '#3b82f6'}" stroke-width="1" stroke-dasharray="2 2" /><circle r="5" fill="${w.utilization > 0.8 ? '#f43f5e' : '#3b82f6'}" /><text x="18" y="4" fill="white" font-size="9" font-family="Space Grotesk" font-weight="bold">${w.name}</text></g>`;
                });
                document.getElementById('map-links').innerHTML = linkHtml; document.getElementById('map-nodes').innerHTML = nodeHtml;
                history.step.push(obs.current_step); history.demand.push(obs.forecasted_demand.reduce((acc, f) => acc + f.next_5_steps[0], 0));
                history.cost.push(obs.total_cost); history.sl.push(obs.service_level);
                const layout = { margin: { t: 5, b: 30, l: 40, r: 10 }, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)', font: { color: '#475569', size: 9, family: 'Space Grotesk' }, xaxis: { gridcolor: 'rgba(255,255,255,0.02)', zeroline: false }, yaxis: { gridcolor: 'rgba(255,255,255,0.02)', zeroline: false } };
                Plotly.react('demand-chart', [{ x: history.step, y: history.demand, type: 'scatter', line: { color: '#3b82f6', width: 2, shape: 'spline' }, fill: 'tozeroy', fillcolor: 'rgba(59, 130, 246, 0.05)' }], layout);
                Plotly.react('inventory-chart', [{ x: obs.warehouses.map(w => w.name), y: obs.warehouses.map(w => w.inventory), type: 'bar', marker: { color: 'rgba(59, 130, 246, 0.6)' } }], layout);
            }
            function animateCounter(id, target, prefix = '', suffix = '') {
                const el = document.getElementById(id); const current = parseFloat(el.innerText.replace(/[^\d.-]/g, '')) || 0;
                gsap.to({ val: current }, { val: target, duration: 1.2, ease: "power2.out", onUpdate: function() { 
                    let v = this.targets()[0].val;
                    if (id.includes('score')) el.innerText = v.toFixed(2);
                    else if (id.includes('sl')) el.innerText = v.toFixed(1) + '%';
                    else if (id.includes('reward')) {
                        el.className = `text-base font-bold ${v >= 0 ? 'text-emerald-400' : 'text-rose-400'}`;
                        el.innerText = (v >= 0 ? '+' : '') + v.toFixed(0);
                    } else el.innerText = prefix + v.toFixed(0) + suffix;
                } });
            }
            window.onload = resetEnv; lucide.createIcons();
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
