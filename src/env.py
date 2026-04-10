import asyncio
import numpy as np
from typing import List, Dict, Any
from .models import (
    Warehouse, Order, Action, InventoryObservation, 
    ResetResponse, StepResponse, generate_demand_patterns, initialize_warehouses
)


class InventoryGymEnv:
    """
    High-fidelity multi-warehouse inventory management environment.
    Features:
    - Seasonal/stochastic demand with 'Black Swan' shocks
    - Multi-objective reward (Cost vs. Service Level)
    - Strategic lead-time management
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

    async def reset(self) -> ResetResponse:
        self.current_step = 0
        self.order_id_counter = 0
        self.total_cost = 0.0
        self.total_demand = 0.0
        self.total_fulfilled = 0.0
        self.last_action_desc = None
        self.pending_orders = []
        
        self.warehouses = initialize_warehouses(self.num_warehouses)
        self.demand_patterns = generate_demand_patterns(self.num_warehouses, self.num_steps)
        self.history_demand = {i: [] for i in range(self.num_warehouses)}
        
        return ResetResponse(observation=self._get_obs())

    async def step(self, action: Action) -> StepResponse:
        self.current_step += 1
        reward = 0.0
        
        # 1. Process Order Action
        if action.quantity > 0 and 0 <= action.dest_warehouse < len(self.warehouses):
            # Cost breakdown: base + priority premium
            base_unit_cost = 1.0
            premium = 0.5 if action.priority == "expedited" else 0.0
            order_cost = action.quantity * (base_unit_cost + premium)
            
            self.total_cost += order_cost
            reward -= order_cost * 0.005 # Direct cost penalty
            
            steps = 1 if action.priority == "expedited" else self.lead_time
            new_order = Order(
                id=self.order_id_counter,
                origin_warehouse=-1,
                dest_warehouse=action.dest_warehouse,
                quantity=action.quantity,
                steps_remaining=steps,
                cost=order_cost
            )
            self.pending_orders.append(new_order)
            self.order_id_counter += 1
            self.last_action_desc = f"Ordered {action.quantity:.0f} to {self.warehouses[action.dest_warehouse].name} ({action.priority})"
        else:
            self.last_action_desc = "No action taken"

        # 2. Advance Pending Orders
        arrived = []
        for order in self.pending_orders[:]:
            order.steps_remaining -= 1
            if order.steps_remaining <= 0:
                self.warehouses[order.dest_warehouse].inventory += order.quantity
                self.pending_orders.remove(order)
                arrived.append(order)

        # 3. Fulfill Demand & Calculate Rewards
        current_service_levels = []
        for i, warehouse in enumerate(self.warehouses):
            demand = self.demand_patterns[i][self.current_step]
            self.history_demand[i].append(demand)
            self.total_demand += demand
            
            fulfilled = min(warehouse.inventory, demand)
            warehouse.inventory -= fulfilled
            self.total_fulfilled += fulfilled
            
            # Per-warehouse service level for this step
            s_level = fulfilled / demand if demand > 0 else 1.0
            current_service_levels.append(s_level)
            
            # --- NOVEL REWARD BALANCING ---
            
            # A. Fulfillment Reward: Heavy incentive to meet demand
            reward += s_level * 0.4
            
            # B. Stockout Penalty: Nonlinear penalty for total failures
            stockout = max(0, demand - fulfilled)
            if stockout > 0:
                reward -= (stockout / 100.0) * 0.2  # Scaled by magnitude
            
            # C. Holding Cost: Based on remaining inventory
            h_cost = warehouse.inventory * warehouse.holding_cost_per_unit * self.inventory_penalty_factor
            self.total_cost += h_cost
            reward -= h_cost * 0.002
            
            # D. Safety Stock 'Goldilocks' Bonus
            # Ideal stock is lead_time * average_demand. We use a heuristic here.
            avg_demand = np.mean(self.history_demand[i][-7:]) if len(self.history_demand[i]) >= 7 else demand
            target_stock = avg_demand * self.lead_time * 1.5
            
            if 0.8 * target_stock <= warehouse.inventory <= 2.5 * target_stock:
                reward += 0.05 # Bonus for staying in optimal planning range
            elif warehouse.inventory > 5 * target_stock:
                reward -= 0.1  # Significant waste penalty

        # 4. Global Episode Progress
        done = self.current_step >= self.num_steps
        
        # E. Terminal Reward (Service Level Consistency)
        if done:
            global_service_level = self.total_fulfilled / self.total_demand if self.total_demand > 0 else 0.0
            if global_service_level > 0.95:
                reward += 2.0  # Big bonus for excellent supply chain health
            elif global_service_level < 0.70:
                reward -= 2.0  # Severe penalty for systematic failure

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
            "total_inventory": sum(w.inventory for w in self.warehouses)
        }

    def _get_obs(self) -> InventoryObservation:
        global_sl = self.total_fulfilled / self.total_demand if self.total_demand > 0 else 1.0
        
        warehouses_data = []
        hist_data = []
        forecast_data = []
        
        for i, w in enumerate(self.warehouses):
            warehouses_data.append({
                "id": w.id,
                "name": w.name,
                "inventory": round(w.inventory, 1),
                "capacity": w.capacity,
                "location": w.location,
                "utilization": round(w.inventory / w.capacity, 3)
            })
            
            # Historical context (last 5 steps)
            hist_data.append({
                "warehouse_id": i,
                "recent_demand": [round(d, 1) for d in self.history_demand[i][-5:]]
            })
            
            # Forecast (next 5 steps)
            forecast_data.append({
                "warehouse_id": i,
                "next_5_steps": [round(d, 1) for d in self.demand_patterns[i][self.current_step+1 : self.current_step+6]]
            })

        pending_data = [
            {"id": o.id, "dest": o.dest_warehouse, "qty": o.quantity, "eta": o.steps_remaining}
            for o in self.pending_orders
        ]

        return InventoryObservation(
            warehouses=warehouses_data,
            pending_orders=pending_data,
            forecasted_demand=forecast_data,
            historical_summary=hist_data,
            current_step=self.current_step,
            total_cost=round(self.total_cost, 2),
            service_level=round(global_sl, 4),
            last_action=self.last_action_desc
        )

    async def close(self): pass