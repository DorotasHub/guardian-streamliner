import pytest
import os
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError
from src.app import get_articles, ensure_sqs_queue_exists, publish_to_sqs, lambda_handler
import json

@pytest.fixture
def sample_guardian_response():
    """Fixture providing a sample response from The Guardian API"""
    return {
        "response": {
            "status": "ok",
            "total": 1,
            "results": [
                {
                    "id": "technology/2024/apr/05/test-article",
                    "type": "article",
                    "sectionId": "technology",
                    "sectionName": "Technology",
                    "webPublicationDate": "2024-04-05T12:34:56Z",
                    "webTitle": "Test Article on Technology",
                    "webUrl": "https://www.theguardian.com/technology/2024/apr/05/test-article",
                    "apiUrl": "https://content.guardianapis.com/technology/2024/apr/05/test-article",
                    "fields": {
                        "trailText": "This is a summary of the test article content.",
                        "body": (
                            "<p>Hakuna Matata! It means no worries, for the rest of your days. "
                            "Just keep swimming, just keep swimming. "
                            "To infinity and beyond!</p>"
                            "<p>Ohana means family, and family means nobody gets left behind. "
                            "Second star to the right and straight on till morning. "
                            "Adventure is out there! Some people are worth melting for.</p>"
                            "<p>A dream is a wish your heart makes when you're fast asleep. "
                            "Let it go, let it go, can't hold it back anymore. "
                            "You're braver than you believe, stronger than you seem, and smarter than you think.</p>"
                        )
                    }
                }
            ]
        }
    }


@pytest.fixture
def sample_articles():
    """Fixture providing sample processed articles"""
    return [
        {
            "webPublicationDate": "2024-04-05T12:34:56Z",
            "webTitle": "Test Article on Technology",
            "webUrl": "https://www.theguardian.com/technology/2024/apr/05/test-article",
            "summary": "This is a summary of the test article content.",
            "content_preview": "<p>Hakuna Matata! It means no worries, for the rest of your days. Just keep swimming, just keep swimming. To infinity and beyond!</p><p>Ohana means family, and family means nobody gets left behind. Second star to the right and straight on till morning. Adventure is out there! Some people are worth melting for.</p><p>A dream is a wish your heart makes when you're fast asleep. Let it go, let it go, can't hold it back anymore. You're braver than you believe, stronger than you seem, and smarter than you think.</p>"
        }
    ]


def test_get_articles_returns_expected_format(sample_guardian_response):
    """Test that get_articles processes API response into expected format"""
    with patch("src.app.requests.get") as mock_get, \
         patch.dict(os.environ, {"GUARDIAN_API_KEY": "fake-api-key"}):
        
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
        assert "summary" in articles[0]
        assert "content_preview" in articles[0]
        assert len(articles[0]["content_preview"]) <= 1000
        
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert kwargs["params"]["q"] == '"test"'
        assert kwargs["params"]["from-date"] == "2024-04-01"
        assert kwargs["params"]["api-key"] == "fake-api-key"


def test_get_articles_missing_api_key():
    """Test that get_articles raises ValueError when API key is missing"""
    with patch.dict(os.environ, {}, clear=True), \
         pytest.raises(ValueError, match="GUARDIAN_API_KEY environment variable is not set"):
        get_articles("test")


def test_get_articles_handles_api_error():
    """Test that get_articles handles API errors gracefully"""
    with patch("src.app.requests.get") as mock_get, \
         patch.dict(os.environ, {"GUARDIAN_API_KEY": "fake-api-key"}):
        
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mock_get.return_value = mock_response

        articles = get_articles("test")
        
        assert articles == []


def test_ensure_sqs_queue_exists_success():
    """Test ensure_sqs_queue_exists when queue exists"""
    mock_sqs_client = MagicMock()
    mock_sqs_client.get_queue_url.return_value = {"QueueUrl": "https://sqs.region.amazonaws.com/123456789012/test-queue"}
    
    with patch("src.app.boto3.client", return_value=mock_sqs_client):
        queue_url = ensure_sqs_queue_exists("test-queue")
        
        assert queue_url == "https://sqs.region.amazonaws.com/123456789012/test-queue"
        mock_sqs_client.get_queue_url.assert_called_once_with(QueueName="test-queue")


