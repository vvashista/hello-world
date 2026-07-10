#!/usr/bin/env bash
# Launch VLC with IPTV news playlists for an IPTV-like channel browsing experience.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
IPTV_DIR="$REPO_ROOT/iptv"

usage() {
  cat <<'EOF'
Usage: watch-news.sh [english|hindi|all] [--channel N]

Open curated news channel playlists in VLC.

  english   English news channels (default)
  hindi     Hindi news channels
  all       Combined English + Hindi playlist

Options:
  --channel N   Start on channel number N (1-based)
  --list        Print available playlists and exit
  --help        Show this help

Examples:
  ./scripts/watch-news.sh
  ./scripts/watch-news.sh hindi
  ./scripts/watch-news.sh all --channel 3
EOF
}

pick_vlc() {
  if command -v cvlc >/dev/null 2>&1; then
    echo "cvlc"
  elif command -v vlc >/dev/null 2>&1; then
    echo "vlc"
  else
    echo "VLC is not installed. Install it with:" >&2
    echo "  Ubuntu/Debian: sudo apt install vlc" >&2
    echo "  macOS:         brew install --cask vlc" >&2
    echo "  Windows:       https://www.videolan.org/vlc/" >&2
    exit 1
  fi
}

playlist_for() {
  case "$1" in
    english) echo "$IPTV_DIR/english-news.m3u" ;;
    hindi) echo "$IPTV_DIR/hindi-news.m3u" ;;
    all) echo "$IPTV_DIR/all-news.m3u" ;;
    *) echo "Unknown playlist: $1" >&2; usage; exit 1 ;;
  esac
}

list_channels() {
  local playlist="$1"
  local n=0
  while IFS= read -r line; do
    if [[ "$line" == \#EXTINF* ]]; then
      n=$((n + 1))
      name="${line##*,}"
      printf "%3d. %s\n" "$n" "$name"
    fi
  done < "$playlist"
}

main() {
  local lang="english"
  local channel=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      english|hindi|all) lang="$1" ;;
      --channel) shift; channel="${1:-}" ;;
      --list)
        for kind in english hindi all; do
          local_file="$(playlist_for "$kind")"
          echo "== $kind ($local_file) =="
          list_channels "$local_file"
          echo
        done
        exit 0
        ;;
      --help|-h) usage; exit 0 ;;
      *) echo "Unknown argument: $1" >&2; usage; exit 1 ;;
    esac
    shift
  done

  local playlist
  playlist="$(playlist_for "$lang")"
  if [[ ! -f "$playlist" ]]; then
    echo "Playlist not found: $playlist" >&2
    echo "Run: python3 scripts/build-playlists.py" >&2
    exit 1
  fi

  local vlc
  vlc="$(pick_vlc)"

  echo "Opening $lang news playlist in VLC..."
  echo "Playlist: $playlist"
  echo
  echo "IPTV tips in VLC:"
  echo "  - View > Playlist (Ctrl+L) to browse channels"
  echo "  - Use Up/Down or PgUp/PgDn to change channels"
  echo "  - Channels are grouped under 'English News' / 'Hindi News'"
  echo

  if [[ -n "$channel" ]]; then
    local url
    url="$(awk -v n="$channel" '
      /^#EXTINF/ { idx++ }
      idx == n && /^https?:/ { print; exit }
    ' "$playlist")"
    if [[ -z "$url" ]]; then
      echo "Channel $channel not found in playlist." >&2
      exit 1
    fi
    exec "$vlc" "$url"
  fi

  exec "$vlc" "$playlist"
}

main "$@"
