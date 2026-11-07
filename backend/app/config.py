from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "CampusPulse AI"
    database_url: str = "sqlite:///./campuspulse.db"
    app_mode: str = "demo"  # demo | live
    discord_bot_token: str = ""
    discord_guild_id: str = ""
    discord_channel_id: str = ""
    switch_base_url: str = ""
    switch_registration_key: str = ""
    switch_agent_id: str = ""
    switch_agent_api_key: str = ""
    switch_room_id: str = ""
    openai_api_key: str = ""
    model_name: str = "gpt-4.1-mini"
    frontend_origin: str = "http://localhost:5173"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
