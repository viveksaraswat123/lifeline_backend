# app/mqtt_client.py
import json
import logging
import threading
import time

import paho.mqtt.client as mqtt

from .config import settings
from .models import SensorPayload
from .db import get_conn, put_conn

logger = logging.getLogger(__name__)

_CLIENT = None
_THREAD = None
_STOP = threading.Event()


def _on_connect(client, userdata, flags, rc):
    logger.info("MQTT connected with result code %s", rc)
    client.subscribe(settings.MQTT_TOPIC)


def _on_message(client, userdata, msg):
    try:
        payload_str = msg.payload.decode()
        payload = json.loads(payload_str)
        data = SensorPayload(**payload)
        # store into DB
        conn = get_conn()
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO sensor_data
                (device_id, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, latitude, longitude, speed)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                data.device_id, data.accel_x, data.accel_y, data.accel_z,
                data.gyro_x, data.gyro_y, data.gyro_z,
                data.latitude, data.longitude, data.speed
            ))
            conn.commit()
            cur.close()
        finally:
            put_conn(conn)
        logger.debug("MQTT received and stored data for device %s", data.device_id)
    except Exception as exc:
        logger.exception("Error processing MQTT message: %s", exc)


def start_mqtt():
    global _CLIENT, _THREAD, _STOP
    if _CLIENT:
        return

    client = mqtt.Client()
    client.on_connect = _on_connect
    client.on_message = _on_message

    def run():
        try:
            client.connect(settings.MQTT_BROKER, settings.MQTT_PORT, 60)
            client.loop_start()
            logger.info("MQTT loop started; subscribed to %s", settings.MQTT_TOPIC)
            while not _STOP.is_set():
                time.sleep(1)
        except Exception:
            logger.exception("MQTT client error")

    _THREAD = threading.Thread(target=run, daemon=True)
    _THREAD.start()
    _CLIENT = client


def stop_mqtt():
    global _CLIENT, _STOP
    _STOP.set()
    if _CLIENT:
        try:
            _CLIENT.loop_stop()
            _CLIENT.disconnect()
        except Exception:
            logger.exception("Error stopping MQTT client")
    logger.info("MQTT stopped")
