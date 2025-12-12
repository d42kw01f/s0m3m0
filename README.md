
# s0m3m0

**s0m3m0** is an experimental AI-driven system that scrapes publicly available social media content, processes it using NLP techniques, and generates analytical insights and predictions. The project is designed as a modular research prototype combining data collection, preprocessing, and AI-based analysis, with a lightweight dashboard for visualisation.

> **Note**: Trained models are intentionally excluded from this repository.

---

## Project Overview

The system follows a simple pipeline:

1. **Data Collection**  
   Scrapes publicly accessible social media content using automated browser-based and API-driven scrapers.

2. **Preprocessing & Translation**  
   Cleans, normalises, and translates multilingual content into a unified format for analysis.

3. **AI / NLP Processing**  
   Applies natural language processing and classification logic to extract signals and generate predictions.

4. **Visualisation**  
   Displays aggregated statistics and insights via a minimal frontend dashboard.

---

## Repository Structure

```text
s0m3m0/
├── backend/
│   ├── app.py                 # Main backend entry point
│   ├── database.py            # Database connection & helpers
│   ├── politicalPredictor.py  # Core prediction logic
│   ├── imageDownloader.py     # Image fetching utilities
│   ├── prediction/            # NLP processing modules
│   │   ├── the_poli.py
│   │   ├── translator.py
│   │   └── fb_processor.py
│   └── archive/               # Experimental / legacy code
│
├── scrapers/
│   ├── facebook-scraper/      # Puppeteer / Node.js based scraper
│   └── esana-scraper/         # News scraping module
│
├── frontend/
│   ├── dashboard.py           # Data visualisation dashboard
│   ├── cal_stats.py
│   └── total_candidate.py
│
├── .gitignore
├── .gitattributes
└── README.md
````

---

## Tech Stack

### Backend
- Python
- Flask (API layer)
- NLP utilities (custom pipelines)
- SQLite / lightweight DB (configurable)
    

### Scraping
- Node.js
- Puppeteer (browser automation)
- TypeScript (Facebook scraper)

### Frontend

- Python-based dashboard (data visualisation & statistics)

---

## Setup & Usage

### Prerequisites

- Python 3.9+
- Node.js 18+
- npm / yarn
- Git

---

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

---

### Scraper Setup (example: Facebook scraper)
```bash
cd scrapers/facebook-scraper
npm install
npm run build
npm start
```

---

## Models & Data

- Trained AI models are **not included** in this repository.
- The `models/` directory is intentionally ignored via `.gitignore`.
- Generated outputs, scraped media, and runtime data are excluded.
    
If you want to run predictions, you must supply your own trained models.

---

## Ethics & Disclaimer

This project is intended **strictly for research and educational purposes**.

- Only publicly available data should be processed.
- Respect platform terms of service.
- Do not use this system for surveillance, profiling, or harmful decision-making.
    

---

## Future Improvements

- Model versioning and experiment tracking
- Dockerised deployment
- API authentication & rate limiting
- Enhanced dashboard (web-based UI)
- Automated retraining pipeline
    

---

## License

This project is currently unlicensed.  
You are free to explore and study the code, but **reuse and redistribution are restricted** unless explicitly permitted by the author.

---

## Author

**Dakshitha Navodya Perera**  
AI • Cybersecurity • Data Engineering  
Sri Lanka
