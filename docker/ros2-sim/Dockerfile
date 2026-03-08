FROM arm64v8/ros:humble

ENV DEBIAN_FRONTEND=noninteractive
ENV TURTLEBOT3_MODEL=waffle
ENV ROS_DISTRO=humble

RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-humble-nav2-msgs \
    ros-humble-rclpy \
    ros-humble-rosbridge-server \
    ros-humble-teleop-twist-keyboard \
    python3-colcon-common-extensions \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY docker/ros2-sim/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
