import json
from typing import Any
import paho.mqtt.client as mqtt
from rclpy.impl.rcutils_logger import RcutilsLogger


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
            self.__client.connect(self.__host, self.__port, keepalive=60)
            self.__client.loop_start()
            self.__log.info('Trying to connect to ThingsBoard...')
        except Exception as e:
            self.__log.error(f'Failed to connect: {e}')

    def disconnect(self) -> None:
        self.__client.loop_stop()
        self.__client.disconnect()
        self.__log.info('Disconnected from ThingsBoard')

    def publish_data(self, data: dict[str, Any]) -> None:
        msg: str = json.dumps(data)
        self.__log.info(f'Publishing data: {msg}')
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
