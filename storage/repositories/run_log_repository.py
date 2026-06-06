from uuid import UUID
from datetime import datetime, timezone
from supabase import Client
from config.logging import get_logger

logger = get_logger(__name__)


class RunLogRepository:
    def __init__(self, client: Client) -> None:
        self._client = client

    async def start_run(self) -> UUID:
        response = (
            self._client.table("weekly_runs")
            .insert({"status": "running"})
            .execute()
        )
        run_id = UUID(response.data[0]["id"])
        logger.info("Started run %s", run_id)
        return run_id

    async def finish_run(self, run_id: UUID, post_count: int) -> None:
        self._client.table("weekly_runs").update({
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "status": "completed",
            "post_count": post_count,
        }).eq("id", str(run_id)).execute()
        logger.info("Finished run %s with %d posts", run_id, post_count)

    async def fail_run(self, run_id: UUID) -> None:
        self._client.table("weekly_runs").update({
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "status": "failed",
        }).eq("id", str(run_id)).execute()
        logger.warning("Run %s marked as failed", run_id)
