import requests
import os
import boto3
import json


def get_articles(search_term, date_from=None):
    api_key = os.getenv("GUARDIAN_API_KEY")
    base_url = "https://content.guardianapis.com/search"

    params = {
        "q": f'"{search_term}"',
        "api-key": api_key,
        "page-size": 5,
        "order-by": "relevance",
        "query-fields": "headline,body",
        "show-fields": "trailText,body"
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
            "summary": result.get("fields", {}).get("trailText", "")[:1000],
            "content_preview": result.get("fields", {}).get("body", "")[:1000]
        }
        articles.append(article)
    return articles

def ensure_sqs_queue_exists(queue_name):
    sqs = boto3.client("sqs")
    try:
        response = sqs.get_queue_url(QueueName=queue_name)
        return response["QueueUrl"]
    except sqs.exceptions.QueueDoesNotExist:
        raise Exception(f"SQS queue '{queue_name}' does not exist.")


def publish_to_sqs(queue_name, articles):
    sqs = boto3.client("sqs")
    queue_url = ensure_sqs_queue_exists(queue_name)

    for article in articles:
        message_body = json.dumps(article)
        response = sqs.send_message(QueueUrl=queue_url, MessageBody=message_body)
        print(f"Sent message ID: {response['MessageId']}")


def lambda_handler(event, context):
    search_term = event.get("search_term")
    if not search_term:
        return {
            "statusCode": 400,
            "body": "Missing required field: search_term"
        }

    date_from = event.get("date_from")
    queue_name = event.get("queue_name", "guardian-content")

    articles = get_articles(search_term, date_from)
    if articles:
        publish_to_sqs(queue_name, articles)

    return {
        "statusCode": 200,
        "body": f"{len(articles)} articles sent to SQS"
    }


if __name__ == "__main__":
    search_term = input("Enter your search term: ")
    date_from = input("Enter a start date (YYYY-MM-DD) or leave blank: ").strip() or None
    queue_name = input("Enter the SQS queue name: ")

    articles = get_articles(search_term, date_from)

    print(f"\nRetrieved {len(articles)} articles.")

    if articles:
        # print(articles)
        publish_to_sqs(queue_name, articles)
        print(f"\nSuccessfully published {len(articles)} articles to SQS queue '{queue_name}'.")
    else:
        print("\nNo articles found to publish.")
