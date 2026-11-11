#!/bin/zsh
# Sales Gym: lanciato da giro.sh ogni 10 minuti. Nota + email una volta al giorno, poi la cartella iCloud.
set -u
DIR="$HOME/Projects/sales-gym"
cd "$DIR" || exit 1
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
export OBSIDIAN_SYNC_CHILD=1
LOCK="state/gym.lock"
mkdir -p logs state
find "$LOCK" -maxdepth 0 -mmin +120 -exec rmdir {} \; 2>/dev/null   # lock rimasto da un riavvio a metà giro
mkdir "$LOCK" 2>/dev/null || exit 0
trap 'rmdir "$LOCK"' EXIT
exec >>"logs/$(date +%F).log" 2>&1
"${GYM_PY:-python3}" gym.py auto
