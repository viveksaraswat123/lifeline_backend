# app/config.py
import os
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    APP_NAME: str = "Lifeline IoT Accident Alert System"
    ENV: str = "production"

    # Postgres
    DB_HOST: str = Field("localhost", env="DB_HOST")
    DB_PORT: int = Field(5432, env="DB_PORT")
    DB_NAME: str = Field("lifeline", env="DB_NAME")
    DB_USER: str = Field("postgres", env="DB_USER")
    DB_PASSWORD: str = Field(..., env="DB_PASSWORD")

    # MQTT
    MQTT_BROKER: str = Field("broker.hivemq.com", env="MQTT_BROKER")
    MQTT_PORT: int = Field(1883, env="MQTT_PORT")
    MQTT_TOPIC: str = Field("lifeline/iot/data", env="MQTT_TOPIC")

    # pool
    DB_MINCONN: int = Field(1, env="DB_MINCONN")
    DB_MAXCONN: int = Field(5, env="DB_MAXCONN")

    class Config:
        env_file = os.getenv("ENV_FILE", ".env")
        env_file_encoding = "utf-8"


settings = Settings()
