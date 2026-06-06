import pytest
from unittest.mock import patch


MOCK_ENV = {
    "ANTHROPIC_API_KEY": "test-claude-key",
    "REDDIT_CLIENT_ID": "test-reddit-id",
    "REDDIT_CLIENT_SECRET": "test-reddit-secret",
    "REDDIT_USERNAME": "testuser",
    "REDDIT_PASSWORD": "testpass",
    "REDDIT_USER_AGENT": "EduBot/1.0",
    "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/test",
    "GOOGLE_CLIENT_ID": "test-google-id",
    "GOOGLE_CLIENT_SECRET": "test-google-secret",
    "GOOGLE_CALENDAR_ID": "test@group.calendar.google.com",
    "GOOGLE_REDIRECT_URI": "http://localhost:8080",
    "GMAIL_NOTIFY_ADDRESS": "test@example.com",
    "PEXELS_API_KEY": "test-pexels-key",
    "UNSPLASH_ACCESS_KEY": "test-unsplash-key",
    "SUPABASE_URL": "https://test.supabase.co",
    "SUPABASE_ANON_KEY": "test-anon-key",
    "SUPABASE_SERVICE_ROLE_KEY": "test-service-key",
    "LOG_LEVEL": "DEBUG",
    "DRY_RUN": "true",
    "WEEKLY_RUN_DAY": "monday",
}


def test_settings_load_without_error():
    with patch.dict("os.environ", MOCK_ENV, clear=False):
        from importlib import reload
        import config.settings as settings_module
        reload(settings_module)
        s = settings_module.Settings()

        assert s.claude.api_key == "test-claude-key"
        assert s.reddit.client_id == "test-reddit-id"
        assert s.reddit.user_agent == "EduBot/1.0"
        assert s.discord.webhook_url == "https://discord.com/api/webhooks/test"
        assert s.google.calendar_id == "test@group.calendar.google.com"
        assert s.pexels.api_key == "test-pexels-key"
        assert s.unsplash.access_key == "test-unsplash-key"
        assert s.supabase.url == "https://test.supabase.co"
        assert s.app.log_level == "DEBUG"
        assert s.app.dry_run is True


def test_settings_have_correct_types():
    with patch.dict("os.environ", MOCK_ENV, clear=False):
        from importlib import reload
        import config.settings as settings_module
        reload(settings_module)
        s = settings_module.Settings()

        assert isinstance(s.app.dry_run, bool)
        assert isinstance(s.app.log_level, str)


def test_logging_setup():
    import logging
    with patch.dict("os.environ", MOCK_ENV, clear=False):
        from config.logging import setup_logging, get_logger
        setup_logging("DEBUG")
        logger = get_logger("test")
        assert logger is not None
        assert logging.getLogger().level == logging.DEBUG
