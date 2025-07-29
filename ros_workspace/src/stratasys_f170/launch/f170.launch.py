import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from dotenv import load_dotenv
from pathlib import Path


def generate_launch_description() -> LaunchDescription:
    # Use source workspace to locate .env
    this_package_dir = get_package_share_directory('stratasys_f170')
    # Go two levels up to ros_workspace/
    workspace_root = Path(this_package_dir).absolute()
    dotenv_path = (workspace_root / "../../../../../").resolve()

    load_dotenv(dotenv_path / '.env')

    access_token = os.getenv("F170_TB_MQTT_ACCESS_TOKEN", "")

    config_file = os.path.join(
        get_package_share_directory('stratasys_f170'),
        'config',
        'f170_params.yaml'
    )

    return LaunchDescription([
        Node(
            package='stratasys_f170',
            executable='f170_node',
            name='f170',
            namespace='printer/stratasys',
            parameters=[
                config_file,
                {'access_token': access_token},
            ],
            output='screen'
        )
    ])
