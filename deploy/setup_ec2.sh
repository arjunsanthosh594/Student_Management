#!/usr/bin/env bash
# ============================================================
# Ubuntu EC2 Automated Server Setup Script
# Student Management System
# Run on clean Ubuntu 22.04 / 24.04 LTS:
#   chmod +x deploy/setup_ec2.sh
#   sudo ./deploy/setup_ec2.sh
# ============================================================

set -e

echo "============================================================"
echo " Starting EC2 Provisioning for Student Management System    "
echo "============================================================"

# 1. System packages update
echo "[1/6] Updating system packages..."
apt-get update && apt-get upgrade -y
apt-get install -y python3 python3-pip python3-venv nginx git curl libmysqlclient-dev

# 2. Setup logging directory
echo "[2/6] Configuring log directories..."
mkdir -p /var/log/sms
chown -R ubuntu:www-data /var/log/sms
chmod -R 775 /var/log/sms

# 3. Setup systemd unit
echo "[3/6] Setting up systemd service..."
cp /home/ubuntu/Student-Management-System/deploy/sms.service /etc/systemd/system/sms.service
systemctl daemon-reload

# 4. Setup Nginx reverse proxy
echo "[4/6] Configuring Nginx..."
rm -f /etc/nginx/sites-enabled/default
cp /home/ubuntu/Student-Management-System/deploy/nginx.conf /etc/nginx/sites-available/sms
ln -sf /etc/nginx/sites-available/sms /etc/nginx/sites-enabled/sms
nginx -t
systemctl restart nginx

# 5. Enable firewall rules
echo "[5/6] Configuring UFW firewall..."
ufw allow 'Nginx Full'
ufw allow OpenSSH
echo "y" | ufw enable || true

# 6. Service activation reminder
echo "[6/6] Finalizing..."
echo "============================================================"
echo " Server Setup Complete!                                     "
echo " Next steps for the operator:                              "
echo "  1. cd /home/ubuntu/Student-Management-System              "
echo "  2. python3 -m venv venv && source venv/bin/activate      "
echo "  3. pip install -r requirements.txt                        "
echo "  4. cp .env.example .env (and configure RDS/S3 parameters) "
echo "  5. python scripts/init_db.py && python scripts/seed_db.py "
echo "  6. sudo systemctl enable --now sms.service                "
echo "  7. sudo systemctl status sms.service                      "
echo "============================================================"
