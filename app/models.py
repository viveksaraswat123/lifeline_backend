from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, StrictFloat, StrictStr


class SensorPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    device_id: StrictStr = Field(..., min_length=3, max_length=64)
    accel_x: StrictFloat
    accel_y: StrictFloat
    accel_z: StrictFloat
    gyro_x: StrictFloat
    gyro_y: StrictFloat
    gyro_z: StrictFloat
    latitude: StrictFloat = Field(..., ge=-90, le=90)
    longitude: StrictFloat = Field(..., ge=-180, le=180)
    speed: StrictFloat = Field(..., ge=0)
    timestamp: Optional[datetime] = None


class HealthResponse(BaseModel):
    status: StrictStr
    details: Optional[Dict[str, Any]] = None
