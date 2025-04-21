import requests
from dotenv import load_dotenv
import os
from datetime import datetime
import boto3
import json

load_dotenv()


def get_articles(search_term, date_from=None):
    api_key = os.getenv("GUARDIAN_API_KEY")
    base_url = "https://content.guardianapis.com/search"
    
    params = {
        "q": search_term,
        "api-key": api_key,
        "page-size": 10,
        "order-by": "newest",
        "show-fields": "trailText,bodyText"
    }

    if date_from:
        params["from-date"] = date_from

    response = requests.get(base_url, params=params)
    response.raise_for_status()

    results = response.json().get("response", {}).get("results", [])
    articles = []
    for result in results:
        article = {
            "webPublicationDate": result.get("webPublicationDate"),
            "webTitle": result.get("webTitle"),
            "webUrl": result.get("webUrl"),
            "content_preview": result.get("fields", {}).get("bodyText", "")[:1000]
        }
        articles.append(article)
    print(articles)


get_articles("OpenAI", date_from="2024-04-04")