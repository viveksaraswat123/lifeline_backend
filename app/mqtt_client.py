import json
import logging
import threading
import time
import paho.mqtt.client as mqtt

from app.config import settings
from app.models import SensorPayload
from app.db import get_conn, put_conn

logger = logging.getLogger("lifeline.mqtt")

_CLIENT: mqtt.Client | None = None
_THREAD: threading.Thread | None = None
_STOP_EVENT = threading.Event()


def _on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        client.subscribe(settings.MQTT_TOPIC, qos=1)
        logger.info("MQTT connected and subscribed")
    else:
        logger.error("MQTT connection failed with code %s", rc)


def _on_message(client, userdata, msg):
    conn = None
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        data = SensorPayload(**payload)

        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO sensor_data
            (device_id, accel_x, accel_y, accel_z,
             gyro_x, gyro_y, gyro_z,
             latitude, longitude, speed)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                data.device_id,
                data.accel_x,
                data.accel_y,
                data.accel_z,
                data.gyro_x,
                data.gyro_y,
                data.gyro_z,
                data.latitude,
                data.longitude,
                data.speed,
            ),
        )
        conn.commit()
        cur.close()

        logger.debug("MQTT data stored for %s", data.device_id)

    except Exception:
        logger.exception("Failed to process MQTT message")
    finally:
        if conn:
            put_conn(conn)


def _mqtt_loop(client: mqtt.Client):
    try:
        client.connect(settings.MQTT_BROKER, settings.MQTT_PORT, keepalive=60)
        client.loop_start()
        while not _STOP_EVENT.is_set():
            time.sleep(1)
    except Exception:
        logger.exception("MQTT loop failure")
    finally:
        try:
            client.loop_stop()
            client.disconnect()
        except Exception:
            logger.exception("MQTT shutdown failure")


def start_mqtt():
    global _CLIENT, _THREAD
    if _CLIENT:
        return

    _STOP_EVENT.clear()

    client = mqtt.Client(protocol=mqtt.MQTTv311)
    client.on_connect = _on_connect
    client.on_message = _on_message

    _THREAD = threading.Thread(
        target=_mqtt_loop,
        args=(client,),
        daemon=True,
        name="mqtt-listener",
    )
    _THREAD.start()

    _CLIENT = client
    logger.info("MQTT listener started")


def stop_mqtt():
    global _CLIENT
    _STOP_EVENT.set()

    if _CLIENT:
        try:
            _CLIENT.loop_stop()
            _CLIENT.disconnect()
        except Exception:
            logger.exception("Error stopping MQTT client")
        finally:
            _CLIENT = None

    logger.info("MQTT listener stopped")
