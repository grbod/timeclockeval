#!/bin/bash

# Server Setup Script for Streamlit App with Nginx, Let's Encrypt, and PM2
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

echo "Setting up server for $APP_NAME at $DOMAIN on port $APP_PORT"

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
echo "Installing nginx, certbot, git, python3..."
sudo apt install -y nginx certbot python3-certbot-nginx git python3-pip python3-venv curl

# Install required Python packages
echo "Installing Python development packages..."
sudo apt install -y python3-dev python3-setuptools

# Create app directory
echo "Creating application directory..."
sudo mkdir -p /var/www/$APP_NAME
sudo chown $USER:$USER /var/www/$APP_NAME

# Clone repository (you'll need to replace with your actual repo)
echo "Cloning repository..."
cd /var/www
git clone https://github.com/yourusername/$APP_NAME.git
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
ExecStart=/var/www/$APP_NAME/venv/bin/streamlit run app.py --server.port $APP_PORT --server.address 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

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
sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

# Setup auto-renewal
echo "Setting up SSL auto-renewal..."
sudo systemctl enable certbot.timer

# Configure firewall
echo "Configuring firewall..."
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

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
echo "   - HOST: $DOMAIN"
echo "   - USERNAME: $USER"
echo "   - SSH_KEY: (your private SSH key)"
echo "3. Push changes to trigger deployment"