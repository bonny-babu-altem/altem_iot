import json
from typing import Any
import rclpy
from rclpy.node import Node
from rclpy.publisher import Publisher
from rclpy.timer import Timer
from std_msgs.msg import String
from stratasys_f170.device import get_device_status
from stratasys_f170.xml_parser import parse_data
from stratasys_f170.mqtt_publisher import MQTT


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

        self.iot = MQTT(token=self.access_token,
                        host=self.tb_host, port=self.tb_port)

        self.get_logger().info(f'TB: {self.tb_host}:{self.tb_port}')
        self.get_logger().info(f'F170 IP: {self.device_ip}')

        self.iot.connect()

        self.timer: Timer = self.create_timer(0.005, self.publish_callback)

    def publish_callback(self) -> None:
        parsed_data: None | dict[str, Any] = self.get_device_data()
        if parsed_data is None:
            return

        self.msg = String()
        self.msg.data = json.dumps(parsed_data)

        self.iot.publish_data(data=parsed_data)
        self.publisher_.publish(self.msg)

    def get_device_data(self) -> None | dict[str, Any]:
        xml_data: str = get_device_status(ip=self.device_ip)
        return parse_data(xml_data=xml_data)


def main(args=None):
    rclpy.init(args=args)
    node = F170()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
