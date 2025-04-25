from src.lambda_func import lambda_handler
from unittest.mock import patch


def test_lambda_handler_success():
    event = {
        "search_term": "OpenAI",
        "date_from": "2024-01-01",
        "queue_name": "guardian-content"
    }

    mock_articles = [{"webTitle": "AI article", "webUrl": "...", "webPublicationDate": "...", "content_preview": "..."}]

    with patch("src.lambda_func.get_articles", return_value=mock_articles) as mock_get, \
         patch("src.lambda_func.publish_to_sqs") as mock_publish:

        response = lambda_handler(event, context={})

        mock_get.assert_called_once_with("OpenAI", "2024-01-01")
        mock_publish.assert_called_once_with("guardian-content", mock_articles)

        assert response["statusCode"] == 200
        assert "articles sent to SQS" in response["body"]


def test_lambda_handler_missing_search_term():
    event = {
        "date_from": "2024-01-01",
        "queue_name": "guardian-content"
    }

    response = lambda_handler(event, context={})

    assert response["statusCode"] == 400
    assert "Missing required field" in response["body"]
