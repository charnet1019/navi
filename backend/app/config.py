from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Navi"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Auth Cookies
    AUTH_ACCESS_COOKIE_NAME: str = "navi_access_token"
    AUTH_REFRESH_COOKIE_NAME: str = "navi_refresh_token"
    AUTH_CSRF_COOKIE_NAME: str = "navi_csrf_token"
    AUTH_CSRF_HEADER_NAME: str = "X-CSRF-Token"
    AUTH_COOKIE_SECURE: bool = False
    AUTH_COOKIE_SAMESITE: str = "lax"
    AUTH_COOKIE_DOMAIN: str | None = None

    # CORS
    CORS_ORIGINS: str = ""
    CORS_ALLOW_CREDENTIALS: bool = True

    @computed_field
    @property
    def auth_cookie_samesite(self) -> str:
        return self.AUTH_COOKIE_SAMESITE.strip().lower()

    @computed_field
    @property
    def auth_cookie_domain(self) -> str | None:
        if self.AUTH_COOKIE_DOMAIN is None:
            return None
        domain = self.AUTH_COOKIE_DOMAIN.strip()
        return domain or None

    @computed_field
    @property
    def cors_origins_list(self) -> list[str]:
        v = self.CORS_ORIGINS.strip()
        if not v:
            return []
        if v.startswith("["):
            import json
            return json.loads(v)
        return [s.strip() for s in v.split(",") if s.strip()]

    @computed_field
    @property
    def cors_allow_credentials(self) -> bool:
        return self.CORS_ALLOW_CREDENTIALS and "*" not in self.cors_origins_list

    # File Upload
    UPLOAD_DIR: str = "/app/uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_EXTENSIONS: set[str] = {
        ".png", ".jpg", ".jpeg", ".gif", ".webp",  # 常见格式
        ".ico",  # Windows图标
        ".bmp",  # 位图
        ".tiff", ".tif",  # TIFF格式
        ".avif",  # 新的高效格式
        ".jfif",  # JPEG文件交换格式
    }

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # Security - Hierarchy limits
    MAX_HIERARCHY_DEPTH: int = 50
    MAX_NAVIGATION_GROUPS: int = 10000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
