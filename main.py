import json
import time
import asyncio
from datetime import datetime

import paho.mqtt.client as mqtt
from fastapi import FastAPI
from pydantic import BaseModel
import psycopg2


def get_db():
    return psycopg2.connect(
        host="localhost",
        database="lifeline",
        user="postgres",
        password="your_password"
    )


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sensor_data (
            id SERIAL PRIMARY KEY,
            device_id TEXT,
            accel_x FLOAT,
            accel_y FLOAT,
            accel_z FLOAT,
            gyro_x FLOAT,
            gyro_y FLOAT,
            gyro_z FLOAT,
            latitude FLOAT,
            longitude FLOAT,
            speed FLOAT,
            timestamp TIMESTAMPTZ DEFAULT NOW()
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

init_db()


app = FastAPI(title="Lifeline IoT Accident Alert System")


class SensorPayload(BaseModel):
    device_id: str
    accel_x: float
    accel_y: float
    accel_z: float
    gyro_x: float
    gyro_y: float
    gyro_z: float
    latitude: float
    longitude: float
    speed: float


def detect_accident(data: SensorPayload):
    impact_force = abs(data.accel_x) + abs(data.accel_y) + abs(data.accel_z)
    tilt = abs(data.gyro_x) + abs(data.gyro_y)

    if impact_force > 30:
        return True, "High impact detected"

    if tilt > 200:
        return True, "Vehicle tilted / rolled"

    return False, "Normal"


def save_data(data: SensorPayload):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO sensor_data
        (device_id, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, 
         latitude, longitude, speed)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        data.device_id, data.accel_x, data.accel_y, data.accel_z,
        data.gyro_x, data.gyro_y, data.gyro_z,
        data.latitude, data.longitude, data.speed
    ))
    conn.commit()
    cur.close()
    conn.close()


@app.post("/iot/send")
async def receive_sensor_data(payload: SensorPayload):
    save_data(payload)
    accident, msg = detect_accident(payload)
    return {
        "status": "received",
        "accident_detected": accident,
        "message": msg
    }


MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC = "lifeline/iot/data"

client = mqtt.Client()


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        data = SensorPayload(**payload)
        save_data(data)
        accident, message = detect_accident(data)
        print("\nMQTT DATA RECEIVED")
        print(payload)
        print("Accident:", accident, "|", message)
    except Exception as e:
        print("MQTT ERROR:", e)


def mqtt_connect():
    client.on_message = on_message
    client.connect(MQTT_BROKER, 1883, 60)
    client.subscribe(MQTT_TOPIC)
    client.loop_start()


@app.on_event("startup")
async def startup_event():
    print("Starting MQTT Listener...")
    mqtt_connect()


@app.get("/")
def root():
    return {"message": "Lifeline IoT API Running"}
