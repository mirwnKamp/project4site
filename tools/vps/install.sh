#!/bin/bash
# One-time setup on the game VPS (run from this repo on your PC): status.json writer + nginx /site/ preview location.
#   tools/vps/install.sh            (SSH alias "contabo", see the samuraicrow-deploy skill)
# Then publish the site with tools/vps/preview.sh. Undo: tools/vps/install.sh --remove
set -euo pipefail
HOST=${P4_VPS:-contabo}
cd "$(dirname "$0")"

if [ "${1:-}" = "--remove" ]; then
  ssh "$HOST" 'set -e
    systemctl disable --now p4-site-status.timer 2>/dev/null || true
    rm -f /etc/systemd/system/p4-site-status.{service,timer} /usr/local/bin/p4-site-status /etc/nginx/snippets/p4preview.conf
    sed -i "/include snippets\/p4preview.conf;/d" /etc/nginx/sites-available/l2patch
    systemctl daemon-reload; nginx -t && systemctl reload nginx
    rm -rf /var/www/p4preview'
  exit
fi

scp p4-site-status "$HOST":/usr/local/bin/p4-site-status
ssh "$HOST" 'set -e
chmod 755 /usr/local/bin/p4-site-status
mkdir -p /var/www/p4preview/site

cat > /etc/systemd/system/p4-site-status.service <<EOF
[Unit]
Description=Write the public server status for the Project4 site
[Service]
Type=oneshot
ExecStart=/usr/local/bin/p4-site-status
Nice=10
EOF
cat > /etc/systemd/system/p4-site-status.timer <<EOF
[Unit]
Description=Project4 site status every minute
[Timer]
OnBootSec=30s
OnUnitActiveSec=60s
[Install]
WantedBy=timers.target
EOF

# Site preview at http://<vps>/site/ : clean URLs like GitHub Pages (/site/wiki serves wiki.html).
cat > /etc/nginx/snippets/p4preview.conf <<EOF
location ^~ /site/ {
	root /var/www/p4preview;
	try_files \$uri \$uri.html \$uri/ =404;
	add_header Cache-Control "no-cache";
}
location = /site/status.json {
	root /var/www/p4preview;
	add_header Cache-Control "no-store";
}
location = /site { return 301 /site/; }
EOF
grep -q "include snippets/p4preview.conf;" /etc/nginx/sites-available/l2patch ||
  sed -i "s|^\troot /var/www/l2patch;|&\n\tinclude snippets/p4preview.conf;|" /etc/nginx/sites-available/l2patch
nginx -t
systemctl reload nginx
systemctl daemon-reload
systemctl enable --now p4-site-status.timer
/usr/local/bin/p4-site-status
cat /var/www/p4preview/site/status.json'
