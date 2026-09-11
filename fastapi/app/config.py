"""Runtime configuration from environment.

Plays the same role `process.env.*` plays in other examples. Settings are
read once at startup and immutable thereafter.
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    # Server
    port: int = int(os.environ.get("PORT", "4000"))

    # Database: sqlite by default (zero-setup dev), or postgres via DATABASE_URL
    # SQLite requires aiosqlite driver for async; URL must use sqlite+aiosqlite:// scheme
    database_url: str = os.environ.get(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./fastapi.db"  # relative to cwd where uvicorn runs
    )

    # Auth fixtures (seeded on startup, all overridable)
    demo_customer_email: str = os.environ.get("DEMO_CUSTOMER_EMAIL", "alice@example.com")
    demo_customer_password: str = os.environ.get("DEMO_CUSTOMER_PASSWORD", "demo-password-123")
    admin_client_id: str = os.environ.get("ADMIN_CLIENT_ID", "admin-service")
    admin_client_secret: str = os.environ.get("ADMIN_CLIENT_SECRET", "admin-service-secret")
    carrier_api_key: str = os.environ.get("CARRIER_API_KEY", "carrier-demo-key")

    # Token expiration (seconds)
    token_expiry_seconds: int = 3600


settings = Settings()
