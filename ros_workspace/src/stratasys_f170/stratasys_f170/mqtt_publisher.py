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

        self.__client = mqtt.Client()
        self.__client.username_pw_set(self.__token)
        self.__client.on_disconnect = lambda _, __, rc: self.__log.error(
            f"Disconnected with result code {rc}")  # type: ignore

    @property
    def client(self) -> mqtt.Client:
        return self.__client

    def connect(self) -> None:
        self.__client.connect(self.__host, self.__port, 60)
        self.__client.loop_start()

        self.__log.info('Connected to thingsboard...')

    def disconnect(self) -> None:
        self.__client.loop_stop()
        self.__client.disconnect()

    def publish_data(self, data: dict[str, Any]) -> None:
        msg: str = json.dumps(data)

        self.__log.debug(msg)

        self.__client.publish(
            topic=self.__topic,
            payload=msg.encode(),
            qos=1
        )
