#!/bin/bash

#install local server and dependencies

set -e

if [ -z "$USER" ]; then
    echo "USER variable not set, make sure user variable is set to user name"
    exit 1
fi

cd "$HOME"

echo "Checking versions..."
#node -v
#npm -v
python3 --version
pip3 --version

REPO_URL="git@github.com:GiPHouse/Stormvogel-2025.git"
PROJECT_DIR="/home/$USER/Stormvogel-2025"
VENV_DIR="$PROJECT_DIR/venv"

cd $PROJECT_DIR

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment"
    python3 -m venv $VENV_DIR
fi

echo "Activating virtual environment"
source $VENV_DIR/bin/activate

echo "Upgrading pip"
pip install --upgrade pip

cd backend

if [ -f "requirements.txt" ]; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
fi

cd ..

echo "Deactivate virtual environment"
deactivate

#cd frontend

#if [ -f "package.json" ]; then
#    echo "Installing Node dependencies..."
#    npm install
#fi

#cd ..

echo "Setup complete!"
