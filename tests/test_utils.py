import pytest
from unittest.mock import patch, MagicMock
from src.utils import get_articles, publish_to_sqs

@pytest.fixture
def sample_guardian_response():
    return {
        "response": {
            "results": [
                {
                    "webPublicationDate": "2024-04-05T12:34:56Z",
                    "webTitle": "Test Article",
                    "webUrl": "https://www.theguardian.com/us-news/2025/apr/05/test-article",
                    "fields": {
                        "bodyText": (
                            "Hakuna Matata! It means no worries, for the rest of your days. "
                            "Just keep swimming, just keep swimming. "
                            "To infinity and beyond!"
                            "Ohana means family, and family means nobody gets left behind. "
                            "Second star to the right and straight on till morning. "
                            "Adventure is out there! Some people are worth melting for. "
                            "A dream is a wish your heart makes when you're fast asleep. "
                            "Let it go, let it go, can't hold it back anymore. "
                            "You're braver than you believe, stronger than you seem, and smarter than you think. "
                        )
                    }
                }
            ]
        }
    }

def test_get_articles_returns_expected_format(sample_guardian_response):
    with patch("src.utils.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = sample_guardian_response
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        articles = get_articles("test", date_from="2024-04-01")

        assert isinstance(articles, list)
        assert len(articles) == 1
        assert "webTitle" in articles[0]
        assert "webPublicationDate" in articles[0]
        assert "webUrl" in articles[0]
        assert "content_preview" in articles[0]
        assert len(articles[0]["content_preview"]) <= 1000


def test_publish_to_sqs_sends_messages():
    mock_sqs_client = MagicMock()
    mock_sqs_client.get_queue_url.return_value = {"QueueUrl": "mock-url"}
    mock_sqs_client.send_message.return_value = {"MessageId": "12345"}

    with patch("src.utils.boto3.client", return_value=mock_sqs_client):
        publish_to_sqs("mock-queue", [{
            "webTitle": "Mock Article",
            "webPublicationDate": "2024-04-10T12:34:56Z",
            "webUrl": "https://www.theguardian.com/mock",
            "content_preview": "Preview text here"
        }])

        mock_sqs_client.get_queue_url.assert_called_once_with(QueueName="mock-queue")
        mock_sqs_client.send_message.assert_called_once()
        args, kwargs = mock_sqs_client.send_message.call_args
        assert kwargs["QueueUrl"] == "mock-url"
        assert "Mock Article" in kwargs["MessageBody"]
