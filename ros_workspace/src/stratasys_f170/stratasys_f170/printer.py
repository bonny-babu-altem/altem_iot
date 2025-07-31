import asyncio
import json
from typing import Any

import rclpy
from rclpy.node import Node
from rclpy.publisher import Publisher
from std_msgs.msg import String

from stratasys_f170.device import DeviceClient
from stratasys_f170.xml_parser import parse_data
from stratasys_f170.mqtt_publisher import MQTTClient


class F170(Node):
    def __init__(self) -> None:
        super().__init__('f170', namespace='printer/stratasys')

        # Parameters
        self.access_token: str = self.declare_parameter(
            'access_token', '').get_parameter_value().string_value

        self.device_ip: str = self.declare_parameter(
            'device_ip', 'localhost').get_parameter_value().string_value

        self.tb_host: str = self.declare_parameter(
            'tb_host', 'localhost').get_parameter_value().string_value

        self.tb_port: int = self.declare_parameter(
            'tb_port', 1883).get_parameter_value().integer_value

        # ROS Publisher
        self.publisher_: Publisher = self.create_publisher(
            String, 'status', 10)

        self.get_logger().info(f"Configured F170 for {self.device_ip}")
        self.get_logger().info(f"MQTT → {self.tb_host}:{self.tb_port}")

    async def run_async(self) -> None:
        self.get_logger().info("Connecting....")
        try:
            async with MQTTClient(
                token=self.access_token,
                host=self.tb_host,
                port=self.tb_port,
                log=self.get_logger()
            ) as mqtt:

                while rclpy.ok():
                    try:
                        async with DeviceClient(ip=self.device_ip, log=self.get_logger()) as device:
                            xml: str = await device.get_status()
                            parsed: None | dict[str, Any] = parse_data(xml)
                            if parsed:
                                self.publish(parsed)
                                await mqtt.publish_data(data=parsed)

                    except Exception as e:
                        self.get_logger().error(f"Error polling device: {e}")

                    await asyncio.sleep(1.0)

        except Exception as e:
            self.get_logger().error(f"MQTT initialization failed: {e}")

    def publish(self, data: dict[str, Any]) -> None:
        msg = String()
        msg.data = json.dumps(data)
        self.publisher_.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = F170()

    loop = asyncio.get_event_loop()

    try:
        # Start the background asyncio task manually
        loop.create_task(node.run_async())

        # Now spin the ROS node (blocking)
        rclpy.spin(node)

    except KeyboardInterrupt:
        node.get_logger().info("KeyboardInterrupt received.")
    finally:
        node.destroy_node()
        rclpy.shutdown()

        # Cleanup asyncio loop
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        try:
            loop.run_until_complete(asyncio.gather(
                *pending, return_exceptions=True))
        except Exception:
            pass
        loop.close()
