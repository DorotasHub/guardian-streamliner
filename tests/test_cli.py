import builtins
from unittest import mock
from src import cli


def test_main_cli_flow(monkeypatch):
    """Test main() flow with file output (not SQS)."""
    inputs = iter(["n", "test search", "2024-01-01", ""])

    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))
    monkeypatch.setattr(cli, "get_articles", lambda *_: [{"title": "One"}])
    monkeypatch.setattr(cli, "publish_to_file", lambda a: len(a))
    monkeypatch.setattr(cli, "publish_to_sqs", lambda q, a: len(a))

    with mock.patch("builtins.print") as mock_print:
        cli.main()
        mock_print.assert_any_call("Retrieved 1 articles.")
