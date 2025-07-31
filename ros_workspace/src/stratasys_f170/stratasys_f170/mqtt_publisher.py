import asyncio
import json
from typing import Any, Optional

from rclpy.impl.rcutils_logger import RcutilsLogger
from asyncio_mqtt import Client, MqttError


class MQTTClient:

    def __init__(self, token: str, log: RcutilsLogger, host: str, port: int = 1883) -> None:
        self._token = token
        self._host = host
        self._port = port
        self._topic = "v1/devices/me/telemetry"
        self._log = log
        self._client: Optional[Client] = None
        self._connected = False

        self._client = Client(
            hostname=self._host,
            port=self._port,
            username=self._token,
            keepalive=60,
        )

    async def connect(self, retries: int = 5, delay: float = 2.0) -> None:
        if not self._client:
            raise RuntimeError("MQTT client is not initialized.")

        for attempt in range(1, retries + 1):
            try:
                await self._client.connect()
                self._log.info("Connected to ThingsBoard MQTT broker.")
                self._connected = True
                return
            except MqttError as e:
                self._log.error(f"Connection attempt {attempt} failed: {e}")
                await asyncio.sleep(delay * (2 ** (attempt - 1)))

        raise ConnectionError(
            "Exceeded maximum number of retries to connect to MQTT broker.")

    async def disconnect(self) -> None:
        if self._client and self._connected:
            try:
                await self._client.disconnect()
                self._log.info("Disconnected from ThingsBoard MQTT broker.")
                self._connected = False
            except MqttError as e:
                self._log.warning(f"Failed to disconnect cleanly: {e}")

    async def publish_data(self, data: dict[str, Any]) -> None:
        if not self._client or not self._connected:
            raise RuntimeError("MQTT client is not connected.")

        payload: bytes = json.dumps(data).encode()

        for attempt in range(1, 4):
            try:
                await self._client.publish(self._topic, payload=payload, qos=1)
                self._log.debug(
                    f"Published telemetry data to topic '{self._topic}'.")
                return
            except MqttError as e:
                self._log.warning(f"Publish attempt {attempt} failed: {e}")
                await self.reconnect()

        self._log.error("Failed to publish data after multiple attempts.")

    async def reconnect(self) -> None:
        if self._client:
            try:
                await self._client.disconnect()
            except Exception:
                pass
            await self.connect()
