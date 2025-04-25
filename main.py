from dotenv import load_dotenv
import argparse
from utils import get_articles, publish_to_sqs

load_dotenv()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch and publish Guardian articles to SQS.")
    parser.add_argument("search_term", help="Search term to query The Guardian API")
    parser.add_argument("--date_from", help="Optional start date in YYYY-MM-DD format")
    parser.add_argument("--queue_name", default="guardian-content", help="Name of the SQS queue")

    args = parser.parse_args()

    articles = get_articles(args.search_term, args.date_from)
    print(f"Retrieved {len(articles)} articles.")

    if articles:
        publish_to_sqs(args.queue_name, articles)


    args = parser.parse_args()

    articles = get_articles(args.search_term, args.date_from)
    print(f"Retrieved {len(articles)} articles.")

    if articles:
        publish_to_sqs(args.queue_name, articles)