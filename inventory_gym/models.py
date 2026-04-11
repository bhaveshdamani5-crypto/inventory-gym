"""
Pydantic models for InventoryGym-v1 OpenEnv environment
"""

from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import random
import math


class Warehouse(BaseModel):
    """Warehouse state"""
    id: int
    name: str
    inventory: float
    capacity: float
    holding_cost_per_unit: float
    location: str


class Order(BaseModel):
    """Pending order in transit"""
    id: int
    origin_warehouse: int
    dest_warehouse: int
    quantity: float
    steps_remaining: int
    cost: float


class Action(BaseModel):
    """Agent action: order replenishment from supplier OR transshipment between nodes"""
    dest_warehouse: int
    quantity: float
    origin_warehouse: int = -1  # -1 for Supplier, else Warehouse ID
    priority: str = "normal"    # "normal" or "expedited" (costs extra)


class InventoryObservation(BaseModel):
    """Current state of inventory system"""
    warehouses: List[Dict[str, Any]]
    pending_orders: List[Dict[str, Any]]
    forecasted_demand: List[Dict[str, Any]]
    historical_summary: List[Dict[str, Any]]  # New: past performance context
    current_step: int
    total_cost: float
    service_level: float                      # overall fulfillment rate
    carbon_footprint: float                   # NEW: Environmental impact metric
    sustainability_score: float               # NEW: Normalized ESG score (0.01 - 0.99)
    compliance_score: float                   # Live Hackathon Grade
    market_intel: List[str]                   # NLP news/intel
    last_action: Optional[str] = None
    instruction: Optional[str] = "Maximize fulfillment while minimizing carbon footprint."


class ResetResponse(BaseModel):
    """OpenEnv reset response"""
    observation: InventoryObservation
    info: Dict[str, Any] = {}


class StepResponse(BaseModel):
    """OpenEnv step response"""
    observation: InventoryObservation
    reward: float
    done: bool
    truncated: bool = False
    info: Dict[str, Any] = {}


def generate_demand_patterns(num_warehouses: int, num_steps: int) -> Dict[int, List[float]]:
    """Generate realistic demand patterns with seasonality, trends, and shocks."""
    demand_patterns = {}
    
    for warehouse_id in range(num_warehouses):
        base_demand = random.uniform(150, 400)
        trend = random.uniform(-0.2, 0.4) 
        seasonality_period = random.choice([7, 14, 28])
        
        demands = []
        for step in range(num_steps + 100):
            # Seasonality using sine wave for smoother transitions
            season_factor = 1.0 + 0.3 * math.sin(2 * math.pi * step / seasonality_period)
            
            # Random noise
            noise = random.gauss(0, base_demand * 0.1)
            
            # Occasional Black Swan / Demand Spike (1% chance)
            shock = 0
            if random.random() < 0.01:
                shock = base_demand * random.uniform(2.0, 4.0)
            
            demand = max(20, (base_demand + trend * step + noise) * season_factor + shock)
            demands.append(demand)
        
        demand_patterns[warehouse_id] = demands
    
    return demand_patterns


def initialize_warehouses(num_warehouses: int) -> List[Warehouse]:
    """Initialize warehouse network."""
    warehouses = []
    locations = ["North", "South", "East", "West", "Central"]
    
    for i in range(num_warehouses):
        # Different warehouses have different cost profiles
        h_cost = 0.3 + (i * 0.1) 
        cities = [
            ("London Hub", "United Kingdom"), ("Tokyo Delta", "Japan"), 
            ("Mumbai Nexus", "India"), ("Brooklyn Edge", "USA"), ("Frankfurt Core", "Germany")
        ]
        name, loc = cities[i % len(cities)]
        warehouse = Warehouse(
            id=i,
            name=name,
            inventory=random.uniform(600, 1000),
            capacity=4000,
            holding_cost_per_unit=h_cost,
            location=loc
        )
        warehouses.append(warehouse)
    
    return warehouses