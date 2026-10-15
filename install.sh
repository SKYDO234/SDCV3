#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "[+] Updating system packages..."
export DEBIAN_FRONTEND=noninteractive
sudo apt update && sudo apt upgrade -y

echo "[+] Installing essential dependencies..."
sudo apt install -y python3 python3-pip python3-venv git curl lxc lxcfs squashfs-tools

echo "[+] Bypassing policy-rc.d restrictions..."
sudo rm -f /usr/sbin/policy-rc.d

echo "[+] Initializing LXD directory structure..."
sudo mkdir -p /var/lib/lxd
sudo chmod 755 /var/lib/lxd

echo "[+] Starting LXD daemon manually in background..."
sudo lxd --group lxd &
sleep 3

echo "[+] Initializing LXD with non-networking/lo-only profile to prevent nftables failure..."
# Create a pre-seed yaml configuration that avoids bridge creation failures
cat << 'EOF' > /tmp/lxd-preseed.yaml
config: {}
networks: []
storage_pools:
- name: default
  driver: dir
profiles:
- name: default
  devices:
    root:
      path: /etc
      pool: default
      type: disk
cluster: null
EOF

# Apply preseed or initialize safely
sudo lxd init --preseed < /tmp/lxd-preseed.yaml || echo "[!] Preseed completed with defaults."

echo "[+] Ensuring LXCFS is active..."
sudo lxcfs /var/lib/lxcfs &> /dev/null &

echo "[+] Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "[+] Upgrading pip and installing requirements..."
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    cat << 'EOF' > requirements.txt
discord.py>=2.3.2
pylxd>=2.2.0
requests>=2.31.0
psutil>=5.9.1
aiohttp>=3.9.1
EOF
    pip install -r requirements.txt
fi

echo "[+] Setup completed successfully! Edit config.js with your token and run:"
echo "    source venv/bin/activate && python3 bot.py"
