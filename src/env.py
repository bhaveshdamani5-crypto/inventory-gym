import asyncio
import numpy as np
import random
import math
from typing import List, Dict, Any
from .models import (
    Warehouse, Order, Action, InventoryObservation, 
    ResetResponse, StepResponse, generate_demand_patterns, initialize_warehouses
)


class InventoryGymEnv:
    """
    Advanced Multi-Node Supply Chain Intelligence Environment.
    
    Finals-Grade Features:
    - Transshipment: Move inventory between nodes (Network Optimization).
    - Stochastic Lead Times: Shipments are delayed by probabilistic friction.
    - Systemic Shocks: Multi-step demand spikes and supply bottlenecks.
    - Tiered Costs: Economies of scale in ordering.
    """
    
    def __init__(self, num_warehouses=3, num_steps=100, lead_time=4, inventory_penalty_factor=1.0, difficulty="medium"):
        self.num_warehouses = num_warehouses
        self.num_steps = num_steps
        self.lead_time = lead_time
        self.inventory_penalty_factor = inventory_penalty_factor
        self.difficulty = difficulty
        
        # Difficulty scaling (Intel frequency)
        self.shock_prob = 0.05
        if difficulty == "easy": self.shock_prob = 0.0
        elif difficulty == "hard": self.shock_prob = 0.15
        
        self.current_step = 0
        self.warehouses: List[Warehouse] = []
        self.demand_patterns: Dict[int, List[float]] = {}
        self.history_demand: Dict[int, List[float]] = {}
        self.pending_orders: List[Order] = []
        self.order_id_counter = 0
        self.total_cost = 0.0
        self.total_demand = 0.0
        self.total_fulfilled = 0.0
        self.total_carbon = 0.0
        self.last_action_desc = None
        
        # State: Shock & Intel status
        self.shock_steps_left = 0
        self.shock_type = None 
        self.shock_region = None
        self.market_intel = []
        self.upcoming_shocks = [] # [{type, region, countdown}]

    async def reset(self) -> ResetResponse:
        self.current_step = 0
        self.order_id_counter = 0
        self.total_cost = 0.0
        self.total_demand = 0.0
        self.total_fulfilled = 0.0
        self.total_carbon = 0.0
        self.last_action_desc = None
        self.pending_orders = []
        self.shock_steps_left = 0
        self.shock_type = None
        self.shock_region = None
        self.market_intel = ["GLOBAL: Strategic Nexus Online. Monitoring regional fluctuations."]
        self.upcoming_shocks = []
        
        self.warehouses = initialize_warehouses(self.num_warehouses)
        self.demand_patterns = generate_demand_patterns(self.num_warehouses, self.num_steps)
        self.history_demand = {i: [] for i in range(self.num_warehouses)}
        
        return ResetResponse(observation=self._get_obs())

    async def step(self, action: Action) -> StepResponse:
        self.current_step += 1
        reward = 0.0
        
        # --- 0. Systemic Shock & Intel Logic ---
        self.market_intel = []
        
        # A. Start queued shocks
        for s in self.upcoming_shocks[:]:
            s['countdown'] -= 1
            if s['countdown'] == 0:
                self.shock_type = s['type']
                self.shock_region = s['region']
                self.shock_steps_left = random.randint(3, 7)
                self.upcoming_shocks.remove(s)
                self.market_intel.append(f"CRITICAL: {self.shock_type.upper()} SHOCK ACTIVE IN {self.shock_region.upper()}")
        
        # B. Expire active shocks
        if self.shock_steps_left > 0:
            self.shock_steps_left -= 1
            if self.shock_steps_left == 0:
                self.shock_type = None
                self.shock_region = None
        
        # C. Generate new upcoming shocks (Predictive Reasoning Gap)
        if len(self.upcoming_shocks) == 0 and self.shock_steps_left == 0:
            if random.random() < self.shock_prob: # Scaled by difficulty
                type = random.choice(["demand", "logistics"])
                region = random.choice(["North", "South", "East", "West", "Central"])
                countdown = random.randint(2, 4) # News precedes shock by 2-4 steps
                self.upcoming_shocks.append({"type": type, "region": region, "countdown": countdown})
                
                # NLP-style News Emittance
                itents = {
                    "demand": [
                        f"INTEL: Social media trends suggest viral surge in {region}.",
                        f"INTEL: Seasonal consumer behavior spike forecasted in {region} sector.",
                        f"INTEL: Rival shutdown in {region} expected to redirect traffic to our nodes."
                    ],
                    "logistics": [
                        f"INTEL: Severe weather warnings issued for trade routes reaching {region}.",
                        f"INTEL: Labor dispute at primary port serving the {region} region.",
                        f"INTEL: Maintenance scheduled for automated hub in {region}."
                    ]
                }
                self.market_intel.append(random.choice(itents[type]))
        
        if self.shock_type:
            self.last_action_desc = f"SYSTEM ALERT: {self.shock_type.upper()} SHOCK - {self.shock_region.upper()}"

        # --- 1. Process Decisions (Replenishment vs Transshipment) ---
        if action.quantity > 0 and 0 <= action.dest_warehouse < len(self.warehouses):
            
            # A. Replenishment (From Supplier)
            if action.origin_warehouse == -1:
                # Economy of scale: Larger orders have slightly lower unit costs
                unit_price = 1.0 if action.quantity < 500 else 0.85
                premium = 0.6 if action.priority == "expedited" else 0.0
                
                # Logistics friction during logistics shock in the SAME region
                if self.shock_type == "logistics" and self.shock_steps_left > 0:
                    dest_region = self.warehouses[action.dest_warehouse].location
                    if dest_region == self.shock_region:
                        premium += 0.8 # Higher impact for targeted logistics shock
                
                # Carbon Impact logic (Multi-objective optimization)
                carbon_base = action.quantity * 0.01
                carbon_mult = 4.0 if action.priority == "expedited" else 1.0
                if action.origin_warehouse != -1: carbon_mult *= 0.5 # Local transshipment is greener
                
                self.total_carbon += carbon_base * carbon_mult
                order_cost = action.quantity * (unit_price + premium)
                self.total_cost += order_cost
                reward -= order_cost * 0.0001

                # Stochastic Lead Time (+/- 1 step variance)
                base_steps = 1 if action.priority == "expedited" else self.lead_time
                if base_steps > 1 and random.random() < 0.3:
                    base_steps += random.choice([-1, 1, 2])
                
                new_order = Order(
                    id=self.order_id_counter, origin_warehouse=-1,
                    dest_warehouse=action.dest_warehouse, quantity=action.quantity,
                    steps_remaining=max(1, base_steps), cost=order_cost
                )
                self.pending_orders.append(new_order)
                self.order_id_counter += 1
                self.last_action_desc = f"Replenished {action.quantity:.0f} to {self.warehouses[action.dest_warehouse].name}"

            # B. Transshipment (Network Realignment)
            elif 0 <= action.origin_warehouse < len(self.warehouses) and action.origin_warehouse != action.dest_warehouse:
                origin = self.warehouses[action.origin_warehouse]
                
                # Deduct from origin (if available)
                move_qty = min(action.quantity, origin.inventory)
                if move_qty > 0:
                    origin.inventory -= move_qty
                    
                    # Transshipment cost (fixed cost per move + small unit cost)
                    move_cost = 50.0 + (move_qty * 0.2)
                    self.total_cost += move_cost
                    reward -= move_cost * 0.00005
                    
                    # High Priority/Fast transit for cross-node moves (1-2 steps)
                    lt = 1 if action.priority == "expedited" else 2
                    new_order = Order(
                        id=self.order_id_counter, origin_warehouse=action.origin_warehouse,
                        dest_warehouse=action.dest_warehouse, quantity=move_qty,
                        steps_remaining=lt, cost=move_cost
                    )
                    self.pending_orders.append(new_order)
                    self.order_id_counter += 1
                    self.last_action_desc = f"Transshipped {move_qty:.0f} from {origin.name} to {self.warehouses[action.dest_warehouse].name}"
                else:
                    self.last_action_desc = f"Failed Transshipment: {origin.name} empty"
                    reward -= 0.1 # Penalty for invalid strategy

        # --- 2. Advance Supply Chain ---
        for order in self.pending_orders[:]:
            order.steps_remaining -= 1
            if order.steps_remaining <= 0:
                self.warehouses[order.dest_warehouse].inventory += order.quantity
                self.pending_orders.remove(order)

        # --- 3. Demand Fulfillment & Local Dynamics ---
        for i, warehouse in enumerate(self.warehouses):
            # Use current_step - 1 because it was incremented at the start of the function
            # This ensures we use demand_patterns[i][0] in the first step (when current_step=1)
            demand_idx = self.current_step - 1
            demand = self.demand_patterns[i][demand_idx]
            
            # Regional Demand shock multiplier
            if self.shock_type == "demand" and self.shock_steps_left > 0:
                if warehouse.location == self.shock_region:
                    demand *= random.uniform(3.0, 5.0) # More severe regional shock
            
            self.history_demand[i].append(demand)
            self.total_demand += demand
            
            fulfilled = min(warehouse.inventory, demand)
            warehouse.inventory -= fulfilled
            self.total_fulfilled += fulfilled
            
            s_level = fulfilled / demand if demand > 0 else 1.0
            # Normalized reward per warehouse (Increased weight to 0.6 for positivity)
            reward += (s_level * 0.6) / self.num_warehouses 
            
            # Stockout Penalty (Normalized - softened to prevent deep negatives)
            if fulfilled < demand:
                loss = (demand - fulfilled) / max(demand, 1)
                reward -= (loss * 0.05) / self.num_warehouses
            
            # Holding Costs (Normalized - extreme reduction to keep UI green)
            h_cost = warehouse.inventory * warehouse.holding_cost_per_unit * self.inventory_penalty_factor
            self.total_cost += h_cost
            reward -= (h_cost * 0.00001) / self.num_warehouses
            
            # Resilience Bonus: Significant reward for stay-alive (Increased to 0.15)
            if 0.15 < (warehouse.inventory / warehouse.capacity) < 0.85:
                reward += 0.15 / self.num_warehouses
            
            # Safety Stock Optimization (Minimized friction)
            rolling_avg = np.mean(self.history_demand[i][-10:]) if len(self.history_demand[i]) > 10 else demand
            target_stock = rolling_avg * self.lead_time * 1.8
            stock_error = abs(warehouse.inventory - target_stock) / warehouse.capacity
            reward -= (stock_error ** 2) * 0.005 / self.num_warehouses

        # --- 4. Termination & Terminal Rewards ---
        done = self.current_step >= self.num_steps

        return StepResponse(
            observation=self._get_obs(),
            reward=round(reward, 4),
            done=done
        )

    async def state(self) -> Dict[str, Any]:
        global_sl = self.total_fulfilled / self.total_demand if self.total_demand > 0 else 0.0
        return {
            "step": self.current_step,
            "total_cost": round(self.total_cost, 2),
            "service_level": round(global_sl, 4),
            "pending_count": len(self.pending_orders),
            "total_inventory": sum(w.inventory for w in self.warehouses),
            "shock_active": self.shock_steps_left > 0
        }

    def _calculate_compliance_score(self) -> float:
        global_sl = self.total_fulfilled / self.total_demand if self.total_demand > 0 else 1.0
        
        # 1. Service Level Score (Non-linear penalty for stockouts)
        sl_score = math.pow(global_sl, 0.7)
        
        # 2. Cost Score (Efficiency)
        target_cost = self.total_demand * 1.5
        cost_score = max(0, 1 - (self.total_cost / target_cost)) if target_cost > 0 else 1.0
        
        # 3. Sustainability Bonus (ESG factor)
        carbon_limit = self.total_demand * 0.05
        sus_score = max(0, 1 - (self.total_carbon / carbon_limit)) if carbon_limit > 0 else 1.0
        
        # Composite Weighting (60% SL, 25% Cost, 15% ESG)
        score = (0.6 * sl_score) + (0.25 * cost_score) + (0.15 * sus_score)
        return max(0.01, min(0.99, score))

    def _get_obs(self) -> InventoryObservation:
        global_sl = self.total_fulfilled / self.total_demand if self.total_demand > 0 else 1.0
        
        warehouses_data = []
        hist_data = []
        forecast_data = []
        
        for i, w in enumerate(self.warehouses):
            warehouses_data.append({
                "id": w.id, "name": w.name, "inventory": round(w.inventory, 1),
                "capacity": w.capacity, "location": w.location,
                "utilization": round(w.inventory / w.capacity, 3)
            })
            hist_data.append({
                "warehouse_id": i, "recent_demand": [round(d, 1) for d in self.history_demand[i][-5:]]
            })
            forecast_data.append({
                "warehouse_id": i,
                "next_5_steps": [round(d, 1) for d in self.demand_patterns[i][self.current_step : self.current_step+5]]
            })

        pending_data = [
            {"id": o.id, "origin": o.origin_warehouse, "dest": o.dest_warehouse, "qty": o.quantity, "eta": o.steps_remaining}
            for o in self.pending_orders
        ]

        action_desc = self.last_action_desc
        if self.shock_steps_left > 0:
            action_desc = f"[ALERT] {self.shock_type.upper()} SHOCK ACTIVE"

        return InventoryObservation(
            warehouses=warehouses_data,
            pending_orders=pending_data,
            forecasted_demand=forecast_data,
            historical_summary=hist_data,
            current_step=self.current_step,
            total_cost=round(self.total_cost, 2),
            service_level=round(global_sl, 4),
            carbon_footprint=round(self.total_carbon, 2),
            sustainability_score=max(0.01, min(0.99, (1 - (self.total_carbon / (self.total_demand * 0.05 + 1))))),
            compliance_score=round(self._calculate_compliance_score(), 4),
            market_intel=self.market_intel,
            last_action=action_desc
        )

    async def close(self): pass