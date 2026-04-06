# 🔍 NP Performance Lab - Injury Investigation Agent

**AI-powered injury cluster analysis for football academies**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](YOUR_DEPLOYED_URL_HERE)

---

## 🎯 What It Does

Analyzes injury patterns and identifies root causes automatically using AI:

- **Upload** your injury/load/GPS data (single Excel file or CSV)
- **Investigates** injury clusters using LangGraph multi-agent workflow
- **Identifies** root causes: excessive load, GPS metrics, poor recovery, fixture congestion
- **Generates** professional PDF reports in minutes

**Traditional approach:** 2+ hours of manual analysis  
**This agent:** 2 minutes, automated

---

## ✨ Features

### 🤖 Intelligent Workflow
- **Conditional routing**: Agent chooses analysis paths based on findings
- **Retry mechanism**: Loops back when confidence is low
- **Multi-factor analysis**: ACWR, GPS (HSR, sprint count), recovery (sleep, wellness), fixture density

### 📊 Smart File Detection
- **Auto-detection**: Recognizes injury/load/GPS data from any column names
- **Single upload**: Handles multi-sheet Excel or combined CSV
- **Flexible format**: Works with UEFA templates or custom structures

### 📄 Professional Reports
- **PDF generation**: Branded reports with color-coded risk indicators
- **Executive summary**: Injury count, confidence score, flagged factors
- **Actionable insights**: AI-generated recommendations for prevention

---

## 🚀 Quick Start

### 1. Get Your Groq API Key (Free)

This agent uses **Groq** for fast, free AI inference:

1. Go to **https://console.groq.com**
2. Sign up (free account)
3. Navigate to **API Keys**
4. Click **"Create API Key"**
5. Copy your key (starts with `gsk_...`)

**Why Groq?**
- ✅ Free tier: 14,400 requests/day
- ✅ Fast inference (Llama 3.3-70B)
- ✅ No credit card required
- ✅ Production-ready

### 2. Installation

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/np-injury-investigation.git
cd np-injury-investigation

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "GROQ_API_KEY=your_actual_key_here" > .env
```

### 3. Run the Agent

```bash
streamlit run smart_dashboard.py
```

Open **http://localhost:8501** in your browser

### 4. Upload Data

Upload any of:
- Multi-sheet Excel file (injuries, load, GPS, fixtures)
- Single CSV with combined data
- Separate CSVs (auto-detected)

**Sample data included:** `master_surveillance_data.xlsx`

---

## 📁 Data Format

The agent auto-detects columns. It looks for:

### Injury Data
- Player ID/Name
- Injury Date
- Injury Type
- Body Part

### Load Data
- Player ID
- Date
- ACWR (Acute:Chronic Workload Ratio)

### GPS Data
- Player ID
- Date
- HSR Distance (m)
- Sprint Count
- Max Speed (km/h)

### Recovery Data
- Player ID
- Sleep Hours
- Wellness Score
- Muscle Soreness

### Fixture Data
- Match Date
- Competition
- Opponent

**Column names can vary** - the agent matches patterns like "player", "name", "id", etc.

---

## 🧠 How It Works

### LangGraph Architecture

```
User Upload
    ↓
fetch_injury_data
    ↓
analyze_load ──→ ACWR correlation?
    ↓                 ↓
  HIGH           WEAK/MODERATE
    ↓                 ↓
check_recovery   check_fixtures
    ↓                 ↓
validate ←──────────────┘
    ↓
confidence > 60%?
    ↓
  YES ──→ generate_report
    ↓
   NO ──→ retry (loop back)
```

### Decision Points

**Node: analyze_load**
- If ACWR correlation is STRONG → Check recovery data
- If WEAK → Check fixture congestion

**Node: validate**
- If confidence ≥60% → Generate report
- If <60% → Retry with more evidence

**Node: generate_report**
- AI synthesizes all findings
- Creates PDF with recommendations

---

## 🛠️ Tech Stack

- **LangGraph** - Multi-agent workflow orchestration
- **Groq** - Free, fast LLM inference (Llama 3.3-70B)
- **Streamlit** - Web interface
- **ReportLab** - PDF generation
- **Pandas** - Data processing

---

## 📊 Sample Output

**PDF Report Includes:**
- Executive summary (injury count, confidence, risk factors)
- Color-coded indicators (🔴 High Risk / 🟢 Normal)
- Root cause analysis
- Prevention recommendations
- Execution log

---

## 🔧 Configuration

### Adjust ACWR Thresholds

Edit in `smart_dashboard.py`:

```python
STRONG_CORRELATION = 1.25  # ACWR threshold for "strong" risk
WEAK_CORRELATION = 1.15    # Below this = weak correlation
```

### Customize Report Branding

```python
# PDF header
doc = SimpleDocTemplate(buffer, pagesize=A4)
elements.append(Paragraph("Your Academy Name", styles['Title']))
```

---

## 🐛 Troubleshooting

### "Module not found" error
```bash
pip install -r requirements.txt
```

### "API key not found"
- Check `.env` file exists
- Verify `GROQ_API_KEY=gsk_...` format
- Restart Streamlit

### File upload fails
- Max file size: 200MB
- Supported: CSV, XLSX, XLS
- Check file isn't corrupted

### PDF colors not showing
- Already fixed in latest version
- Update `smart_dashboard.py` if using old version

---

## 📈 Real-World Results

**U17 Football Academy (4 months):**
- 30% reduction in muscular injuries
- Weekly report time: 2 hours → 2 minutes
- Earlier identification of high-risk clusters

---

## 🤝 Contributing

This is a portfolio/research project. Feedback welcome!

**Contact:** [Your LinkedIn/Email]

---

## 📄 License

MIT License - Free for personal and commercial use

---

## 🙏 Credits

Built by **Nitesh Patel** (www.linkedin.com/in/niteshppatel)

**Research foundation:**
- LaLiga injury risk model
- Gabbett TJ (2016) - Training-injury prevention paradox
- Bengtsson H et al. (2013) - Fixture congestion research

**Powered by:**
- [Groq](https://groq.com) - Free AI inference
- [LangGraph](https://langchain-ai.github.io/langgraph/) - Agent framework
- [Streamlit](https://streamlit.io) - Web deployment

---

## 🚀 Live Demo

Try it yourself: **[YOUR_DEPLOYED_URL]**

Sample data included - upload and run!

---

**Built with LangGraph • Powered by Groq • NP Performance Lab**
