# Quick Setup on bbmr-drivetimes-prod

## SSH in
ssh -i "FTP Server.pem" ubuntu@44.244.49.134

## Install
sudo apt update && sudo apt install -y nginx python3 python3-requests

## Create folders
sudo mkdir -p /var/www/drivetimes/logos /opt/drivetimes
sudo chown -R $USER:$USER /var/www/drivetimes /opt/drivetimes

## Upload (use FileZilla or scp from your laptop)
index.html → /var/www/drivetimes/
update_all.py → /opt/drivetimes/
drivetimes.nginx.conf → /tmp/

## Configure nginx
sudo cp /tmp/drivetimes.nginx.conf /etc/nginx/sites-available/drivetimes
sudo ln -s /etc/nginx/sites-available/drivetimes /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

## Set cron (paste both lines)
crontab -e
TOMTOM_KEY=your_tomtom_key_here
*/5 * * * * /usr/bin/python3 /opt/drivetimes/update_all.py >> /var/log/drivetimes.log 2>&1

## Test
TOMTOM_KEY=your_key /usr/bin/python3 /opt/drivetimes/update_all.py
ls -l /var/www/drivetimes/*.json

## Open
http://44.244.49.134/?base=bearmountain
