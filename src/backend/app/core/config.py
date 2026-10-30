from typing import Annotated, Literal, Self

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

ENV_EXAMPLE_PLACEHOLDER = "change-me"
MIN_JWT_SECRET_LENGTH = {"HS256": 32, "HS384": 48, "HS512": 64}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", frozen=True, hide_input_in_errors=True
    )

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    cors_origins: Annotated[list[str], NoDecode] = []
    database_url: SecretStr
    database_schema: str = Field(default="cic", pattern=r"^[a-z_][a-z0-9_]{0,62}$")
    jwt_secret: SecretStr
    jwt_algorithm: Literal["HS256", "HS384", "HS512"] = "HS256"
    jwt_expire_minutes: int = Field(default=30, gt=0)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def check_jwt_secret(self) -> Self:
        secret = self.jwt_secret.get_secret_value()
        if secret.startswith(ENV_EXAMPLE_PLACEHOLDER):
            raise ValueError("JWT_SECRET still holds the .env.example placeholder")
        if len(secret) < MIN_JWT_SECRET_LENGTH[self.jwt_algorithm]:
            raise ValueError(f"JWT_SECRET is too short for {self.jwt_algorithm}")
        return self
