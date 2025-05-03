import requests
import os
import boto3
import json
from botocore.exceptions import ClientError
import logging
from datetime import datetime
import re

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_articles(search_term, date_from=None):
    api_key = os.environ.get('GUARDIAN_API_KEY')
    if not api_key:
        raise ValueError("GUARDIAN_API_KEY environment variable is not set")
    
    base_url = "https://content.guardianapis.com/search"
    
    params = {
        "q": f'"{search_term}"',
        "api-key": api_key,
        "show-fields": "trailText,body",
        "page-size": 10,
        "order-by": "newest"
    }
    
    if date_from:
        params["from-date"] = date_from
    
    try:
        response = requests.get(base_url, params=params, timeout=120)
        data = response.json()
        
        articles = []
        for article in data["response"]["results"]:
            title = article.get("webTitle", "")
            trail_text = article.get("fields", {}).get("trailText", "")
            body = article.get("fields", {}).get("body", "")
    
        # refine search term filtering
            if not any(re.search(rf"\b{re.escape(search_term)}\b", text, re.IGNORECASE) for text in [title, trail_text, body]):
                continue

            processed_article = {
                "webPublicationDate": article["webPublicationDate"],
                "webTitle": title,
                "webUrl": article["webUrl"],
                "summary": trail_text,
                "content_preview": body[:1000]
            }
            articles.append(processed_article)

        logger.info(f"Retrieved {len(articles)} articles for term '{search_term}'")
        return articles
    
    except Exception as e:
        logger.error(f"Error fetching articles from Guardian API: {e}")
        return []


def ensure_sqs_queue_exists(queue_name):
    sqs_client = boto3.client('sqs')
    
    try:
        response = sqs_client.get_queue_url(QueueName=queue_name)
        return response['QueueUrl']
    except ClientError as e:
        if e.response['Error']['Code'] == 'AWS.SimpleQueueService.NonExistentQueue':
            raise Exception(f"SQS queue '{queue_name}' does not exist.")
        raise


def publish_to_sqs(queue_name, articles):
    if not articles:
        return 0
    
    sqs_client = boto3.client('sqs')
    message_count = 0
    
    try:
        queue_url = ensure_sqs_queue_exists(queue_name)
        
        for article in articles:
            try:
                response = sqs_client.send_message(
                    QueueUrl=queue_url,
                    MessageBody=json.dumps(article)
                )
                if 'MessageId' in response:
                    message_count += 1
            except Exception as e:
                logger.error(f"Error sending message to SQS: {e}")
        return message_count

    except Exception as e:
        logger.error(f"Error in SQS publishing: {e}")
        return 0

def publish_to_file(articles):
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    filename = f"output_{timestamp}.json"
    try:
        with open(filename, "w") as f:
            json.dump(articles, f, indent=2)
        logger.info(f"Wrote {len(articles)} articles to local file: {filename}")
        return len(articles)
    except Exception as e:
        logger.error(f"Error writing to local file: {e}")
        return 0

def lambda_handler(event, context):
  
    search_term = event.get('search_term')
    date_from = event.get('date_from')
    queue_name = event.get('queue_name', 'guardian-content')
    
    if not search_term:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Missing required field: search_term'})
        }
    
    articles = get_articles(search_term, date_from)
    
    if not articles:
        logger.info(f"No articles found")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'No articles found'})
        }
    
    message_count = publish_to_sqs(queue_name, articles)
    logger.info(f"Successfully published {len(articles)} articles to SQS queue '{queue_name}'")
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f"{message_count} articles sent to SQS queue '{queue_name}'",
            'article_count': message_count
        })
    }


if __name__ == "__main__":
    use_sqs_input = input("Publish to AWS SQS? (y/n): ").lower().strip()
    search_term = input("Enter your search term: ").strip()
    date_from = input("Enter a start date (YYYY-MM-DD) or leave blank: ").strip() or None
    queue_name = input("Enter the SQS queue name or leave blank for local file: ").strip()

    use_sqs = use_sqs_input in ["y", "yes"]

    articles = get_articles(search_term, date_from)
    print(f"Retrieved {len(articles)} articles.")

    if articles:
        if use_sqs:
            publish_to_sqs(queue_name, articles)
        else:
            publish_to_file(articles)
    else:
        print("No articles found to publish.")