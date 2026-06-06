from supabase import create_client, Client
from config.settings import settings
from config.logging import get_logger

logger = get_logger(__name__)

_client: Client | None = None


def get_supabase_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(
            settings.supabase.url,
            settings.supabase.anon_key,
        )
    return _client


def get_supabase_service_client() -> Client:
    return create_client(
        settings.supabase.url,
        settings.supabase.service_role_key,
    )


async def test_connection() -> bool:
    try:
        client = get_supabase_client()
        client.table("weekly_runs").select("id").limit(1).execute()
        logger.info("Supabase connection OK")
        return True
    except Exception as exc:
        logger.error("Supabase connection failed: %s", exc)
        return False
