set -eo pipefail
cd "$HOME"
mkdir -p evidence
. /etc/os-release
echo "$PRETTY_NAME $VERSION_CODENAME $(dpkg --print-architecture)"
sudo apt update -qq
sudo apt install -y -qq curl ca-certificates git software-properties-common locales
sudo add-apt-repository -y universe
sudo locale-gen en_US.UTF-8
export LANG=en_US.UTF-8
locale charmap
ros_source_version=$(curl -fsSL -o /dev/null -w '%{url_effective}' https://github.com/ros-infrastructure/ros-apt-source/releases/latest)
ros_source_version=${ros_source_version##*/}
curl -fL --retry 3 -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ros_source_version}/ros2-apt-source_${ros_source_version}.noble_all.deb"
sudo dpkg -i /tmp/ros2-apt-source.deb
sudo apt update -qq
sudo apt install -y -qq ros-jazzy-ros-base ros-jazzy-rqt-plot ros-jazzy-rqt-reconfigure python3-colcon-common-extensions python3-matplotlib
source /opt/ros/jazzy/setup.bash
echo "$ROS_DISTRO"
mkdir -p ~/rm_ws/src
git clone https://github.com/lazyerZZZ/rm-tuning-lab.git ~/rm_ws/src/rm-tuning-lab
cd ~/rm_ws
colcon build --symlink-install --packages-select rm_tuning_lab
source install/setup.bash
ros2 pkg prefix rm_tuning_lab
