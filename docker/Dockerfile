FROM ros:jazzy

RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-colcon-common-extensions \
    build-essential \
    net-tools \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --break-system-packages python-dotenv requests paho-mqtt

COPY ./ros_workspace /ros_workspace

WORKDIR /ros_workspace

# Build the ROS2 workspace inside the image
RUN . /opt/ros/jazzy/setup.sh && \
    colcon build --symlink-install

# Copy entrypoint after build for cache efficiency
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["ros2", "launch", "stratasys_f170", "f170.launch.py"]
