# 📈 Bitcoin News Analyzer

A desktop application that collects Bitcoin and cryptocurrency news in real-time from multiple sources and performs AI-powered **Sentiment Analysis** — all wrapped in a modern, sleek Tkinter interface.

<img width="1482" height="845" alt="Ekran görüntüsü 2026-05-07 223847" src="https://github.com/user-attachments/assets/79b59c1c-7212-48a6-a7d1-ba5395f6c147" />

## 🌟 Features

- **Multi-Source News Feed:** Simultaneously pulls data from free, unlimited RSS feeds (CoinDesk, CoinTelegraph, CryptoPotato) as well as Reddit and CryptoNews.
- **API Support:** Extensible architecture supporting NewsData.io and CoinMarketCap news APIs.
- **VADER Sentiment Analysis:** Every article is instantly classified as **Positive**, **Negative**, or **Neutral** using NLP.
- **Async Architecture:** Data is fetched in the background using `aiohttp` and `threading` — the UI never freezes.
- **Dynamic Charts:**
  - **Sentiment Distribution (Pie Chart):** Shows the overall market mood ratio.
  - **Source Distribution (Bar Chart):** Displays how many articles came from each source.
  - **Trend Line (Line Chart):** Visualizes the sentiment shift across recent articles.
- **News Filtering:** Click any source button (e.g. "CoinTelegraph") to instantly filter the feed.
- **Secure API Management:** All API keys are stored in a local `config.json` file that is excluded from git.

## 🛠 Installation

Python 3.8 or higher is recommended.

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **NLTK setup:**
   The VADER sentiment lexicon will be downloaded automatically on first run.

3. **(Optional) Add API Keys:**
   If you want to use NewsData.io or CoinMarketCap, create a `config.json` in the root directory:
   ```json
   {
       "NEWSDATA_API_KEY": "YOUR_KEY_HERE",
       "COINMARKETCAP_API_KEY": "YOUR_KEY_HERE"
   }
   ```
   *(This file is listed in `.gitignore` and will never be uploaded to GitHub.)*

4. **Run the app:**
   ```bash
   python new_gui.py
   ```

## 🏗 Tech Stack

| Layer | Technology |
|---|---|
| GUI | Tkinter (built-in Python) |
| HTTP Requests | `aiohttp` (async) |
| HTML/RSS Parsing | `BeautifulSoup4` |
| NLP / Sentiment | `nltk` (VADER) |
| Async Management | `asyncio`, `nest_asyncio`, `threading` |

## 🤝 Contributing

This project is open for contributions. To add a new news source, simply update the URL list in `news.py` — the entire UI (buttons, charts) will **automatically adapt** to the new source without any additional changes.
