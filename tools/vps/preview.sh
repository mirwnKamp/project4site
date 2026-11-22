#!/bin/bash
# Publish a branch of this site to the VPS preview: http://13.140.161.129/site/
#   tools/vps/preview.sh [ref]      (default: the current branch; only committed files are sent)
set -euo pipefail
HOST=${P4_VPS:-contabo}
REF=${1:-HEAD}
cd "$(git rev-parse --show-toplevel)"
git archive --format=tar "$REF" | ssh "$HOST" 'set -e
  d=/var/www/p4preview/site
  t=$(mktemp -d /var/www/p4preview/.site-XXXXXX)
  tar -x -C "$t"
  rm -rf "$t/tools"
  if [ -f "$d/status.json" ]; then cp -p "$d/status.json" "$t/"; fi
  chmod -R a+rX "$t"; chmod 755 "$t"
  rm -rf "$d.old"; if [ -d "$d" ]; then mv "$d" "$d.old"; fi
  mv "$t" "$d"; rm -rf "$d.old"'
echo "preview: http://13.140.161.129/site/  ($(git rev-parse --short "$REF"))"
