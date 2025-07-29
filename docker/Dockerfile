# docker/Dockerfile
FROM ros:jazzy

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    git curl wget \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Optional GUI tools (you can comment/uncomment later)
# RUN apt-get update && apt-get install -y \
#     ros-jazzy-rviz2 \
#     ros-jazzy-gazebo-ros-pkgs \
#     && rm -rf /var/lib/apt/lists/*

SHELL ["/bin/bash", "-c"]

# Source ROS setup in bash
RUN echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc

# Setup workspace
ENV ROS_WS=/ros_workspace
WORKDIR $ROS_WS

COPY ./ros_workspace/src ./src

RUN apt-get update && rosdep update && \
    rosdep install --from-paths src --ignore-src -r -y

RUN . /opt/ros/jazzy/setup.bash && colcon build

RUN echo "source $ROS_WS/install/setup.bash" >> ~/.bashrc