def test_ensure_sqs_queue_exists_not_found():
    """Test ensure_sqs_queue_exists when queue doesn't exist"""
    mock_sqs_client = MagicMock()
    mock_sqs_client.get_queue_url.side_effect = ClientError(
        {"Error": {"Code": "AWS.SimpleQueueService.NonExistentQueue"}},
        "GetQueueUrl"
    )
    
    with patch("src.app.boto3.client", return_value=mock_sqs_client), \
         pytest.raises(Exception, match="SQS queue 'missing-queue' does not exist."):
        ensure_sqs_queue_exists("missing-queue")


def test_publish_to_sqs_sends_messages(sample_articles):
    """Test publish_to_sqs sends messages to SQS"""
    mock_sqs_client = MagicMock()
    mock_sqs_client.get_queue_url.return_value = {"QueueUrl": "mock-url"}
    mock_sqs_client.send_message.return_value = {"MessageId": "12345"}

    with patch("src.app.boto3.client", return_value=mock_sqs_client):
        count = publish_to_sqs("mock-queue", sample_articles)

        mock_sqs_client.get_queue_url.assert_called_once_with(QueueName="mock-queue")
        mock_sqs_client.send_message.assert_called_once()
        
        args, kwargs = mock_sqs_client.send_message.call_args
        assert kwargs["QueueUrl"] == "mock-url"
        assert "Test Article on Technology" in kwargs["MessageBody"]
        assert count == 1


def test_publish_to_sqs_empty_list():
    """Test publish_to_sqs with empty article list"""
    with patch("src.app.boto3.client") as mock_boto3:
        count = publish_to_sqs("mock-queue", [])
        
        assert count == 0
        mock_boto3.assert_not_called()


def test_publish_to_sqs_handles_errors(sample_articles):
    """Test publish_to_sqs handles errors when sending messages"""
    mock_sqs_client = MagicMock()
    mock_sqs_client.get_queue_url.return_value = {"QueueUrl": "mock-url"}
    mock_sqs_client.send_message.side_effect = Exception("SQS Error")

    with patch("src.app.boto3.client", return_value=mock_sqs_client):
        count = publish_to_sqs("mock-queue", sample_articles)
        
        assert count == 0
        mock_sqs_client.send_message.assert_called_once()


def test_lambda_handler_success(sample_articles):
    """Test lambda_handler processes input and returns success response"""
    event = {
        "search_term": "Technology",
        "date_from": "2024-01-01",
        "queue_name": "guardian-content"
    }

    with patch("src.app.get_articles", return_value=sample_articles) as mock_get, \
         patch("src.app.publish_to_sqs", return_value=1) as mock_publish:

        response = lambda_handler(event, context={})

        mock_get.assert_called_once_with("Technology", "2024-01-01")
        mock_publish.assert_called_once_with("guardian-content", sample_articles)

        assert response["statusCode"] == 200
        assert "1 articles sent to SQS queue 'guardian-content'" in json.dumps(response["body"],indent=4)


def test_lambda_handler_missing_search_term():
    """Test lambda_handler returns error when search_term is missing"""
    event = {
        "date_from": "2024-01-01",
        "queue_name": "guardian-content"
    }

    response = lambda_handler(event, context={})

    assert response["statusCode"] == 400
    assert "Missing required field" in response["body"]


def test_lambda_handler_no_articles_found():
    """Test lambda_handler when no articles are found"""
    event = {
        "search_term": "NonexistentTopic",
        "date_from": "2024-01-01"
    }

    with patch("src.app.get_articles", return_value=[]):
        response = lambda_handler(event, context={})

        assert response["statusCode"] == 200
        assert "No articles found" in response["body"]