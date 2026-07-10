#!/usr/bin/env bash
# Launch VLC with IPTV news playlists. Defaults to the interactive navigator.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ $# -eq 0 ]]; then
  exec "$SCRIPT_DIR/news-tv.sh"
fi

case "${1:-}" in
  --interactive|-i)
    shift
    exec "$SCRIPT_DIR/news-tv.sh" "$@"
    ;;
  --help|-h)
    exec "$SCRIPT_DIR/news-tv.sh" --help
    ;;
esac

exec "$SCRIPT_DIR/news-tv.sh" "$@"
