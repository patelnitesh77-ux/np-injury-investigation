# LangGraph Injury Investigation Agent - Setup Guide

## Quick Start

### 1. Setup Environment
```bash
mkdir langgraph-injury-agent
cd langgraph-injury-agent

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install langgraph langchain-anthropic pandas python-dotenv
```

### 2. Add Your API Key
Create a file called `.env`:
```
ANTHROPIC_API_KEY=your_actual_api_key_here
```

Get your API key from: https://console.anthropic.com/

### 3. Add the Files
Copy these 4 files into your `langgraph-injury-agent` folder:
- `injury_agent.py` (the main agent)
- `injury_data.csv` (your injury records)
- `load_data.csv` (your load monitoring data)
- `fixture_schedule.csv` (your match schedule)

### 4. Replace with YOUR Data
Open each CSV file and replace with your actual data:

**injury_data.csv** - Match your UEFA injury template format
- Add more columns if needed (TSR scores, GPS data, etc.)
- Keep the Date, Player_ID, Location, ACWR columns

**load_data.csv** - Your daily/weekly load monitoring
- Use your actual ACWR calculations
- Add RPE, session duration, GPS metrics

**fixture_schedule.csv** - Your match calendar
- Include all competitions
- Add recovery time between matches

### 5. Run It!
```bash
python injury_agent.py
```

## What You'll See

The agent will:
1. Load your injury data
2. Analyze load patterns with AI decision-making
3. Conditionally route to either recovery or fixture analysis
4. Validate the hypothesis
5. Loop back if confidence is low
6. Generate a final report

## Expected Output
```
📊 Fetching injury data...
Found 3 hamstring injuries in February
  • 2024-02-05: Arjun Sharma - Grade 1
  • 2024-02-12: Rahul Patel - Grade 2
  • 2024-02-18: Vikram Singh - Grade 1

🏋️ Analyzing training load patterns...
Load analysis: Player P001: Max ACWR 1.27...
AI Decision: STRONG_CORRELATION

→ Load correlation found, checking recovery metrics...

😴 Checking recovery metrics...
Recovery analysis: Avg sleep 6.1hrs, Wellness 62/100
AI Decision: RECOVERY_DEFICIENT

🔍 Validating hypothesis...
Validation result:
CONFIDENCE: HIGH
SCORE: 0.85
REASONING: Strong evidence from both load spikes and recovery deficiency.

✓ Sufficient confidence, generating report...

📝 Generating final report...

============================================================
FINAL INVESTIGATION REPORT
============================================================
The February hamstring injury cluster (3 cases) was primarily 
caused by acute training load spikes (ACWR > 1.25) combined 
with inadequate recovery. All injured players showed compromised 
sleep (<7hrs) and low wellness scores (<65), reducing their 
tissue resilience during high-intensity periods. The mechanism 
involves insufficient neuromuscular recovery between high-load 
sessions, leaving hamstrings vulnerable during explosive movements. 
Immediate intervention: Implement mandatory recovery protocols 
for players showing ACWR > 1.2, including sleep monitoring and 
reduced training volume for 48hrs post-spike.
============================================================
```

## Customize It

### Add Your Own Analysis Nodes

Want to check GPS data? Add a new node:

```python
def analyze_gps_data(state: AgentState) -> AgentState:
    print("\n🎯 Analyzing GPS metrics...")
    
    # Your GPS analysis logic here
    high_speed_running = state['load_data']['HSR_Distance'].mean()
    
    # Ask AI to interpret
    prompt = f"GPS shows average HSR of {high_speed_running}m. Is this excessive?"
    response = llm.invoke(prompt)
    
    state['gps_analysis'] = response.content
    state['nodes_visited'].append('analyze_gps_data')
    return state

# Add to graph
workflow.add_node("check_gps", analyze_gps_data)
workflow.add_edge("analyze_load", "check_gps")
```

### Change the Routing Logic

Want different decision paths? Modify the conditional functions:

```python
def should_check_recovery(state: AgentState) -> str:
    # Your custom logic
    if state['injury_count'] > 5:
        return "emergency_protocol"
    elif state['load_correlation']:
        return "check_recovery"
    else:
        return "check_fixtures"
```

### Use Your 31-Point Surveillance System

Replace the simple ACWR check with your weighted scoring:

```python
def calculate_risk_score(player_data):
    """Your proprietary 31-point system"""
    score = 0
    
    # Example weights (use your actual algorithm)
    score += player_data['ACWR'] > 1.3 ? 15 : 0
    score += player_data['Sleep'] < 7 ? 10 : 0
    score += player_data['Wellness'] < 65 ? 8 : 0
    # ... add all 31 factors
    
    return score

# Then use in your node:
risk_scores = injuries.apply(calculate_risk_score, axis=1)
state['risk_classification'] = classify_traffic_light(risk_scores)
```

## Next Steps

1. **Run with sample data first** to understand the flow
2. **Replace with your actual data** (start with 1 month)
3. **Customize the nodes** to match your workflow
4. **Add your surveillance metrics** (TSR, GPS, RPE, etc.)
5. **Deploy as an API** or integrate into your dashboard

## Troubleshooting

**"Module not found" error:**
```bash
# Make sure you're in the virtual environment
source venv/bin/activate
pip install langgraph langchain-anthropic pandas python-dotenv
```

**"API key not found":**
- Check `.env` file exists
- Verify API key is correct
- Don't commit `.env` to git!

**Data loading errors:**
- Check CSV column names match exactly
- Ensure dates are in YYYY-MM-DD format
- Verify no empty rows

## Questions?

The code is heavily commented - read through `injury_agent.py` to understand each section.

Key concepts:
- **StateGraph** = The workflow container
- **Nodes** = Functions that do work
- **Edges** = Connections between nodes
- **Conditional edges** = AI-powered routing decisions
