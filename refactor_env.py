import re

file_path = r'c:\Users\BHAVESH\Downloads\audit-gym\inventory_gym\env.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Inject Config Constants into __init__
init_target = "self.upcoming_shocks = [] # [{type, region, countdown}]"
init_replacement = """self.upcoming_shocks = [] # [{type, region, countdown}]
        
        # Reward Shaping Weights (Normalized)
        self.w_order_cost = 0.0001
        self.w_move_cost = 0.00005
        self.w_sl_bonus = 0.6
        self.w_stockout_pen = 0.05
        self.w_holding_pen = 0.00001
        self.w_resilience_bonus = 0.15
        self.w_safety_error = 0.005
"""
text = text.replace(init_target, init_replacement)

# 2. Refactor step function
step_target = """    async def step(self, action: Action) -> StepResponse:
        self.current_step += 1
        reward = 0.0"""

step_replacement = """    def _process_shocks(self):
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
            if random.random() < self.shock_prob:
                type = random.choice(["demand", "logistics"])
                region = random.choice(["North", "South", "East", "West", "Central"])
                countdown = random.randint(2, 4)
                self.upcoming_shocks.append({"type": type, "region": region, "countdown": countdown})
                
                adjectives = ["Severe", "Unexpected", "Moderate", "Critical", "Escalating"]
                sectors = ["retail", "industrial", "consumer", "logistics", "automation"]
                verbs = ["suggest", "indicate", "forecast", "warn of", "highlight"]
                
                if type == "demand":
                    self.market_intel.append(f"INTEL: {random.choice(adjectives)} signals {random.choice(verbs)} a viral surge in the {region} {random.choice(sectors)} sector.")
                else:
                    self.market_intel.append(f"INTEL: {random.choice(adjectives)} disruptions {random.choice(verbs)} bottlenecks for {region} trade routes.")
        
        if self.shock_type:
            self.last_action_desc = f"SYSTEM ALERT: {self.shock_type.upper()} SHOCK - {self.shock_region.upper()}"

    def _resolve_logistics(self, action: Action) -> float:
        reward_delta = 0.0
        if action.quantity > 0 and 0 <= action.dest_warehouse < len(self.warehouses):
            if action.origin_warehouse == -1:
                unit_price = 1.0 if action.quantity < 500 else 0.85
                premium = 0.6 if action.priority == "expedited" else 0.0
                if self.shock_type == "logistics" and self.shock_steps_left > 0:
                    dest_region = self.warehouses[action.dest_warehouse].location
                    if dest_region == self.shock_region:
                        premium += 0.8
                
                carbon_base = action.quantity * 0.01
                carbon_mult = 4.0 if action.priority == "expedited" else 1.0
                self.total_carbon += carbon_base * carbon_mult
                order_cost = action.quantity * (unit_price + premium)
                self.total_cost += order_cost
                reward_delta -= order_cost * self.w_order_cost

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

            elif 0 <= action.origin_warehouse < len(self.warehouses) and action.origin_warehouse != action.dest_warehouse:
                origin = self.warehouses[action.origin_warehouse]
                move_qty = min(action.quantity, origin.inventory)
                if move_qty > 0:
                    origin.inventory -= move_qty
                    move_cost = 50.0 + (move_qty * 0.2)
                    self.total_cost += move_cost
                    reward_delta -= move_cost * self.w_move_cost
                    
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
                    reward_delta -= 0.1
        return reward_delta

    def _compute_local_dynamics(self) -> float:
        reward_delta = 0.0
        for i, warehouse in enumerate(self.warehouses):
            demand_idx = self.current_step - 1
            demand = self.demand_patterns[i][demand_idx]
            
            if self.shock_type == "demand" and self.shock_steps_left > 0:
                if warehouse.location == self.shock_region:
                    demand *= random.uniform(3.0, 5.0)
            
            self.history_demand[i].append(demand)
            self.total_demand += demand
            
            fulfilled = min(warehouse.inventory, demand)
            warehouse.inventory -= fulfilled
            self.total_fulfilled += fulfilled
            
            s_level = fulfilled / demand if demand > 0 else 1.0
            reward_delta += (s_level * self.w_sl_bonus) / self.num_warehouses 
            
            if fulfilled < demand:
                loss = (demand - fulfilled) / max(demand, 1)
                reward_delta -= (loss * self.w_stockout_pen) / self.num_warehouses
            
            h_cost = warehouse.inventory * warehouse.holding_cost_per_unit * self.inventory_penalty_factor
            self.total_cost += h_cost
            reward_delta -= (h_cost * self.w_holding_pen) / self.num_warehouses
            
            if 0.15 < (warehouse.inventory / warehouse.capacity) < 0.85:
                reward_delta += self.w_resilience_bonus / self.num_warehouses
            
            rolling_avg = np.mean(self.history_demand[i][-10:]) if len(self.history_demand[i]) > 10 else demand
            target_stock = rolling_avg * self.lead_time * 1.8
            stock_error = abs(warehouse.inventory - target_stock) / warehouse.capacity
            reward_delta -= (stock_error ** 2) * self.w_safety_error / self.num_warehouses
        return reward_delta

    def _store_step_data(self):
        step_cost = self.total_cost - getattr(self, '_prev_cost', 0.0)
        step_carbon = self.total_carbon - getattr(self, '_prev_carbon', 0.0)
        step_demand = sum(self.demand_patterns[i][self.current_step - 1] for i in range(self.num_warehouses))
        step_fulfilled = self.total_fulfilled - getattr(self, '_prev_fulfilled', 0.0)
        
        self.step_history.append({
            "step": self.current_step,
            "demand": step_demand,
            "fulfilled": step_fulfilled,
            "cost": step_cost,
            "carbon": step_carbon
        })
        self._prev_cost = self.total_cost
        self._prev_carbon = self.total_carbon
        self._prev_fulfilled = self.total_fulfilled

    async def step(self, action: Action) -> StepResponse:
        self.current_step += 1
        reward = 0.0
        
        self.market_intel = []
        self._process_shocks()
        reward += self._resolve_logistics(action)
        
        for order in self.pending_orders[:]:
            order.steps_remaining -= 1
            if order.steps_remaining <= 0:
                self.warehouses[order.dest_warehouse].inventory += order.quantity
                self.pending_orders.remove(order)
                
        reward += self._compute_local_dynamics()
        self._store_step_data()"""

# We need to drop everything from process decisions to the end of step
start_drop_idx = text.find('async def step(self, action: Action) -> StepResponse:')
end_drop_idx = text.find('def _calculate_compliance_score', start_drop_idx)

if start_drop_idx != -1 and end_drop_idx != -1:
    new_text = text[:start_drop_idx] + step_replacement + "\n\n    " + text[end_drop_idx:]
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_text)
    print("Env refactor success")
