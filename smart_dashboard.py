"""
Smart Injury Investigation Agent
Upload ONE file - Agent auto-detects and extracts all data
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime
from typing import TypedDict, Annotated, Dict, List
from io import BytesIO

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER

st.set_page_config(
    page_title="NP Performance Lab - Smart Injury Investigation",
    page_icon="🏥",
    layout="wide"
)

load_dotenv()

# ============================================================================
# INTELLIGENT FILE PARSER
# ============================================================================

class DataDetector:
    """Auto-detects data types from uploaded file"""
    
    # Column patterns for detection
    INJURY_PATTERNS = ['injury', 'location', 'diagnosis', 'severity', 'mechanism', 'days_lost']
    LOAD_PATTERNS = ['acwr', 'acute', 'chronic', 'load', 'rpe', 'duration']
    GPS_PATTERNS = ['hsr', 'sprint', 'acceleration', 'deceleration', 'distance', 'gps']
    FIXTURE_PATTERNS = ['opponent', 'competition', 'result', 'match']
    RECOVERY_PATTERNS = ['sleep', 'wellness', 'soreness', 'fatigue', 'readiness']
    PLAYER_PATTERNS = ['player', 'athlete', 'name']
    DATE_PATTERNS = ['date', 'time']
    
    @staticmethod
    def detect_column_type(column_name: str) -> str:
        """Detect what type of data a column contains"""
        col_lower = column_name.lower().replace('_', '').replace(' ', '')
        
        # Check each pattern type
        if any(pattern in col_lower for pattern in DataDetector.INJURY_PATTERNS):
            return 'injury'
        elif any(pattern in col_lower for pattern in DataDetector.LOAD_PATTERNS):
            return 'load'
        elif any(pattern in col_lower for pattern in DataDetector.GPS_PATTERNS):
            return 'gps'
        elif any(pattern in col_lower for pattern in DataDetector.FIXTURE_PATTERNS):
            return 'fixture'
        elif any(pattern in col_lower for pattern in DataDetector.RECOVERY_PATTERNS):
            return 'recovery'
        elif any(pattern in col_lower for pattern in DataDetector.PLAYER_PATTERNS):
            return 'player'
        elif any(pattern in col_lower for pattern in DataDetector.DATE_PATTERNS):
            return 'date'
        else:
            return 'unknown'
    
    @staticmethod
    def analyze_dataframe(df: pd.DataFrame) -> Dict:
        """Analyze a dataframe and categorize its data"""
        column_types = {}
        for col in df.columns:
            column_types[col] = DataDetector.detect_column_type(col)
        
        # Count data types
        type_counts = {}
        for col_type in column_types.values():
            type_counts[col_type] = type_counts.get(col_type, 0) + 1
        
        # Determine primary data type
        if type_counts.get('injury', 0) >= 2:
            primary = 'injury'
        elif type_counts.get('load', 0) >= 2:
            primary = 'load'
        elif type_counts.get('gps', 0) >= 3:
            primary = 'gps'
        elif type_counts.get('fixture', 0) >= 1:
            primary = 'fixture'
        else:
            primary = 'mixed'
        
        return {
            'column_types': column_types,
            'type_counts': type_counts,
            'primary_type': primary,
            'row_count': len(df)
        }
    
    @staticmethod
    def load_file(uploaded_file) -> Dict[str, pd.DataFrame]:
        """Load file and auto-detect data structure"""
        file_ext = uploaded_file.name.split('.')[-1].lower()
        datasets = {}
        
        if file_ext == 'csv':
            # Single CSV file
            df = pd.read_csv(uploaded_file)
            analysis = DataDetector.analyze_dataframe(df)
            datasets['main'] = {
                'data': df,
                'analysis': analysis
            }
        
        elif file_ext in ['xlsx', 'xls']:
            # Excel file - check all sheets
            excel_file = pd.ExcelFile(uploaded_file)
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                if not df.empty:
                    analysis = DataDetector.analyze_dataframe(df)
                    datasets[sheet_name] = {
                        'data': df,
                        'analysis': analysis
                    }
        
        return datasets
    
    @staticmethod
    def extract_data_types(datasets: Dict) -> Dict[str, pd.DataFrame]:
        """Extract injury, load, GPS, fixture data from datasets"""
        extracted = {
            'injury': pd.DataFrame(),
            'load': pd.DataFrame(),
            'gps': pd.DataFrame(),
            'fixture': pd.DataFrame()
        }
        
        for sheet_name, dataset in datasets.items():
            df = dataset['data']
            primary = dataset['analysis']['primary_type']
            
            if primary == 'injury':
                extracted['injury'] = pd.concat([extracted['injury'], df], ignore_index=True)
            elif primary == 'load':
                extracted['load'] = pd.concat([extracted['load'], df], ignore_index=True)
            elif primary == 'gps':
                extracted['gps'] = pd.concat([extracted['gps'], df], ignore_index=True)
            elif primary == 'fixture':
                extracted['fixture'] = pd.concat([extracted['fixture'], df], ignore_index=True)
            elif primary == 'mixed':
                # Try to extract relevant columns
                col_types = dataset['analysis']['column_types']
                
                # Extract injury columns
                injury_cols = [col for col, type_ in col_types.items() if type_ in ['injury', 'recovery', 'player', 'date']]
                if len(injury_cols) >= 3:
                    extracted['injury'] = pd.concat([extracted['injury'], df[injury_cols]], ignore_index=True)
                
                # Extract load columns
                load_cols = [col for col, type_ in col_types.items() if type_ in ['load', 'player', 'date']]
                if len(load_cols) >= 3:
                    extracted['load'] = pd.concat([extracted['load'], df[load_cols]], ignore_index=True)
                
                # Extract GPS columns
                gps_cols = [col for col, type_ in col_types.items() if type_ in ['gps', 'player', 'date']]
                if len(gps_cols) >= 3:
                    extracted['gps'] = pd.concat([extracted['gps'], df[gps_cols]], ignore_index=True)
        
        return extracted

# ============================================================================
# STATE & LLM (Same as before)
# ============================================================================

class AgentState(TypedDict):
    injury_data: pd.DataFrame
    load_data: pd.DataFrame
    fixture_data: pd.DataFrame
    gps_data: pd.DataFrame
    injury_count: int
    load_correlation: bool
    load_details: str
    recovery_issue: bool
    recovery_details: str
    fixture_congestion: bool
    fixture_details: str
    gps_excessive: bool
    gps_details: str
    hypothesis_validated: bool
    confidence_score: float
    final_report: str
    nodes_visited: list
    retry_count: int
    logs: list

@st.cache_resource
def get_llm():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("⚠️ GROQ_API_KEY not found")
        st.stop()
    return ChatGroq(model="llama-3.3-70b-versatile", temperature=0, groq_api_key=api_key)

llm = get_llm()

def add_log(state, message, msg_type="info"):
    if 'logs' not in state:
        state['logs'] = []
    state['logs'].append({'msg': message, 'type': msg_type})
    return state

# ============================================================================
# AGENT NODES (Simplified - same logic as before)
# ============================================================================

def fetch_injury_data(state):
    state = add_log(state, "📊 Loading injury data...", "info")
    injuries = state['injury_data']
    
    if injuries.empty:
        state['injury_count'] = 0
        state['nodes_visited'].append('fetch')
        return state
    
    # Parse dates if available
    date_cols = [col for col in injuries.columns if 'date' in col.lower()]
    if date_cols:
        injuries[date_cols[0]] = pd.to_datetime(injuries[date_cols[0]], errors='coerce')
        max_date = injuries[date_cols[0]].max()
        min_date = max_date - pd.Timedelta(days=30)
        recent = injuries[(injuries[date_cols[0]] >= min_date) & (injuries[date_cols[0]] <= max_date)]
    else:
        recent = injuries
    
    # Filter hamstring if location column exists
    location_cols = [col for col in recent.columns if 'location' in col.lower() or 'injury' in col.lower()]
    if location_cols:
        hamstring = recent[recent[location_cols[0]].str.contains('Hamstring', case=False, na=False)]
    else:
        hamstring = recent
    
    state['injury_data'] = hamstring
    state['injury_count'] = len(hamstring)
    state = add_log(state, f"✓ Found {len(hamstring)} hamstring injuries", "success")
    
    state['nodes_visited'].append('fetch')
    return state

def analyze_load(state):
    state = add_log(state, "🏋️ Analyzing load...", "info")
    
    if state['injury_count'] == 0:
        state['load_correlation'] = False
        state['load_details'] = "No injuries"
        state['nodes_visited'].append('load')
        return state
    
    load_data = state['load_data']
    if load_data.empty:
        state['load_correlation'] = False
        state['load_details'] = "No data"
        state['nodes_visited'].append('load')
        return state
    
    # Find ACWR column
    acwr_col = next((col for col in load_data.columns if 'acwr' in col.lower()), None)
    player_col = next((col for col in load_data.columns if 'player' in col.lower() or 'id' in col.lower()), None)
    
    if not acwr_col:
        state['load_correlation'] = False
        state['load_details'] = "No ACWR column"
        state['nodes_visited'].append('load')
        return state
    
    # Get injured players
    injury_player_col = next((col for col in state['injury_data'].columns if 'player' in col.lower() or 'id' in col.lower()), None)
    if not injury_player_col or not player_col:
        state['load_correlation'] = False
        state['load_details'] = "Can't match players"
        state['nodes_visited'].append('load')
        return state
    
    injured = state['injury_data'][injury_player_col].unique()
    
    analysis = []
    for pid in injured:
        player_load = load_data[load_data[player_col] == pid]
        if not player_load.empty:
            max_acwr = player_load[acwr_col].max()
            analysis.append({'player': pid, 'acwr': max_acwr, 'spike': max_acwr > 1.25})
    
    if not analysis:
        state['load_correlation'] = False
        state['load_details'] = "No matching data"
        state['nodes_visited'].append('load')
        return state
    
    summary = "\n".join([f"{a['player']}: ACWR {a['acwr']:.2f} {'⚠️' if a['spike'] else '✓'}" for a in analysis])
    
    prompt = f"Analyze {state['injury_count']} injuries. Load: {summary}. ACWR>1.25=risk. Strong correlation? Reply: STRONG_CORRELATION or WEAK_CORRELATION"
    decision = llm.invoke(prompt).content.strip()
    
    state = add_log(state, f"  {summary.replace(chr(10), ', ')}", "data")
    state = add_log(state, f"🤖 {decision}", "ai")
    
    state['load_correlation'] = "STRONG" in decision.upper()
    state['load_details'] = summary
    state['nodes_visited'].append('load')
    return state

def analyze_gps(state):
    state = add_log(state, "🎯 Analyzing GPS...", "info")
    
    gps_data = state.get('gps_data', pd.DataFrame())
    
    if gps_data.empty:
        state['gps_excessive'] = False
        state['gps_details'] = "No data"
        state['nodes_visited'].append('gps')
        return state
    
    # Find HSR column
    hsr_col = next((col for col in gps_data.columns if 'hsr' in col.lower()), None)
    
    if hsr_col:
        avg_hsr = gps_data[hsr_col].mean()
        state = add_log(state, f"  Avg HSR: {avg_hsr:.0f}m", "data")
        
        prompt = f"HSR average {avg_hsr:.0f}m. High risk if >600m. Excessive? Reply: GPS_EXCESSIVE or GPS_NORMAL"
        decision = llm.invoke(prompt).content.strip()
        state = add_log(state, f"🤖 {decision}", "ai")
        
        state['gps_excessive'] = "EXCESSIVE" in decision.upper()
        state['gps_details'] = f"HSR {avg_hsr:.0f}m"
    else:
        state['gps_excessive'] = False
        state['gps_details'] = "No HSR column"
    
    state['nodes_visited'].append('gps')
    return state

def check_recovery(state):
    state = add_log(state, "😴 Checking recovery...", "info")
    
    injury_data = state['injury_data']
    
    sleep_col = next((col for col in injury_data.columns if 'sleep' in col.lower()), None)
    wellness_col = next((col for col in injury_data.columns if 'wellness' in col.lower()), None)
    
    if not sleep_col and not wellness_col:
        state['recovery_issue'] = False
        state['recovery_details'] = "No data"
        state['nodes_visited'].append('recovery')
        return state
    
    avg_sleep = injury_data[sleep_col].mean() if sleep_col else 7.0
    avg_wellness = injury_data[wellness_col].mean() if wellness_col else 70
    
    prompt = f"Recovery: {avg_sleep:.1f}hrs sleep, {avg_wellness:.0f} wellness. Deficient? Reply: RECOVERY_DEFICIENT or RECOVERY_ADEQUATE"
    decision = llm.invoke(prompt).content.strip()
    
    state = add_log(state, f"  {avg_sleep:.1f}hrs, {avg_wellness:.0f} wellness", "data")
    state = add_log(state, f"🤖 {decision}", "ai")
    
    state['recovery_issue'] = "DEFICIENT" in decision.upper()
    state['recovery_details'] = f"{avg_sleep:.1f}hrs, {avg_wellness:.0f}"
    state['nodes_visited'].append('recovery')
    return state

def check_fixtures(state):
    state = add_log(state, "📅 Checking fixtures...", "info")
    
    fixtures = state['fixture_data']
    count = len(fixtures)
    congested = count >= 5
    
    state = add_log(state, f"  {count} matches", "data")
    
    state['fixture_congestion'] = congested
    state['fixture_details'] = f"{count} matches"
    state['nodes_visited'].append('fixtures')
    return state

def validate(state):
    state = add_log(state, "🔍 Validating...", "info")
    
    factors = sum([
        state.get('load_correlation', False),
        state.get('recovery_issue', False),
        state.get('fixture_congestion', False),
        state.get('gps_excessive', False)
    ])
    
    prompt = f"Evidence: Load={state.get('load_correlation')}, Recovery={state.get('recovery_issue')}, Fixtures={state.get('fixture_congestion')}, GPS={state.get('gps_excessive')}. Need 2+ for HIGH. Reply: CONFIDENCE: HIGH/LOW, SCORE: 0.X"
    result = llm.invoke(prompt).content.strip()
    
    confident = "HIGH" in result.upper()
    try:
        score = float([l for l in result.split('\n') if 'SCORE' in l][0].split(':')[1].strip())
    except:
        score = 0.8 if confident else 0.4
    
    state = add_log(state, result, "ai")
    
    state['hypothesis_validated'] = confident
    state['confidence_score'] = score
    state['nodes_visited'].append('validate')
    return state

def generate_report(state):
    state = add_log(state, "📝 Generating report...", "info")
    
    prompt = f"Write 4-sentence injury report: {state['injury_count']} hamstring injuries. Load: {state.get('load_details')}. GPS: {state.get('gps_details')}. Recovery: {state.get('recovery_details')}. Include cause, mechanism, intervention."
    report = llm.invoke(prompt).content.strip()
    
    state['final_report'] = report
    state['nodes_visited'].append('report')
    state = add_log(state, "✓ Complete", "success")
    return state

def retry_node(state):
    state['retry_count'] = state.get('retry_count', 0) + 1
    state = add_log(state, "🔄 Retry...", "warning")
    return state

# ============================================================================
# ROUTING & GRAPH (Same as before)
# ============================================================================

def route_after_load(state):
    if state.get('load_correlation'):
        state = add_log(state, "→ Check GPS & recovery", "route")
        return "gps"
    else:
        state = add_log(state, "→ Check fixtures", "route")
        return "fixtures"

def route_after_validate(state):
    if state.get('hypothesis_validated') or state.get('retry_count', 0) >= 1:
        state = add_log(state, "→ Finish", "route")
        return "finish"
    else:
        state = add_log(state, "→ Retry", "route")
        return "retry"

def build_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("fetch", fetch_injury_data)
    workflow.add_node("load", analyze_load)
    workflow.add_node("gps", analyze_gps)
    workflow.add_node("recovery", check_recovery)
    workflow.add_node("fixtures", check_fixtures)
    workflow.add_node("validate", validate)
    workflow.add_node("retry", retry_node)
    workflow.add_node("report", generate_report)
    
    workflow.set_entry_point("fetch")
    workflow.add_edge("fetch", "load")
    workflow.add_conditional_edges("load", route_after_load, {"gps": "gps", "fixtures": "fixtures"})
    workflow.add_edge("gps", "recovery")
    workflow.add_edge("recovery", "validate")
    workflow.add_edge("fixtures", "validate")
    workflow.add_conditional_edges("validate", route_after_validate, {"retry": "retry", "finish": "report"})
    workflow.add_edge("retry", "fixtures")
    workflow.add_edge("report", END)
    
    return workflow.compile()

# ============================================================================
# PDF (Simplified version)
# ============================================================================

def generate_pdf_report(result, date):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    elements.append(Paragraph("NP Performance Lab - Injury Investigation", styles['Title']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Summary with colored status
    def status_text(is_risk):
        return 'HIGH RISK' if is_risk else 'NORMAL'
    
    def status_color(is_risk):
        return colors.red if is_risk else colors.green
    
    summary_data = [
        ['Injuries Found:', str(result.get('injury_count', 0))],
        ['Analysis Confidence:', f"{result.get('confidence_score', 0)*100:.0f}%"],
        ['Load Pattern:', status_text(result.get('load_correlation', False))],
        ['GPS Metrics:', status_text(result.get('gps_excessive', False))],
        ['Recovery Status:', status_text(result.get('recovery_issue', False))],
    ]
    
    table = Table(summary_data, colWidths=[2.5*inch, 3.5*inch])
    
    # Apply colors to status cells
    table_style = [
        ('GRID', (0,0), (-1,-1), 1, colors.grey),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('PADDING', (0,0), (-1,-1), 8),
    ]
    
    # Color the status cells
    if result.get('load_correlation'):
        table_style.append(('BACKGROUND', (1,2), (1,2), colors.Color(1, 0.8, 0.8)))
        table_style.append(('TEXTCOLOR', (1,2), (1,2), colors.red))
        table_style.append(('FONTNAME', (1,2), (1,2), 'Helvetica-Bold'))
    else:
        table_style.append(('BACKGROUND', (1,2), (1,2), colors.Color(0.8, 1, 0.8)))
        table_style.append(('TEXTCOLOR', (1,2), (1,2), colors.green))
    
    if result.get('gps_excessive'):
        table_style.append(('BACKGROUND', (1,3), (1,3), colors.Color(1, 0.8, 0.8)))
        table_style.append(('TEXTCOLOR', (1,3), (1,3), colors.red))
        table_style.append(('FONTNAME', (1,3), (1,3), 'Helvetica-Bold'))
    else:
        table_style.append(('BACKGROUND', (1,3), (1,3), colors.Color(0.8, 1, 0.8)))
        table_style.append(('TEXTCOLOR', (1,3), (1,3), colors.green))
    
    if result.get('recovery_issue'):
        table_style.append(('BACKGROUND', (1,4), (1,4), colors.Color(1, 0.8, 0.8)))
        table_style.append(('TEXTCOLOR', (1,4), (1,4), colors.red))
        table_style.append(('FONTNAME', (1,4), (1,4), 'Helvetica-Bold'))
    else:
        table_style.append(('BACKGROUND', (1,4), (1,4), colors.Color(0.8, 1, 0.8)))
        table_style.append(('TEXTCOLOR', (1,4), (1,4), colors.green))
    
    table.setStyle(TableStyle(table_style))
    elements.append(table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Report
    elements.append(Paragraph("Report", styles['Heading2']))
    elements.append(Paragraph(result.get('final_report', ''), styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

# ============================================================================
# STREAMLIT UI
# ============================================================================

st.title("🧠 Smart Injury Investigation Agent")
st.markdown("**Upload ONE file** - Agent auto-detects and extracts all data types")

# File upload
uploaded_file = st.file_uploader(
    "📁 Upload your data file (CSV or Excel)",
    type=['csv', 'xlsx', 'xls'],
    help="Upload a single file with injury, load, GPS, or fixture data. Agent will auto-detect everything!"
)

if uploaded_file:
    st.success("✅ File uploaded successfully!")
    
    # Parse file
    with st.spinner("🔍 Analyzing file structure..."):
        uploaded_file.seek(0)
        datasets = DataDetector.load_file(uploaded_file)
        extracted = DataDetector.extract_data_types(datasets)
    
    # Show detection results
    st.subheader("🔍 Auto-Detection Results")
    
    cols = st.columns(4)
    with cols[0]:
        injury_count = len(extracted['injury'])
        st.metric("Injury Data", f"{injury_count} rows", "✓" if injury_count > 0 else "✗")
    with cols[1]:
        load_count = len(extracted['load'])
        st.metric("Load Data", f"{load_count} rows", "✓" if load_count > 0 else "✗")
    with cols[2]:
        gps_count = len(extracted['gps'])
        st.metric("GPS Data", f"{gps_count} rows", "✓" if gps_count > 0 else "✗")
    with cols[3]:
        fixture_count = len(extracted['fixture'])
        st.metric("Fixture Data", f"{fixture_count} rows", "✓" if fixture_count > 0 else "✗")
    
    # Show detected sheets/data
    with st.expander("📊 Detected Data Structure"):
        for name, dataset in datasets.items():
            analysis = dataset['analysis']
            st.write(f"**{name}** - {analysis['primary_type'].upper()} data ({analysis['row_count']} rows)")
            st.write(f"Columns: {', '.join(list(dataset['data'].columns)[:10])}")
    
    # Preview extracted data
    with st.expander("👀 Data Preview"):
        tab1, tab2, tab3, tab4 = st.tabs(["Injury", "Load", "GPS", "Fixtures"])
        
        with tab1:
            if not extracted['injury'].empty:
                st.dataframe(extracted['injury'].head(), use_container_width=True)
            else:
                st.info("No injury data detected")
        
        with tab2:
            if not extracted['load'].empty:
                st.dataframe(extracted['load'].head(), use_container_width=True)
            else:
                st.info("No load data detected")
        
        with tab3:
            if not extracted['gps'].empty:
                st.dataframe(extracted['gps'].head(), use_container_width=True)
            else:
                st.info("No GPS data detected")
        
        with tab4:
            if not extracted['fixture'].empty:
                st.dataframe(extracted['fixture'].head(), use_container_width=True)
            else:
                st.info("No fixture data detected")
    
    # Run investigation
    if st.button("▶️ Run Investigation", type="primary", use_container_width=True):
        initial_state = {
            'injury_data': extracted['injury'],
            'load_data': extracted['load'],
            'gps_data': extracted['gps'],
            'fixture_data': extracted['fixture'],
            'nodes_visited': [],
            'retry_count': 0,
            'logs': []
        }
        
        with st.spinner("🤖 Agent analyzing..."):
            app = build_graph()
            result = app.invoke(initial_state)
        
        st.session_state['result'] = result
        st.session_state['date'] = datetime.now()
        
        # Results
        st.success("✅ Analysis Complete!")
        
        # Execution log
        with st.expander("📋 Execution Log", expanded=True):
            for log in result.get('logs', []):
                if log['type'] == 'success':
                    st.success(log['msg'])
                elif log['type'] == 'ai':
                    st.info(f"🤖 {log['msg']}")
                else:
                    st.text(log['msg'])
        
        # Metrics
        st.subheader("📊 Results")
        cols = st.columns(5)
        with cols[0]:
            st.metric("Injuries", result.get('injury_count', 0))
        with cols[1]:
            st.metric("Confidence", f"{result.get('confidence_score', 0)*100:.0f}%")
        with cols[2]:
            st.metric("Load", "🔴" if result.get('load_correlation') else "🟢")
        with cols[3]:
            st.metric("GPS", "🔴" if result.get('gps_excessive') else "🟢")
        with cols[4]:
            st.metric("Recovery", "🔴" if result.get('recovery_issue') else "🟢")
        
        # Report
        st.markdown("### 📝 Investigation Report")
        st.info(result.get('final_report', ''))
        
        # PDF Download
        pdf = generate_pdf_report(result, st.session_state['date'])
        st.download_button(
            "📄 Download PDF Report",
            pdf,
            f"investigation_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            "application/pdf",
            type="primary",
            use_container_width=True
        )

else:
    st.info("👆 Upload a file to get started")
    
    st.markdown("### 📚 Supported File Formats:")
    st.markdown("""
    - **CSV** - Single file with all data
    - **Excel (.xlsx)** - Multiple sheets (e.g., Injuries, Load, GPS, Fixtures)
    
    ### 🔍 Auto-Detection:
    The agent automatically detects:
    - Injury data (columns: Location, Injury, Severity, Sleep, Wellness)
    - Load data (columns: ACWR, Load, RPE, Duration)
    - GPS data (columns: HSR, Sprint, Acceleration)
    - Fixture data (columns: Opponent, Competition, Result)
    
    No need to format perfectly - agent adapts to your column names!
    """)

st.markdown("---")
st.markdown("Built with LangGraph • NP Performance Lab")
