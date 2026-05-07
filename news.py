import requests 
from bs4 import BeautifulSoup
import pandas as pd
import aiohttp
import asyncio
import nest_asyncio
import json
import os
from nltk.sentiment.vader import SentimentIntensityAnalyzer


nest_asyncio.apply()

class NewsData():
    def __init__(self):
        self.sia = SentimentIntensityAnalyzer()
        self.text_crynews=''
        self.text_reddit=''

    async def fetch(self, url, headers=None):
        # create HTTP session
        async with aiohttp.ClientSession() as session:
            # make GET request using session
            async with session.get(url, headers=headers) as response:
                # return text content
                return await response.text()
            
    async def main(self):
        newsdata_api_key = None
        cmc_api_key = None
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r") as f:
                    config = json.load(f)
                    key = config.get("NEWSDATA_API_KEY", "")
                    if key and key != "YOUR_NEWSDATA_API_KEY_HERE":
                        newsdata_api_key = key
                    cmc_key = config.get("COINMARKETCAP_API_KEY", "")
                    if cmc_key and cmc_key != "YOUR_CMC_API_KEY_HERE":
                        cmc_api_key = cmc_key
            except Exception:
                pass
                
        async def _safe_fetch(url, headers=None):
            if url:
                try:
                    return await self.fetch(url, headers)
                except Exception:
                    return None
            return None

        url1 = 'https://www.reddit.com/r/CryptoCurrency/new/'
        url2 = 'https://crypto.news/tag/bitcoin/'
        url3 = f'https://newsdata.io/api/1/news?apikey={newsdata_api_key}&q=bitcoin&language=en' if newsdata_api_key else None
        url4 = 'https://pro-api.coinmarketcap.com/v1/content/latest' if cmc_api_key else None
        headers4 = {"X-CMC_PRO_API_KEY": cmc_api_key} if cmc_api_key else None
        url_coindesk = "https://www.coindesk.com/arc/outboundfeeds/rss/"
        url_cointelegraph = "https://cointelegraph.com/rss"
        url_cryptopotato = "https://cryptopotato.com/feed/"
        
        results = await asyncio.gather(
            _safe_fetch(url1),
            _safe_fetch(url2),
            _safe_fetch(url3),
            _safe_fetch(url4, headers4),
            _safe_fetch(url_coindesk),
            _safe_fetch(url_cointelegraph),
            _safe_fetch(url_cryptopotato)
        )
        
        requests_reddit = results[0]
        requests_crynews = results[1]
        requests_newsdata = results[2]
        requests_cmc = results[3]
        requests_coindesk = results[4]
        requests_cointelegraph = results[5]
        requests_cryptopotato = results[6]

        news_items = []
        all_texts_map = {}

        # 1. Scrape HTML sources
        acc_reddit = ""
        if requests_reddit:
            soup_reddit = BeautifulSoup(requests_reddit, 'html.parser')
            content_reddit = soup_reddit.find_all(class_='absolute inset-0')
            for items_reddit in content_reddit[-10:]:
                text = items_reddit.get_text(separator=' ',strip=True)
                acc_reddit += text + '\n\n'
                if text.strip():
                    score = self.sia.polarity_scores(text)['compound']
                    sentiment = "positive" if score > 0.05 else "negative" if score < -0.05 else "neutral"
                    news_items.append({
                        "source": "Reddit",
                        "title": text[:50] + "..." if len(text) > 50 else text,
                        "body": text[:150] + "..." if len(text) > 150 else text,
                        "time": "Yeni",
                        "sentiment": sentiment,
                        "compound": score
                    })
        all_texts_map["Reddit"] = acc_reddit

        acc_crynews = ""
        if requests_crynews:
            soup_crynews = BeautifulSoup(requests_crynews, 'html.parser')
            content_crynews = soup_crynews.find_all(class_='post-loop__link')
            for items in content_crynews[-10:]:
                text = items.get_text(separator=' ',strip=True)
                acc_crynews += text + '\n\n'
                if text.strip():
                    score = self.sia.polarity_scores(text)['compound']
                    sentiment = "positive" if score > 0.05 else "negative" if score < -0.05 else "neutral"
                    news_items.append({
                        "source": "CryptoNews",
                        "title": text[:50] + "..." if len(text) > 50 else text,
                        "body": text[:150] + "..." if len(text) > 150 else text,
                        "time": "Yeni",
                        "sentiment": sentiment,
                        "compound": score
                    })
        all_texts_map["CryptoNews"] = acc_crynews

        # 2. Parse RSS sources
        def parse_rss(html_content, source_name):
            acc_text = ""
            if html_content:
                soup = BeautifulSoup(html_content, 'html.parser')
                for item in soup.find_all('item')[:10]:
                    title = item.title.text if item.title else ""
                    desc = item.description.text if item.description else ""
                    title = title.replace("<![CDATA[", "").replace("]]>", "")
                    desc = desc.replace("<![CDATA[", "").replace("]]>", "")
                    desc = BeautifulSoup(desc, 'html.parser').get_text(separator=' ', strip=True)
                    text = f"{title}. {desc}"
                    acc_text += text + "\n\n"
                    if text.strip():
                        score = self.sia.polarity_scores(text)['compound']
                        sentiment = "positive" if score > 0.05 else "negative" if score < -0.05 else "neutral"
                        news_items.append({
                            "source": source_name,
                            "title": title[:50] + "..." if len(title) > 50 else title,
                            "body": desc[:150] + "..." if len(desc) > 150 else desc,
                            "time": "Yeni",
                            "sentiment": sentiment,
                            "compound": score
                        })
            return acc_text

        all_texts_map["CoinDesk"] = parse_rss(requests_coindesk, "CoinDesk")
        all_texts_map["CoinTelegraph"] = parse_rss(requests_cointelegraph, "CoinTelegraph")
        all_texts_map["CryptoPotato"] = parse_rss(requests_cryptopotato, "CryptoPotato")

        # 3. Parse JSON sources
        def parse_json(json_str, source_name, is_cmc=False):
            acc_text = ""
            if json_str:
                try:
                    data = json.loads(json_str)
                    articles = data.get("data", []) if is_cmc else data.get("results", [])
                    for item in articles[:10]:
                        title = item.get("title", "") or ""
                        if is_cmc:
                            desc = item.get("subtitle", "") or item.get("content", "") or ""
                        else:
                            desc = item.get("description", "") or ""
                        text = f"{title}. {desc}"
                        acc_text += text + "\n\n"
                        if text.strip():
                            score = self.sia.polarity_scores(text)['compound']
                            sentiment = "positive" if score > 0.05 else "negative" if score < -0.05 else "neutral"
                            news_items.append({
                                "source": source_name,
                                "title": title[:50] + "..." if len(title) > 50 else title,
                                "body": desc[:150] + "..." if len(desc) > 150 else desc,
                                "time": "Yeni",
                                "sentiment": sentiment,
                                "compound": score
                            })
                except Exception:
                    pass
            return acc_text

        all_texts_map["NewsData.io"] = parse_json(requests_newsdata, "NewsData.io", False)
        all_texts_map["CoinMarketCap"] = parse_json(requests_cmc, "CoinMarketCap", True)

        # 4. Global Sentiments
        total_compound, total_pos, total_neu, total_neg = 0, 0, 0, 0
        valid_sources = 0
        all_combined_text = ""
        
        for source_name, text in all_texts_map.items():
            if text and text.strip():
                valid_sources += 1
                scores = self.sia.polarity_scores(text)
                total_compound += scores['compound']
                total_pos += scores['pos']
                total_neu += scores['neu']
                total_neg += scores['neg']
                all_combined_text += text + "\n\n"
                
        if valid_sources == 0:
            valid_sources = 1

        return (
            total_compound / valid_sources,
            total_pos / valid_sources,
            total_neu / valid_sources,
            total_neg / valid_sources,
            all_combined_text,
            news_items
        )
        
    def run(self):
        return asyncio.run(self.main())       

if __name__ == "__main__":
    newsdata = NewsData()
    newsdata.run()