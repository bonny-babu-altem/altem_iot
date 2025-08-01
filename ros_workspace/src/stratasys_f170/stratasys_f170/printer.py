import asyncio
import json
from threading import Thread
from typing import Any

from httpx import Response

import rclpy
from rclpy.impl.rcutils_logger import RcutilsLogger
from rclpy.node import Node
from rclpy.publisher import Publisher
from std_msgs.msg import String

from stratasys_f170.device import DeviceRequest, wait_for_device_ip
from stratasys_f170.xml_parser import parse_data
from stratasys_f170.mqtt_publisher import MQTTClient, wait_for_broker


class F170(Node):
    def __init__(self) -> None:
        super().__init__('f170', namespace="printer/stratasys")

        self.access_token: str = self.declare_parameter(
            'access_token', '').get_parameter_value().string_value

        self.device_ip: str = self.declare_parameter(
            'device_ip', 'localhost').get_parameter_value().string_value

        self.tb_host: str = self.declare_parameter(
            'tb_host', 'localhost').get_parameter_value().string_value

        self.tb_port: int = self.declare_parameter(
            'tb_port', 1883).get_parameter_value().integer_value

        self.publisher_: Publisher = self.create_publisher(
            String, 'status', 10)

        self.get_logger().info(f'TB: {self.tb_host}:{self.tb_port}')
        self.get_logger().info(f'F170 IP: {self.device_ip}')

        _log: RcutilsLogger = self.get_logger()

        self.request = DeviceRequest(url=self.device_ip, log=_log)
        self.iot = MQTTClient(
            token=self.access_token, log=_log,
            host=self.tb_host, port=self.tb_port
        )

        self.loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
        self.thread = Thread(target=self.start_loop, daemon=True)
        self.thread.start()
        asyncio.run_coroutine_threadsafe(self.publish_data(), self.loop)

    def start_loop(self) -> None:
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def publish_data(self) -> None:
        _log: RcutilsLogger = self.get_logger()

        await wait_for_device_ip(ip=self.device_ip, delay=5, logger=_log)
        await wait_for_broker(host=self.tb_host, delay=5, logger=_log)

        await self.request.connect()
        await self.iot.connect()

        try:
            while rclpy.ok():
                try:
                    response: Response = await self.request.get()

                except Exception as e:
                    self.get_logger().error(f"HTTP fetch failed: {e}")
                    # await wait_for_device_ip(ip=self.device_ip, delay=5, logger=self.get_logger())
                    continue

                parsed_data: None | dict[str, Any] = parse_data(
                    xml_data=response.text)
                if parsed_data is None:
                    self.get_logger().warning('No data received from f170 device')
                    return

                self.msg = String()
                self.msg.data = json.dumps(parsed_data)

                await self.iot.publish_data(data=parsed_data)
                self.publisher_.publish(self.msg)
        finally:
            await self.request.disconnect()

    def destroy_node(self) -> None:
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join()

        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = F170()
    try:
        rclpy.spin(node)
    except Exception as e:
        node.get_logger().error(f"An Exception: {e} has occurred.")
    finally:
        node.destroy_node()
        rclpy.shutdown()
