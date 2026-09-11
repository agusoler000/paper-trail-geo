#!/usr/bin/env bash
# Manda un aviso por Telegram. Se usa cuando el vigilante encuentra que no hay video.
set -euo pipefail
[ -n "${TELEGRAM_BOT_TOKEN:-}" ] || { echo "sin TELEGRAM_BOT_TOKEN; el aviso queda en el log"; echo "$*"; exit 0; }
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d "chat_id=${TELEGRAM_CHAT_ID}" \
  --data-urlencode "text=THE LEDGER — el video de hoy NO esta subido.
$*" >/dev/null
