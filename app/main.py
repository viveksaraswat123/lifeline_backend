import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import init_db_pool, close_db_pool, ensure_schema, get_conn, put_conn
from app.models import SensorPayload, HealthResponse
from app.mqtt_client import start_mqtt, stop_mqtt

logger = logging.getLogger("lifeline")
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO if settings.ENV == "production" else logging.DEBUG)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db_pool()
    ensure_schema()
    start_mqtt()
    yield
    stop_mqtt()
    close_db_pool()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="LIFELINE IoT Accident Detection & Emergency Alert System",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def detect_accident(data: SensorPayload):
    impact = abs(data.accel_x) + abs(data.accel_y) + abs(data.accel_z)
    tilt = abs(data.gyro_x) + abs(data.gyro_y)
    if impact >= settings.IMPACT_THRESHOLD:
        return True, "High impact detected"
    if tilt >= settings.TILT_THRESHOLD:
        return True, "Vehicle rollover detected"
    return False, "Normal movement"

@app.post("/api/v1/iot/sensor-data", status_code=status.HTTP_201_CREATED)
async def ingest_sensor_data(payload: SensorPayload):
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO sensor_data
            (device_id, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, latitude, longitude, speed)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id, timestamp
            """,
            (
                payload.device_id,
                payload.accel_x,
                payload.accel_y,
                payload.accel_z,
                payload.gyro_x,
                payload.gyro_y,
                payload.gyro_z,
                payload.latitude,
                payload.longitude,
                payload.speed,
            ),
        )
        record_id, ts = cur.fetchone()
        conn.commit()
        cur.close()
        accident, reason = detect_accident(payload)
        return {
            "status": "success",
            "record_id": record_id,
            "timestamp": ts.isoformat(),
            "accident_detected": accident,
            "reason": reason,
        }
    except Exception:
        logger.exception("Sensor ingestion failed")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if conn:
            put_conn(conn)

@app.get("/api/v1/health", response_model=HealthResponse)
def health():
    conn = None
    details = {}
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        details["db"] = "ok"
    except Exception as e:
        details["db"] = str(e)
    finally:
        if conn:
            put_conn(conn)
    status_val = "ok" if details.get("db") == "ok" else "degraded"
    return HealthResponse(status=status_val, details=details)

@app.get("/")
def root():
    return {"service": settings.APP_NAME, "version": settings.VERSION}
