# app/main.py
import logging
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .db import init_db_pool, close_db_pool, ensure_schema, get_conn, put_conn
from .models import SensorPayload, HealthResponse
from .mqtt_client import start_mqtt, stop_mqtt

logger = logging.getLogger("lifeline")
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO if settings.ENV == "production" else logging.DEBUG)

app = FastAPI(title=settings.APP_NAME)

# CORS (adjust origins in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    logger.info("Starting application...")
    # init DB pool and ensure schema
    init_db_pool()
    ensure_schema()
    # start mqtt listener
    start_mqtt()
    logger.info("Startup complete.")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application...")
    stop_mqtt()
    close_db_pool()
    logger.info("Shutdown complete.")


def detect_accident(data: SensorPayload):
    """
    Detection logic kept from your prototype.
    tweak thresholds per real-world testing.
    """
    impact_force = abs(data.accel_x) + abs(data.accel_y) + abs(data.accel_z)
    tilt = abs(data.gyro_x) + abs(data.gyro_y)

    if impact_force > 30:
        return True, "High impact detected"
    if tilt > 200:
        return True, "Vehicle tilted / rolled"
    return False, "Normal"


@app.post("/iot/send")
async def receive_sensor_data(payload: SensorPayload):
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO sensor_data
            (device_id, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, latitude, longitude, speed)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id, timestamp
        """, (
            payload.device_id, payload.accel_x, payload.accel_y, payload.accel_z,
            payload.gyro_x, payload.gyro_y, payload.gyro_z,
            payload.latitude, payload.longitude, payload.speed
        ))
        result = cur.fetchone()
        conn.commit()
        cur.close()
        accident, msg = detect_accident(payload)
        response = {
            "status": "received",
            "accident_detected": accident,
            "message": msg,
            "record_id": result[0],
            "timestamp": result[1].isoformat() if result[1] else None
        }
        return JSONResponse(status_code=200, content=response)
    except Exception as e:
        logger.exception("Error saving sensor data: %s", e)
        raise HTTPException(status_code=500, detail="internal server error")
    finally:
        if conn:
            put_conn(conn)


@app.get("/health", response_model=HealthResponse)
def health():
    # Check DB connectivity
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
        details["db"] = f"error: {e}"
    finally:
        if conn:
            put_conn(conn)

    return HealthResponse(status="ok" if details.get("db") == "ok" else "degraded", details=details)


@app.get("/")
def root():
    return {"message": f"{settings.APP_NAME} running"}
