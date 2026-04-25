# AI Data Analyst

A powerful, beautiful **no-code data analytics web app** built with Streamlit. Upload any CSV or Excel file and instantly get:

- **Auto Data Cleaning** — dates, duplicates, casing, currencies
- **KPI Dashboard** — key metrics auto-detected from your data
- **Interactive Charts** — 8+ auto-generated visualizations
- **Ask Your Data** — plain English questions, no SQL needed
- **Outlier Detection** — IQR-based anomaly flagging

**No API key required. Completely free to run.**

---

## 🚀 Deploy to Streamlit Cloud (Free)

1. Fork this repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Select this repo → `app.py` as the main file
5. Click **Deploy** — done!

---

## 💻 Run Locally

```bash
git clone https://github.com/YOUR_USERNAME/datasense-ai
cd datasense-ai
pip install -r requirements.txt
streamlit run app.py
```

---

## 📁 Project Structure

```
datasense-ai/
├── app.py                  # Main app entry point
├── requirements.txt
├── .streamlit/
│   └── config.toml         # Dark theme config
├── styles/
│   └── main.css            # Custom styling
├── tabs/
│   ├── upload_tab.py       # File upload
│   ├── clean_tab.py        # Data cleaning
│   ├── kpi_tab.py          # KPI cards
│   ├── dashboard_tab.py    # Charts dashboard
│   └── chat_tab.py         # NL question answering
└── utils/
    ├── session.py          # Session state management
    ├── cleaner.py          # Data cleaning logic
    ├── kpi_engine.py       # KPI computation
    ├── chart_builder.py    # Plotly chart generation
    └── nlq_engine.py       # Natural language query engine
```

---

## 🎯 Supported File Types

| Format | Extension |
|--------|-----------|
| CSV    | .csv      |
| Excel  | .xlsx, .xls |

Max file size: **200 MB**

---

## 💬 Example Questions You Can Ask

- *"How many rows are in the dataset?"*
- *"What is the total revenue?"*
- *"Show me the top 5 by sales"*
- *"Group by region and show totals"*
- *"Are there missing values?"*
- *"What are the unique categories?"*
- *"Show trends over time"*
- *"Find duplicates"*

---

## 🛠️ Tech Stack

- **Streamlit** — UI framework
- **Pandas** — Data processing
- **Plotly** — Interactive charts
- **NumPy** — Numerical operations
- **Pure Python NLQ** — No LLM API needed

---

## 📄 License

MIT License — free to use, modify, and deploy.
