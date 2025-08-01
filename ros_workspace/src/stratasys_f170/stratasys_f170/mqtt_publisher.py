import asyncio
import json
from typing import Any, Optional
import rclpy
from rclpy.impl.rcutils_logger import RcutilsLogger

from gmqtt import Client


class MQTTClient:
    __slots__: tuple[str, ...] = (
        '_token',
        '_client',
        '_topic',
        '_host',
        '_port',
        '_log',
        '_connected',
    )

    def __init__(self, token: str, log: RcutilsLogger, host: str, port: int = 1883) -> None:
        self._token: str = token
        self._host: str = host
        self._port: int = port
        self._log: RcutilsLogger = log

        self._client: Client

        self._topic: str = "v1/devices/me/telemetry"

        self._connected = asyncio.Event()

    async def _is_client(self) -> bool:
        return hasattr(self, '_client')

    async def connect(self) -> None:
        if not await self._is_client():
            self._log.info(f'Trying to connect to {self._host}:{self._port}')
            self._client = Client(client_id=f'id-client-{id(self)}')
            self._client.set_auth_credentials(self._token, None)

            self._client.set_config(
                {
                    'reconnect_retries': 10,
                    'reconnect_delay': 60
                }
            )

            self._client.on_connect = self._on_connect
            self._client.on_disconnect = self._on_disconnect

            await self._client.connect(
                self._host, self._port,
                keepalive=10
            )

            await self._connected.wait()

    async def disconnect(self) -> None:
        if await self._is_client():
            await self._client.disconnect()

    def _on_connect(self, *_) -> None:
        self._connected.set()
        self._log.info('Successfully connected to ThingsBoard.')

    def _on_disconnect(self, *_) -> None:
        self._connected.clear()
        self._log.warn("Disconnected from ThingsBoard. Reconnecting...")

    async def publish_data(self, data: dict[str, Any], qos: int = 1, retain: bool = False) -> None:
        msg: str = json.dumps(data)

        if not self._connected.is_set():
            self._log.warn("Client not initialized. Use 'connect'.")
            return

        if not self._client.is_connected:
            self._log.warn("Client is disconnected.")
            return

        self._log.info(
            f'Publishing data [topic: {self._topic}, {self._host}:{self._port}]')

        self._client.publish(self._topic, msg, qos, retain)


async def wait_for_broker(
        host: str, port: int = 1883,
        delay: float = 2.0, max_attempts: int = 0,
        logger: Optional[RcutilsLogger] = None) -> bool:

    attempt = 0
    while rclpy.ok():
        try:
            _, writer = await asyncio.open_connection(host, port)
            writer.close()
            await writer.wait_closed()

            if logger:
                logger.info(f"Broker at {host}:{port} is reachable.")
            return True

        except (OSError, ConnectionRefusedError):
            attempt += 1
            msg: str = f"Broker at {host}:{port} not reachable. Attempt {attempt}"
            if logger:
                logger.warn(msg)
            else:
                print(msg)

            if max_attempts and attempt >= max_attempts:
                if logger:
                    logger.error(
                        f"Broker not reachable after {max_attempts} attempts.")
                return False

        await asyncio.sleep(delay)

    return False
