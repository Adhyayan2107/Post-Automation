from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

ENV_FILE = ".env"
ENV_ENC = "utf-8"


class ClaudeSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE, env_file_encoding=ENV_ENC,
        env_prefix="ANTHROPIC_", extra="ignore",
    )
    api_key: str = Field(default="")


class RedditSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE, env_file_encoding=ENV_ENC,
        env_prefix="REDDIT_", extra="ignore",
    )
    client_id: str = Field(default="")
    client_secret: str = Field(default="")
    username: str = Field(default="")
    password: str = Field(default="")
    user_agent: str = Field(default="EduBot/1.0")


class DiscordSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE, env_file_encoding=ENV_ENC,
        env_prefix="DISCORD_", extra="ignore",
    )
    webhook_url: str = Field(default="")



class PexelsSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE, env_file_encoding=ENV_ENC,
        env_prefix="PEXELS_", extra="ignore",
    )
    api_key: str = Field(default="")


class UnsplashSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE, env_file_encoding=ENV_ENC,
        env_prefix="UNSPLASH_", extra="ignore",
    )
    access_key: str = Field(default="")


class TmdbSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE, env_file_encoding=ENV_ENC,
        env_prefix="TMDB_", extra="ignore",
    )
    api_key: str = Field(default="")


class SupabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE, env_file_encoding=ENV_ENC,
        env_prefix="SUPABASE_", extra="ignore",
    )
    url: str = Field(default="")
    anon_key: str = Field(default="")
    service_role_key: str = Field(default="")


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE, env_file_encoding=ENV_ENC,
        env_prefix="", extra="ignore",
        populate_by_name=True,
    )
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    dry_run: bool = Field(default=False, alias="DRY_RUN")
    weekly_run_day: str = Field(default="monday", alias="WEEKLY_RUN_DAY")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE, env_file_encoding=ENV_ENC, extra="ignore",
    )
    claude: ClaudeSettings = Field(default_factory=ClaudeSettings)
    reddit: RedditSettings = Field(default_factory=RedditSettings)
    discord: DiscordSettings = Field(default_factory=DiscordSettings)
    pexels: PexelsSettings = Field(default_factory=PexelsSettings)
    unsplash: UnsplashSettings = Field(default_factory=UnsplashSettings)
    tmdb: TmdbSettings = Field(default_factory=TmdbSettings)
    supabase: SupabaseSettings = Field(default_factory=SupabaseSettings)
    app: AppSettings = Field(default_factory=AppSettings)


settings = Settings()
