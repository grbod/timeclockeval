# Deployment Guide

This guide covers deploying your Streamlit app to a DigitalOcean droplet with automated GitHub deployments.

## Quick Setup

### 1. Server Setup
Run this one-time setup on your droplet:

```bash
# Download and run setup script
wget https://raw.githubusercontent.com/yourusername/timeclockchecker/main/setup-server.sh
chmod +x setup-server.sh
./setup-server.sh timeclock.yourdomain.com timeclockchecker
```

**Note**: The setup script will automatically remove any previous installation of the app (including systemd service, nginx config, app directory, and logs) before setting up the new installation. This ensures a clean deployment every time.

### 2. GitHub Secrets
Add these secrets to your GitHub repository settings:

- `HOST`: Your droplet's IP address (e.g., `203.0.113.1`)
- `USERNAME`: Your server username (usually `root` or `ubuntu`)
- `SSH_KEY`: Your private SSH key content (the entire key including headers)

### 3. Update Repository URL
Edit `setup-server.sh` and replace:
```bash
git clone https://github.com/yourusername/timeclockchecker.git
```

## Manual Commands

### Systemd Service Management
```bash
# Check service status
sudo systemctl status timeclockchecker

# View logs (real-time)
sudo journalctl -u timeclockchecker -f

# View recent logs
sudo journalctl -u timeclockchecker --since "1 hour ago"

# View application logs
sudo tail -f /var/log/timeclockchecker.log
sudo tail -f /var/log/timeclockchecker.error.log

# Restart service
sudo systemctl restart timeclockchecker

# Stop service
sudo systemctl stop timeclockchecker

# Start service
sudo systemctl start timeclockchecker

# Enable service (auto-start on boot)
sudo systemctl enable timeclockchecker
```

### Nginx Management
```bash
# Check nginx status
sudo systemctl status nginx

# Reload nginx config
sudo nginx -t && sudo systemctl reload nginx

# View nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### SSL Certificate Renewal
```bash
# Test renewal
sudo certbot renew --dry-run

# Force renewal
sudo certbot renew --force-renewal
```

## Adding More Apps

For each additional Streamlit app:

1. **Choose a port**: 8502, 8503, etc.
2. **Run setup script**:
   ```bash
   ./setup-server.sh app2.yourdomain.com myapp2 8502
   ```
3. **Create systemd service** for the new app
4. **Add GitHub secrets** for the new repository

## Troubleshooting

### App Won't Start
```bash
# Check systemd logs
sudo journalctl -u timeclockchecker -f

# Check application logs
sudo tail -20 /var/log/timeclockchecker.log
sudo tail -20 /var/log/timeclockchecker.error.log

# Check if port is in use
sudo netstat -tlnp | grep 8501

# Restart service
sudo systemctl restart timeclockchecker

# Check service status
sudo systemctl status timeclockchecker
```

### SSL Issues
```bash
# Check certificate status
sudo certbot certificates

# Test SSL configuration
sudo nginx -t
```

### GitHub Actions Failing
- Verify SSH key has correct permissions on server
- Check if `git pull` works manually on server
- Ensure app directory permissions are correct

## File Structure
```
/var/www/timeclockchecker/
├── app.py
├── main.py
├── requirements.txt
├── timeclockchecker.service
└── venv/
```

## Service Files
```
/etc/systemd/system/
└── timeclockchecker.service
```