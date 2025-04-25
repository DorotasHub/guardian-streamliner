import requests
import os
import boto3
import json

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
    return articles


def ensure_queue_exists(queue_name):
    sqs = boto3.client("sqs")
    try:
        response = sqs.get_queue_url(QueueName=queue_name)
        return response["QueueUrl"]
    except sqs.exceptions.QueueDoesNotExist:
        response = sqs.create_queue(QueueName=queue_name)
        return response["QueueUrl"]


def publish_to_sqs(queue_name, articles):
    sqs = boto3.client("sqs")
    queue_url = ensure_queue_exists(queue_name)

    for article in articles:
        message_body = json.dumps(article)
        response = sqs.send_message(QueueUrl=queue_url, MessageBody=message_body)
        print(f"Sent message ID: {response['MessageId']}")
