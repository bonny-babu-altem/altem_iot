import asyncio
import json
from typing import Any, Optional
import paho.mqtt.client as mqtt
import rclpy
from rclpy.impl.rcutils_logger import RcutilsLogger

from gmqtt import Client


class MQTT:
    __slots__: tuple[str, ...] = (
        '__token',
        '__client',
        '__topic',
        '__host',
        '__port',
        '__log'
    )

    def __init__(self, token: str, log: RcutilsLogger, host: str, port: int = 1883) -> None:
        self.__token: str = token
        self.__host: str = host
        self.__port: int = port
        self.__log: RcutilsLogger = log

        self.__topic: str = "v1/devices/me/telemetry"

        # Initialize MQTT client
        self.__client = mqtt.Client()
        self.__client.username_pw_set(self.__token)

        # Bind callbacks
        self.__client.on_connect = self._on_connect
        self.__client.on_disconnect = self._on_disconnect

    @property
    def client(self) -> mqtt.Client:
        return self.__client

    def connect(self) -> None:
        try:
            self.__log.info('Trying to connect to ThingsBoard...')
            self.__client.connect(self.__host, self.__port, keepalive=60)
            self.__client.loop_start()
        except Exception as e:
            self.__log.error(f'Failed to connect: {e}')

    def disconnect(self) -> None:
        self.__client.loop_stop()
        self.__client.disconnect()
        self.__log.info('Disconnected from ThingsBoard')

    def publish_data(self, data: dict[str, Any]) -> None:
        msg: str = json.dumps(data)
        self.__log.info(
            f'Publishing data [topic: {self.__topic}, {self.__host}:{self.__port}]')
        self.__client.publish(
            topic=self.__topic,
            payload=msg.encode(),
            qos=1
        )

    def _on_connect(self, client, userdata, flags, rc) -> None:
        if rc == 0:
            self.__log.info('Successfully connected to ThingsBoard.')
        else:
            self.__log.error(f'Connection failed with return code {rc}')

    def _on_disconnect(self, client, userdata, rc) -> None:
        self.__log.error(f'Disconnected with result code {rc}')
        # If unexpected disconnect (rc != 0), try auto reconnect
        if rc != 0:
            self.__log.info('Attempting to reconnect...')
            try:
                client.reconnect()
            except Exception as e:
                self.__log.error(f'Auto-reconnect failed: {e}')


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
                keepalive=60
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
            raise RuntimeError("Client not initialized. Use 'connect'.")

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
