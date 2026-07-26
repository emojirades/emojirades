from unittest.mock import MagicMock, patch

from emojirades.bot import EmojiradesBot


class TestSQSOnboarding:
    @patch("boto3.client")
    @patch("emojirades.bot.get_workspace_repository")
    def test_listen_for_onboarding_sqs_long_polling(self, mock_get_repo, mock_boto_client):
        mock_sqs = MagicMock()
        mock_boto_client.return_value = mock_sqs
        mock_sqs.get_queue_url.return_value = {"QueueUrl": "https://sqs.fake/queue"}
        mock_sqs.receive_message.return_value = {
            "Messages": [
                {
                    "Body": '{"workspace_id": "WS123"}',
                    "ReceiptHandle": "handle123",
                }
            ]
        }

        mock_repo = MagicMock()
        mock_get_repo.return_value = mock_repo
        mock_repo.workspace.return_value = {
            "workspace_id": "WS123",
            "bot_name": "testbot",
            "bot_id": "U123",
        }

        bot = EmojiradesBot()
        bot.onboarding_queue = "onboarding-queue"
        bot.configure_workspace = MagicMock()
        mock_slack_obj = MagicMock()
        mock_slack_obj.workspace_id = "WS123"
        bot.configure_workspace.return_value = mock_slack_obj

        mock_workspace = MagicMock()
        bot.workspaces["WS123"] = mock_workspace

        # Run non-blocking (oneshot=True)
        bot.listen_for_onboarding("s3://fake-workspaces", blocking=False, wait_time_seconds=15)

        # Assert long polling parameter WaitTimeSeconds was passed to receive_message
        mock_sqs.receive_message.assert_called_once_with(
            QueueUrl="https://sqs.fake/queue",
            WaitTimeSeconds=15,
        )

        # Assert onboarding was processed and message deleted
        bot.configure_workspace.assert_called_once()
        mock_sqs.delete_message.assert_called_once_with(
            QueueUrl="https://sqs.fake/queue",
            ReceiptHandle="handle123",
        )
