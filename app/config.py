import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    APP_NAME: str = "Lifeline IoT Accident Alert System"
    VERSION: str = "1.0.0"
    ENV: str = "production"

    ALLOWED_ORIGINS: List[str] = ["*"]

    DB_HOST: str = Field("localhost")
    DB_PORT: int = Field(5432)
    DB_NAME: str = Field("lifeline")
    DB_USER: str = Field("postgres")
    DB_PASSWORD: str

    DB_MINCONN: int = Field(1, ge=1)
    DB_MAXCONN: int = Field(10, ge=1)

    MQTT_BROKER: str = Field("broker.hivemq.com")
    MQTT_PORT: int = Field(1883)
    MQTT_TOPIC: str = Field("lifeline/iot/data")

    IMPACT_THRESHOLD: float = Field(30.0, gt=0)
    TILT_THRESHOLD: float = Field(200.0, gt=0)


settings = Settings()
