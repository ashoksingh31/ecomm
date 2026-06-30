"""
Application-wide configuration.

Everything that would normally live in environment variables / a .env file
is centralised here so the rest of the codebase never hardcodes a magic
number. This is what Decision "Fixed config for N and discount %" refers to
in DECISIONS.md - MILESTONE_INTERVAL and MILESTONE_DISCOUNT_PERCENTAGE are
NOT accepted from API callers, they are read from here only.
"""

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- JWT ---
    # In a real system this secret would come from a secrets manager.
    # Authentication itself is out of scope for this assignment (see
    # ASSUMPTIONS.md #1), but we still need a key to verify/sign tokens
    # for local testing via scripts/generate_test_token.py.
    jwt_secret_key: str = "dev-only-secret-change-me"
    jwt_algorithm: str = "HS256"

    # --- Discount / milestone rules ---
    # Every Nth order (store-wide, see DECISIONS.md) becomes eligible for
    # an automatically-generated single-use discount code.
    milestone_interval: int = 5
    milestone_discount_percentage: float = 10.0

    # --- App metadata ---
    app_name: str = "E-Commerce Cart & Checkout Service"
    app_version: str = "1.0.0"

    model_config = ConfigDict(env_prefix="APP_")


# Single shared settings instance, imported everywhere instead of
# re-instantiating Settings() in every module.
settings = Settings()
