from src.app import get_articles, publish_to_file, publish_to_sqs


def main():
    """Main function to run module as a standalone script for local testing"""

    use_sqs_input = input("Publish to AWS SQS? (y/n): ").lower().strip()
    search_term = input("Enter your search term: ").strip()
    date_from = (
        input("Enter a start date (YYYY-MM-DD) or leave blank: ").strip() or None
    )
    queue_name = input(
        "Enter the SQS queue name or leave blank for local file: "
    ).strip()
    use_sqs = use_sqs_input in ["y", "yes"]
    articles = get_articles(search_term, date_from)

    if len(articles) > 0:
        print(f"Retrieved {len(articles)} articles.")
        if use_sqs:
            publish_to_sqs(queue_name, articles)
        else:
            publish_to_file(articles)
    else:
        print("No articles found to publish.")


if __name__ == "__main__":
    main()
