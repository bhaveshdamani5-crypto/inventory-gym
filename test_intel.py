import asyncio
import random
from src.env import InventoryGymEnv
from src.models import Action

async def main():
    print("Starting Market Intelligence Verification Test...")
    env = InventoryGymEnv(num_warehouses=3)
    await env.reset()
    
    news_found = False
    for i in range(1, 101):
        # Taking no action to just see the world evolve
        resp = await env.step(Action(dest_warehouse=0, quantity=0))
        obs = resp.observation
        
        if obs.market_intel:
            print(f"\n[STEP {i}] NEWS RECEIVED:")
            for news in obs.market_intel:
                print(f" >> {news}")
            news_found = True
            
        if "ACTIVE" in str(obs.market_intel):
            print(f"[STEP {i}] SHOCK IS NOW LIVE!")
            
    if not news_found:
        print("\nNo news found in this 100-step sample (stochastic luck). Try again.")
    else:
        print("\nTest Complete: Intelligence Feed is functional.")

if __name__ == "__main__":
    asyncio.run(main())
