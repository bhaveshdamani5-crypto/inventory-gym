#!/usr/bin/env python3
"""
AuditGym-v1 Hugging Face Space - Interactive Streamlit UI
Demonstrates OpenEnv environment with live demos and documentation
"""

import streamlit as st
import asyncio
import json
from src.env import AuditGymEnv
from src.models import Action
from src.grader import grade_easy, grade_medium, grade_hard

# Helper function to run async code in Streamlit
def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

# Page config
st.set_page_config(
    page_title="AuditGym-v1",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-box {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #FF6B6B;
    }
    .success-box {
        background-color: #f0fdf4;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #22c55e;
    }
    .info-box {
        background-color: #f0f9ff;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #0284c7;
    }
    .header-title {
        color: #1f2937;
        font-size: 2.5em;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'env_state' not in st.session_state:
    st.session_state.env_state = None
if 'current_step' not in st.session_state:
    st.session_state.current_step = 0
if 'total_reward' not in st.session_state:
    st.session_state.total_reward = 0.0
if 'history' not in st.session_state:
    st.session_state.history = []

# Header
st.markdown('<p class="header-title">🔍 AuditGym-v1: OpenEnv Forensic Audit Environment</p>', unsafe_allow_html=True)
st.markdown("**Detect synthetic fraud in transaction datasets using OpenEnv API**")
st.divider()

# Sidebar
with st.sidebar:
    st.markdown("### 📋 Navigation")
    page = st.radio("Select Section:", 
        ["🏠 Home", "🎮 Environment Explorer", "📚 API & OpenEnv Spec", "📊 Task Levels", "🎯 Live Demo"])

# ============ HOME PAGE ============
if page == "🏠 Home":
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### What is AuditGym-v1?")
        st.write("""
        AuditGym is a real-world OpenEnv environment for training AI agents to detect fraudulent 
        transactions in financial datasets. It presents a forensic audit challenge where agents 
        must intelligently query, verify, and flag suspicious activities.
        
        **Key Characteristics:**
        - 🎯 **Real-world task**: Forensic fraud detection
        - 📈 **Progressive difficulty**: Easy, Medium, Hard
        - 🏆 **OpenEnv compliant**: Standard async API
        - 💡 **Meaningful rewards**: Partial progress signals
        """)
        
        st.markdown("### How It Works")
        st.info("""
        1. **Query** (`query amount > 5000`): Filter transactions by criteria
        2. **Verify** (`verify id 123`): Get cross-reference information  
        3. **Flag** (`flag id 123`): Mark transaction as fraudulent
        
        The agent earns rewards for correct decisions and penalties for mistakes.
        """)
    
    with col2:
        st.markdown("### 📊 Statistics")
        st.metric("Total Frauds Hidden", "1-5", delta="Per Task")
        st.metric("Red Herrings", "5-50", delta="Per Task")
        st.metric("Max Episode Length", "1000", delta="Transactions")

# ============ ENVIRONMENT EXPLORER ============
elif page == "🎮 Environment Explorer":
    st.markdown("### 🎮 Interactive Environment Explorer")
    st.write("Test the OpenEnv environment with manual actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Task Configuration")
        difficulty = st.selectbox("Select Difficulty", ["Easy", "Medium", "Hard"])
        
        config_map = {
            "Easy": {"num_total": 100, "num_fraud": 1, "num_red_herring": 5, "max_steps": 50},
            "Medium": {"num_total": 500, "num_fraud": 3, "num_red_herring": 25, "max_steps": 100},
            "Hard": {"num_total": 1000, "num_fraud": 5, "num_red_herring": 50, "max_steps": 200}
        }
        config = config_map[difficulty]
        
        # Display config details
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Transactions", config["num_total"])
        col_b.metric("Frauds", config["num_fraud"])
        col_c.metric("Red Herrings", config["num_red_herring"])
    
    with col2:
        st.markdown("#### Episode Control")
        if st.button("🔄 Reset Environment", use_container_width=True):
            st.session_state.env_state = config
            st.session_state.current_step = 0
            st.session_state.total_reward = 0.0
            st.session_state.history = []
            st.success("✅ Environment reset!")
    
    if st.session_state.env_state:
        st.divider()
        
        st.markdown("#### ➡️ Take an Action")
        action_type = st.selectbox("Action Type", ["Query", "Verify", "Flag"])
        
        if action_type == "Query":
            field = st.selectbox("Field", ["amount"])
            operator = st.selectbox("Operator", [">", "<"])
            value = st.number_input("Value", value=5000.0)
            action_msg = f"query {field} {operator} {value}"
        elif action_type == "Verify":
            tx_id = st.number_input("Transaction ID", min_value=0, value=0)
            action_msg = f"verify id {tx_id}"
        else:  # Flag
            tx_id = st.number_input("Transaction ID to Flag", min_value=0, value=0)
            action_msg = f"flag id {tx_id}"
        
        if st.button("Execute Action", use_container_width=True, type="primary"):
            st.info(f"Action: {action_msg}")
            st.caption("Demo mode - showing sample execution")

# ============ API & OPENENV SPEC ============
elif page == "📚 API & OpenEnv Spec":
    st.markdown("### 📚 OpenEnv API Documentation")
    st.write("Complete OpenEnv specification and Swagger-like API reference")
    
    # Tabs for API sections
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Models", "🔄 Methods", "📡 OpenENV Spec", "💬 Messages"])
    
    with tab1:
        st.markdown("#### 🔹 Pydantic Models")
        
        st.markdown("**Action** - Agent's command")
        st.json({
            "message": "query amount > 5000"
        })
        
        st.markdown("**Observation** - Environment state")
        st.json({
            "transactions": [
                {"id": 0, "amount": 1500.5, "date": "2026-04-01", "description": "Transaction 0", "verified": False, "extra_info": ""}
            ],
            "step_count": 0,
            "echoed_message": "query amount > 5000"
        })
        
        st.markdown("**ResetResponse & StepResponse**")
        st.json({
            "observation": {"transactions": [], "step_count": 0, "echoed_message": ""},
            "reward": 0.10,
            "done": False
        })
    
    with tab2:
        st.markdown("#### 🔄 Core Methods")
        
        st.code("""
async reset() -> ResetResponse
    Initialize environment, return initial observation
    
async step(action: Action) -> StepResponse
    Execute action, return (observation, reward, done)
    
async state() -> Dict[str, Any]
    Get current environment state (flagged counts, step count)
        """, language="python")
    
    with tab3:
        st.markdown("#### 📡 OpenENV Specification")
        st.code("""name: AuditGym
version: v1
description: Forensic audit environment
models:
  - src.models.Action
  - src.models.Observation
  - src.models.ResetResponse
  - src.models.StepResponse
environment: src.env:AuditGymEnv
        """, language="yaml")
    
    with tab4:
        st.markdown("#### 💬 Message Format")
        st.write("**Natural Language Commands:**")
        st.code("""
# Query: Filter transactions
"query amount > 5000"
"query amount < 0"

# Verify: Get cross-reference
"verify id 0"
"verify id 123"

# Flag: Mark as fraudulent
"flag id 0"
"flag id 25"
        """)

# ============ TASK LEVELS ============
elif page == "📊 Task Levels":
    st.markdown("### 📊 Progressive Difficulty Levels")
    
    tasks = [
        {
            "name": "Easy",
            "icon": "🟢",
            "transactions": 100,
            "frauds": 1,
            "red_herrings": 5,
            "max_reward": 0.95,
            "difficulty": "Beginner - Single fraud in small dataset"
        },
        {
            "name": "Medium",
            "icon": "🟡",
            "transactions": 500,
            "frauds": 3,
            "red_herrings": 25,
            "max_reward": 2.85,
            "difficulty": "Intermediate - Multiple frauds with many red herrings"
        },
        {
            "name": "Hard",
            "icon": "🔴",
            "transactions": 1000,
            "frauds": 5,
            "red_herrings": 50,
            "max_reward": 4.75,
            "difficulty": "Advanced - Complex fraud detection scenario"
        }
    ]
    
    for task in tasks:
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns(4)
            
            col1.metric(f"{task['icon']} {task['name']}", task['difficulty'].split('-')[0])
            col2.metric("Transactions", task['transactions'])
            col3.metric("Frauds Hidden", task['frauds'])
            col4.metric("Red Herrings", task['red_herrings'])
            
            st.write(f"**Task:** {task['difficulty']}")
            st.write(f"**Max Achievable Reward:** {task['max_reward']:.2f}")
            
            # Reward breakdown
            st.markdown("""
            **Reward Structure:**
            - ✅ Correct fraud flag: +0.95
            - ✅ Correct clear: +0.70
            - ❌ False positive: +0.05 (penalty)
            - ❌ Step penalty: -0.02
            - 🔍 Query info: +0.10
            """)

# ============ LIVE DEMO ============
elif page == "🎯 Live Demo":
    st.markdown("### 🎯 Live Environment Demo")
    st.write("Watch the environment in action with a sample episode")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        difficulty = st.selectbox("Demo Difficulty", ["Easy", "Medium", "Hard"], key="demo_difficulty")
        
        demo_config = {
            "Easy": {"num_total": 100, "num_fraud": 1, "num_red_herring": 5, "max_steps": 10},
            "Medium": {"num_total": 500, "num_fraud": 3, "num_red_herring": 25, "max_steps": 15},
            "Hard": {"num_total": 1000, "num_fraud": 5, "num_red_herring": 50, "max_steps": 20}
        }
        config = demo_config[difficulty]
    
    with col2:
        st.metric("Demo Mode", f"{difficulty} Task", delta="Safe Execution")
    
    if st.button("▶️ Run Demo Episode", use_container_width=True, type="primary"):
        st.info("🎬 Running demo episode...")
        
        # Create environment
        env = AuditGymEnv(**config)
        
        # Run demo
        result = run_async(env.reset())
        total_reward = 0.0
        step = 0
        
        # Demo actions
        demo_actions = [
            "query amount > 5000",
            f"verify id 0",
            f"flag id 0",
            "query amount < 0",
        ]
        
        progress_bar = st.progress(0)
        demo_container = st.container(border=True)
        
        for action_msg in demo_actions[:config["max_steps"]]:
            step += 1
            
            result = run_async(env.step(Action(message=action_msg)))
            reward = result.reward
            total_reward += reward
            
            with demo_container:
                col_step, col_action, col_reward = st.columns([1, 3, 1])
                col_step.write(f"**Step {step}**")
                col_action.write(f"`{action_msg}`")
                col_reward.write(f"{reward:+.2f}" + ("🟢" if reward > 0 else "🔴"))
            
            progress_bar.progress(min(step / config["max_steps"], 1.0))
            
            if result.done:
                break
        
        # Final stats
        st.divider()
        st.success(f"✅ Demo Complete! Total Reward: {total_reward:.2f}")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Final Reward", f"{total_reward:.2f}")
        col2.metric("Steps Taken", step)
        
        state = run_async(env.state())
        col3.metric("Frauds Flagged", state['flagged_frauds'])
        
        # Grading
        if difficulty == "Easy":
            score = grade_easy(state)
        elif difficulty == "Medium":
            score = grade_medium(state)
        else:
            score = grade_hard(state)
        
        st.metric("Final Score", f"{score:.2%}", delta=f"{score - 0.5:.2%}" if score > 0.5 else f"{score:.2%}")
        
        run_async(env.close())

st.divider()
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9em;'>
AuditGym-v1 | OpenEnv Hackathon | 🔍 Forensic Fraud Detection Environment
</div>
""", unsafe_allow_html=True)

