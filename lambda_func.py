from utils import get_articles, publish_to_sqs

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
