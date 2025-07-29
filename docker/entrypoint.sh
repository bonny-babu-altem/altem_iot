#!/bin/bash
trap 'echo "Startup failed!"; exit 1' ERR
set -e

# Source ROS2 installation
source /opt/ros/$ROS_DISTRO/setup.bash

# Source built workspace in image
source /ros_workspace/install/setup.bash

# Export environment variables if .env file exists inside container
if [ -f "/ros_workspace/.env" ]; then
    export $(grep -v '^#' /ros_workspace/.env | xargs)
fi

exec "$@"
