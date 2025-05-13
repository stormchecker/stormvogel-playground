#!/bin/bash

#install system-wide server and dependencies

set -e

if [ -z "$1" ]; then
        echo "Provide argument."
        echo "Usage: $0 <server-host-user>"
        exit 1
fi

server_host="$1"

echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

#installing docker for ubuntu 
#If this does not work it may have changed: https://docs.docker.com/engine/install/ubuntu/

echo "Adding docker's official GPG key"
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo "Adding docker repo to apt"
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

echo "Installing docker"
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "Docker installed (basic sanity check)"
sudo docker --version

echo "Adding user to docker user group (such that current user can run docker wihout sudo)"
sudo usermod -aG docker "$server_host"

#installing gvisor runc docker runtime
#in this doesn't work it may have changed: https://gvisor.dev/docs/user_guide/install/

echo "Installing gvisor runtime"
(
  set -e
  ARCH=$(uname -m)
  URL=https://storage.googleapis.com/gvisor/releases/release/latest/${ARCH}
  wget ${URL}/runsc ${URL}/runsc.sha512 \
    ${URL}/containerd-shim-runsc-v1 ${URL}/containerd-shim-runsc-v1.sha512
  sha512sum -c runsc.sha512 \
    -c containerd-shim-runsc-v1.sha512
  rm -f *.sha512
  chmod a+rx runsc containerd-shim-runsc-v1
  sudo mv runsc containerd-shim-runsc-v1 /usr/local/bin
)

/usr/local/bin/runsc install
sudo systemctl reload docker

echo "Gvisor installed to check if everything is installed correctly: docker run --rm --runtime=runsc hello-world"

#Installing server other server dependencies

echo "Installing required packages..."
sudo apt install -y curl git python3 python3-pip python3-venv

#Retrospective: nodejs and npm not necesary:
#sudo apt install nodejs nmp
