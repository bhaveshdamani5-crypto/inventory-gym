import asyncio
import numpy as np
import random
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
    
    def __init__(self, num_warehouses=3, num_steps=100, lead_time=4, inventory_penalty_factor=1.0):
        self.num_warehouses = num_warehouses
        self.num_steps = num_steps
        self.lead_time = lead_time
        self.inventory_penalty_factor = inventory_penalty_factor
        
        self.current_step = 0
        self.warehouses: List[Warehouse] = []
        self.demand_patterns: Dict[int, List[float]] = {}
        self.history_demand: Dict[int, List[float]] = {}
        self.pending_orders: List[Order] = []
        self.order_id_counter = 0
        self.total_cost = 0.0
        self.total_demand = 0.0
        self.total_fulfilled = 0.0
        self.last_action_desc = None
        
        # State: Shock status
        self.shock_steps_left = 0
        self.shock_type = None # "demand", "logistics"

    async def reset(self) -> ResetResponse:
        self.current_step = 0
        self.order_id_counter = 0
        self.total_cost = 0.0
        self.total_demand = 0.0
        self.total_fulfilled = 0.0
        self.last_action_desc = None
        self.pending_orders = []
        self.shock_steps_left = 0
        self.shock_type = None
        
        self.warehouses = initialize_warehouses(self.num_warehouses)
        self.demand_patterns = generate_demand_patterns(self.num_warehouses, self.num_steps)
        self.history_demand = {i: [] for i in range(self.num_warehouses)}
        
        return ResetResponse(observation=self._get_obs())

    async def step(self, action: Action) -> StepResponse:
        self.current_step += 1
        reward = 0.0
        
        # --- 0. Systemic Shock Logic ---
        if self.shock_steps_left > 0:
            self.shock_steps_left -= 1
        elif random.random() < 0.02: # 2% chance of starting a new shock episode
            self.shock_steps_left = random.randint(3, 7)
            self.shock_type = random.choice(["demand", "logistics"])
            self.last_action_desc = f"SYSTEM ALERT: {self.shock_type.upper()} SHOCK DETECTED"

        # --- 1. Process Decisions (Replenishment vs Transshipment) ---
        if action.quantity > 0 and 0 <= action.dest_warehouse < len(self.warehouses):
            
            # A. Replenishment (From Supplier)
            if action.origin_warehouse == -1:
                # Economy of scale: Larger orders have slightly lower unit costs
                unit_price = 1.0 if action.quantity < 500 else 0.85
                premium = 0.6 if action.priority == "expedited" else 0.0
                
                # Logistics friction during logistics shock
                if self.shock_type == "logistics" and self.shock_steps_left > 0:
                    premium += 0.5 
                
                order_cost = action.quantity * (unit_price + premium)
                self.total_cost += order_cost
                reward -= order_cost * 0.001

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
                    reward -= move_cost * 0.0005
                    
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
            demand = self.demand_patterns[i][self.current_step]
            
            # Demand shock multiplier
            if self.shock_type == "demand" and self.shock_steps_left > 0:
                demand *= random.uniform(2.5, 4.0)
            
            self.history_demand[i].append(demand)
            self.total_demand += demand
            
            fulfilled = min(warehouse.inventory, demand)
            warehouse.inventory -= fulfilled
            self.total_fulfilled += fulfilled
            
            s_level = fulfilled / demand if demand > 0 else 1.0
            reward += s_level * 1.5 
            
            # Stockout Penalty
            if fulfilled < demand:
                loss = (demand - fulfilled)
                reward -= (loss / 100.0) * 0.3
            
            # Holding Costs
            h_cost = warehouse.inventory * warehouse.holding_cost_per_unit * self.inventory_penalty_factor
            self.total_cost += h_cost
            reward -= h_cost * 0.001
            
            # Safety Stock Optimization Penalty
            rolling_avg = np.mean(self.history_demand[i][-10:]) if len(self.history_demand[i]) > 10 else demand
            target_stock = rolling_avg * self.lead_time * 1.8
            stock_error = abs(warehouse.inventory - target_stock) / warehouse.capacity
            reward -= (stock_error ** 2) * 0.05

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
        """Calculate internal hackathon grade (0.01-0.99)"""
        global_sl = self.total_fulfilled / self.total_demand if self.total_demand > 0 else 1.0
        
        # SL Score: Exponential decay below 88%
        target_sl = 0.88
        sl_score = 1.0 if global_sl >= target_sl else (global_sl / target_sl) ** 2
        
        # Cost Score: Ratio against a theoretical budget
        theoretical_budget = (self.num_warehouses * 12000) + (self.current_step * self.num_warehouses * 50)
        cost_score = min(1.0, theoretical_budget / max(self.total_cost, 1))
        
        # Composite
        score = (0.6 * sl_score) + (0.4 * cost_score)
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
                "next_5_steps": [round(d, 1) for d in self.demand_patterns[i][self.current_step+1 : self.current_step+6]]
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
            compliance_score=round(self._calculate_compliance_score(), 4),
            last_action=action_desc
        )

    async def close(self): pass