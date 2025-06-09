#!/bin/bash

# Server Setup Script for Streamlit App with Nginx, Let's Encrypt, and systemd
# Usage: bash setup-server.sh yourdomain.com timeclockchecker

set -e

DOMAIN=$1
APP_NAME=$2
APP_PORT=${3:-8501}

if [ -z "$DOMAIN" ] || [ -z "$APP_NAME" ]; then
    echo "Usage: bash setup-server.sh <domain> <app_name> [port]"
    echo "Example: bash setup-server.sh timeclock.example.com timeclockchecker 8501"
    exit 1
fi

# Validate domain format
if ! echo "$DOMAIN" | grep -E '^[a-zA-Z0-9][a-zA-Z0-9.-]+[a-zA-Z0-9]$' > /dev/null; then
    echo "Error: Invalid domain format"
    exit 1
fi

# Validate app name (alphanumeric and hyphens only)
if ! echo "$APP_NAME" | grep -E '^[a-zA-Z0-9-]+$' > /dev/null; then
    echo "Error: App name must contain only alphanumeric characters and hyphens"
    exit 1
fi

# Allow running as root for simplified deployment

echo "Setting up server for $APP_NAME at $DOMAIN on port $APP_PORT"

# Check for and remove previous installation
if [ -d "/var/www/$APP_NAME" ] || [ -f "/etc/systemd/system/$APP_NAME.service" ] || [ -f "/etc/nginx/sites-available/$APP_NAME" ]; then
    echo "Found previous installation. Removing..."
    
    # Stop and disable service if it exists
    if systemctl list-units --all | grep -q "$APP_NAME.service"; then
        echo "Stopping and disabling existing service..."
        sudo systemctl stop $APP_NAME || true
        sudo systemctl disable $APP_NAME || true
    fi
    
    # Remove systemd service
    if [ -f "/etc/systemd/system/$APP_NAME.service" ]; then
        echo "Removing systemd service..."
        sudo rm -f /etc/systemd/system/$APP_NAME.service
        sudo systemctl daemon-reload
    fi
    
    # Remove nginx configuration
    if [ -f "/etc/nginx/sites-enabled/$APP_NAME" ]; then
        echo "Removing nginx configuration..."
        sudo rm -f /etc/nginx/sites-enabled/$APP_NAME
    fi
    if [ -f "/etc/nginx/sites-available/$APP_NAME" ]; then
        sudo rm -f /etc/nginx/sites-available/$APP_NAME
    fi
    sudo nginx -t && sudo systemctl reload nginx || true
    
    # Remove application directory
    if [ -d "/var/www/$APP_NAME" ]; then
        echo "Removing application directory..."
        sudo rm -rf /var/www/$APP_NAME
    fi
    
    # Remove log files
    if [ -f "/var/log/$APP_NAME.log" ] || [ -f "/var/log/$APP_NAME.error.log" ]; then
        echo "Removing log files..."
        sudo rm -f /var/log/$APP_NAME.log /var/log/$APP_NAME.error.log
    fi
    
    echo "Previous installation removed."
fi

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
echo "Installing nginx, certbot, git, python3..."
sudo apt install -y nginx certbot python3-certbot-nginx git python3-pip python3-venv curl

# Install required Python packages
echo "Installing Python development packages..."
sudo apt install -y python3-dev python3-setuptools

# Install matplotlib system dependencies
echo "Installing matplotlib dependencies..."
sudo apt install -y python3-tk tk-dev libfreetype6-dev pkg-config

# Install fonts to prevent matplotlib hanging
echo "Installing fonts..."
sudo apt install -y fonts-liberation fonts-dejavu-core fontconfig
fc-cache -f -v

# Configure firewall early for security
echo "Configuring firewall..."
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

# Create app directory
echo "Creating application directory..."
sudo mkdir -p /var/www/$APP_NAME
sudo chown $USER:$USER /var/www/$APP_NAME

# Clone repository
echo "Cloning repository..."
cd /var/www
git clone https://github.com/grbod/timeclockeval.git $APP_NAME
cd $APP_NAME

# Create virtual environment and install dependencies
echo "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create systemd service file
echo "Creating systemd service..."
sudo tee /etc/systemd/system/$APP_NAME.service << EOF
[Unit]
Description=Streamlit App - $APP_NAME
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/var/www/$APP_NAME
Environment=PATH=/var/www/$APP_NAME/venv/bin
Environment=PYTHONPATH=/var/www/$APP_NAME
ExecStart=/var/www/$APP_NAME/venv/bin/streamlit run app.py --server.port $APP_PORT --server.address 0.0.0.0
Restart=always
RestartSec=10
StandardOutput=append:/var/log/$APP_NAME.log
StandardError=append:/var/log/$APP_NAME.error.log

[Install]
WantedBy=multi-user.target
EOF

# Create log files with proper permissions
echo "Setting up logging..."
sudo touch /var/log/$APP_NAME.log /var/log/$APP_NAME.error.log
sudo chown $USER:$USER /var/log/$APP_NAME.log /var/log/$APP_NAME.error.log

# Enable and start the service
echo "Starting systemd service..."
sudo systemctl daemon-reload
sudo systemctl enable $APP_NAME
sudo systemctl start $APP_NAME

# Create nginx configuration
echo "Configuring nginx..."
sudo tee /etc/nginx/sites-available/$APP_NAME << EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://localhost:$APP_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF

# Enable nginx site
sudo ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Setup SSL with Let's Encrypt
echo "Setting up SSL certificate..."
sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email webmaster@$DOMAIN || echo 'Warning: SSL setup failed - you may need to configure manually'

# Setup auto-renewal
echo "Setting up SSL auto-renewal..."
sudo systemctl enable certbot.timer

echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Your app should be available at: https://$DOMAIN"
echo "📊 Service status: sudo systemctl status $APP_NAME"
echo "🔄 Service logs: sudo journalctl -u $APP_NAME -f"
echo "🛠️  Service restart: sudo systemctl restart $APP_NAME"
echo ""
echo "Next steps:"
echo "1. Update your GitHub repository URL in this script"
echo "2. Add these secrets to your GitHub repository:"
echo "   - HOST: (your server IP address)"
echo "   - USERNAME: $USER"
echo "   - SSH_KEY: (your private SSH key)"
echo "3. Push changes to trigger deployment"