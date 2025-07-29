FROM ros:jazzy

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-colcon-common-extensions \
    build-essential \
    net-tools \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
RUN pip install --break-system-packages python-dotenv requests paho-mqtt

# Copy ROS workspace source code into image
COPY ./ros_workspace /ros_workspace

# Build workspace inside the image
WORKDIR /ros_workspace

# Source ROS setup script and build
RUN . /opt/ros/jazzy/setup.sh && \
    colcon build --symlink-install

# Copy entrypoint with executable permission
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Entrypoint and default command
ENTRYPOINT ["/entrypoint.sh"]
CMD ["ros2", "launch", "stratasys_f170", "f170.launch.py"]
