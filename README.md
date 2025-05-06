# Guardian Streamliner

A Python application that searches The Guardian API for articles matching specified terms and publishes them to AWS SQS for further processing.

## Project Overview

Guardian Streamliner is a lightweight data pipeline that allows users to:

1. Search for articles in The Guardian's content using specific search terms
2. Filter results by publication date
3. Publish formatted article data to AWS SQS for downstream applications
4. Run as either a standalone CLI tool or as an AWS Lambda function

The application returns up to 10 of the most recent articles matching the search criteria and publishes them in a standardized JSON format.

## Features

- Search The Guardian API by keyword with optional date filtering
- Publish article data to AWS SQS or local JSON files
- Detailed error handling and logging
- AWS Lambda integration
- Configurable message retention (default: 3 days)
- Content preview of article text (first 1000 characters)
- Comprehensive unit tests with high coverage

## Prerequisites

- Python 3.11+
- AWS CLI configured with appropriate credentials
- Guardian API key (free tier: [https://open-platform.theguardian.com/access/](https://open-platform.theguardian.com/access/))
- AWS SAM CLI (for deployment)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/DorotasHub/guardian-streamliner.git
cd guardian-streamliner
```

2. Setup virtual environment and install dependencies
```bash
make setup
```

3. Activate virtual enviroment:
```bash
source venv/bin/activate
```

4. Create a `.env` file in the project root with your Guardian API key:
   ```
   GUARDIAN_API_KEY=your-api-key-here
   ```

## Running Locally

The application can be run as a standalone CLI tool for testing and development:

```bash
make run
```

The CLI will prompt you for:
- Whether to publish to AWS SQS (y/n)
- Search term
- Start date (optional)
- SQS queue name (if publishing to SQS)

## AWS Deployment

The project uses AWS SAM for simplified deployment:

1. Ensure your AWS CLI is configured with the correct credentials and region:
   ```bash
   aws configure
   ```

2. Update the region in `samconfig.toml` if needed (default is `us-east-1`)

3. Run the deployment script:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

This will:
- Build the Lambda package
- Deploy the resources defined in `template.yaml`:
  - An SQS queue named `guardian-content`
  - A Lambda function named `articlePublisher`
  - Appropriate IAM roles and permissions
- Pass your Guardian API key securely to the Lambda environment

## Testing

Run unit tests with pytest:

```bash
# Run all tests
pytest

# Run with coverage report
coverage run -m pytest tests/
coverage report
```

### Current Test Coverage

The project maintains high test coverage (95% overall):

```
Name                Stmts   Miss  Cover
---------------------------------------
src/__init__.py         0      0   100%
src/app.py             92      9    90%
src/cli.py             16      3    81%
tests/__init__.py       0      0   100%
tests/test_app.py     142      0   100%
tests/test_cli.py      12      0   100%
---------------------------------------
TOTAL                 262     12    95%
```

### Security Scanning

Check for security issues:

```bash
bandit -r src/
```

## Lambda Invocation

Once deployed, you can invoke the Lambda function with:

```bash
aws lambda invoke \
  --function-name articlePublisher \
  --payload '{"search_term": "machine learning", "date_from": "2023-01-01", "queue_name": "guardian-content"}' \
  response.json
```

Or through the AWS Console Lambda Test interface with a test event like:

```json
{
  "search_term": "machine learning",
  "date_from": "2023-01-01",
  "queue_name": "guardian-content"
}
```

## Project Structure

```
guardian-streamliner/
├── src/
│   ├── app.py            # Main application code
│   └── cli.py            # Command-line interface
├── tests/
│   ├── test_app.py       # Unit tests for app.py
│   └── test_cli.py       # Unit tests for cli.py
├── deploy.sh             # Deployment script
├── dev-requirements.txt  # Development dependencies
├── samconfig.toml        # SAM configuration
└── template.yaml         # AWS SAM template
```

## JSON Output Format

The application publishes articles in the following JSON format:

```json
{
  "webPublicationDate": "2023-11-21T11:11:31Z",
  "webTitle": "Example Article Title",
  "webUrl": "https://www.theguardian.com/example/article",
  "summary": "Article summary text from the trailText field",
  "content_preview": "First 1000 characters of the article body..."
}
```

## Security and Quality Considerations

### Security
- No credentials are stored in code
- API key is passed securely via environment variables
- Lambda execution role follows principle of least privilege
- Messages are retained in SQS for a maximum of 3 days
- Regular security scanning with Bandit

### Code Quality
- 95% test coverage across the codebase
- PEP-8 compliant formatting
- Comprehensive error handling
- Detailed logging for troubleshooting

## Future Improvements

This project serves as a proof of concept for retrieving and publishing Guardian API content. Future enhancements could include:

1. **Content Enrichment**: Add sentiment analysis or topic classification to the article data
2. **Pagination Support**: Implement pagination to retrieve more than 10 articles when needed
3. **Scheduled Execution**: Create CloudWatch scheduled events to trigger the Lambda function periodically for specific search terms
4. **Content Filtering**: Add more sophisticated filtering options beyond the current search term and date filters