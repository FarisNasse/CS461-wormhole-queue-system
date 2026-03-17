# Deploy on EC2 with Nginx (No AWS Load Balancer)

This guide assumes Amazon Linux 2023 on EC2 and a domain that points to the instance Elastic IP.

## 1) Install system packages

sudo dnf update -y
sudo dnf install -y nginx certbot python3-certbot-nginx
sudo systemctl enable nginx
sudo systemctl start nginx

## 2) Install and configure the app service

1. Copy deploy/systemd/wormhole.service to /etc/systemd/system/wormhole.service.
2. Create env file:
   - sudo mkdir -p /etc/wormhole
   - sudo cp deploy/systemd/wormhole.env.example /etc/wormhole/wormhole.env
   - sudo nano /etc/wormhole/wormhole.env
3. Edit these values:
   - SECRET_KEY
   - DATABASE_URL
4. Enable and start service:
   - sudo systemctl daemon-reload
   - sudo systemctl enable wormhole
   - sudo systemctl restart wormhole
5. Verify:
   - sudo systemctl status wormhole
   - curl http://127.0.0.1:8000/health

## 3) Configure Nginx

1. Copy deploy/nginx/wormhole.conf to /etc/nginx/conf.d/wormhole.conf.
2. Replace queue.example.com with your real domain in that file.
3. Validate and reload:
   - sudo nginx -t
   - sudo systemctl reload nginx

## 4) Issue TLS certificate

sudo certbot --nginx -d queue.example.com

Then recheck:
- sudo nginx -t
- sudo systemctl reload nginx

## 5) Open only required ports

EC2 security group inbound rules:
- 80/tcp from 0.0.0.0/0
- 443/tcp from 0.0.0.0/0
- 22/tcp from your admin IP

Do not expose 8000 publicly.

## 6) Validate end-to-end

- https://queue.example.com loads without certificate warning
- http://queue.example.com redirects to HTTPS
- Login/session works
- Live queue updates function (Socket.IO over WSS)
