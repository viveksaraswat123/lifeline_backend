# app/models.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class SensorPayload(BaseModel):
    device_id: str = Field(..., example="device-1234")
    accel_x: float
    accel_y: float
    accel_z: float
    gyro_x: float
    gyro_y: float
    gyro_z: float
    latitude: float
    longitude: float
    speed: float
    timestamp: Optional[datetime] = None


class HealthResponse(BaseModel):
    status: str
    details: dict | None = None
