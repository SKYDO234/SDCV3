#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "[+] Updating system packages..."
sudo apt update && sudo apt upgrade -y

echo "[+] Installing essential dependencies (Python 3, Pip, Git, Curl, LXC, LXCFS)..."
sudo apt install -y python3 python3-pip python3-venv git curl lxd lxcfs bridge-utils squashfs-tools

echo "[+] Initializing LXD..."
# Pre-seed or non-interactive lxd init if not already initialized
if ! lxc profile list > /dev/null 2>&1; then
    sudo lxd init --auto
else
    echo "[*] LXD is already initialized."
fi

echo "[+] Ensuring LXCFS service is running..."
sudo systemctl enable --now lxcfs

echo "[+] Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "[+] Upgrading pip and installing requirements..."
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "[!] requirements.txt not found! Please make sure it's in the directory."
fi

echo "[+] Installation complete! Please edit config.js with your Discord Bot Token and Admin IDs, then run: source venv/bin/activate && python3 bot.py"
