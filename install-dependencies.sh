#!/bin/bash

# Install system dependencies for matplotlib on headless servers
echo "Installing system dependencies for matplotlib..."

# Update package list
sudo apt-get update

# Install required libraries for matplotlib backend
sudo apt-get install -y \
    python3-tk \
    tk-dev \
    libfreetype6-dev \
    pkg-config

# Install fonts to prevent matplotlib hanging
echo "Installing fonts..."
sudo apt-get install -y \
    fonts-liberation \
    fonts-dejavu-core \
    fontconfig

# Clear font cache
echo "Clearing font cache..."
fc-cache -f -v

echo "System dependencies installed successfully!"
echo "Please restart the timeclockchecker service:"
echo "sudo systemctl restart timeclockchecker"