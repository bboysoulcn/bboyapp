"""BBoyApp 配置模块（通过环境变量加载）"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # 数据库
    database_url: str = "postgresql+asyncpg://bboyapp:bboyapp@localhost:5432/bboyapp"

    # SMTP 邮件
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@bboyapp.com"

    # 爬虫
    scraper_interval_hours: int = 6

    # 管理接口
    admin_api_key: str = "change-me-in-production"

    # 应用
    app_name: str = "BBoyApp"
    debug: bool = False


settings = Settings()
