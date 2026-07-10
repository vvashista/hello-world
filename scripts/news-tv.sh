#!/usr/bin/env bash
# Interactive news channel navigator for VLC — pick by number, name, or language.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
IPTV_DIR="$REPO_ROOT/iptv"
CATALOG="$IPTV_DIR/channels.json"
PYTHON="${PYTHON:-python3}"

BOLD='\033[1m'
DIM='\033[2m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RESET='\033[0m'

usage() {
  cat <<'EOF'
Usage: news-tv.sh [options]

Interactive news channel navigator for VLC.

Options:
  --lang hindi|english|all   Filter channels by language
  --channel N                Jump directly to channel number (101+)
  --search TEXT              Search channel by name
  --list                     Print channel guide and exit
  --help                     Show this help

With no options, opens an interactive menu.

VLC controls once playing:
  Ctrl+L       Playlist sidebar (grouped by language)
  PgUp / PgDn  Previous / next channel
  F            Fullscreen
EOF
}

ensure_catalog() {
  if [[ ! -f "$CATALOG" ]]; then
    echo "Building channel catalog..."
    "$PYTHON" "$SCRIPT_DIR/build-playlists.py"
  fi
}

pick_vlc() {
  if command -v vlc >/dev/null 2>&1; then
    echo "vlc"
  elif command -v cvlc >/dev/null 2>&1; then
    echo "cvlc"
  else
    echo "VLC is not installed." >&2
    exit 1
  fi
}

print_header() {
  printf '\n%s╔══════════════════════════════════════════╗%s\n' "$CYAN" "$RESET"
  printf '%s║%s  %s📺  NEWS TV%s — Channel Navigator        %s║%s\n' "$CYAN" "$RESET" "$BOLD" "$RESET" "$CYAN" "$RESET"
  printf '%s╚══════════════════════════════════════════╝%s\n\n' "$CYAN" "$RESET"
}

print_channels() {
  local lang="$1"
  "$PYTHON" - "$lang" "$CATALOG" <<'PY'
import json, sys
from pathlib import Path

catalog = json.loads(Path(sys.argv[2]).read_text())
lang = sys.argv[1]
groups = []
if lang in ("all", "hindi"):
    groups.append(("Hindi News", catalog.get("hindi", [])))
if lang in ("all", "english"):
    groups.append(("English News", catalog.get("english", [])))

for title, channels in groups:
    print(f"\n{title}")
    print("-" * len(title))
    for ch in channels:
        print(f"  {ch['number']:03d}  {ch['label']}")
PY
}

search_channels() {
  local lang="$1"
  local query="$2"
  "$PYTHON" - "$lang" "$query" <<'PY'
import json, sys
from pathlib import Path

catalog = json.loads(Path(sys.argv[2]).read_text())
lang, query = sys.argv[1], sys.argv[3].lower()
pool = []
if lang in ("all", "hindi"):
    pool.extend(catalog.get("hindi", []))
if lang in ("all", "english"):
    pool.extend(catalog.get("english", []))

matches = [ch for ch in pool if query in ch["label"].lower()]
for ch in matches:
    print(f"{ch['number']}\t{ch['label']}\t{ch['language']}")
PY
"$CATALOG"
}

resolve_channel() {
  local lang="$1"
  local query="$2"
  "$PYTHON" - "$lang" "$query" "$CATALOG" <<'PY'
import json, sys
from pathlib import Path

catalog = json.loads(Path(sys.argv[3]).read_text())
lang, query = sys.argv[1], sys.argv[2].strip()
pool = []
if lang in ("all", "hindi"):
    pool.extend(catalog.get("hindi", []))
if lang in ("all", "english"):
    pool.extend(catalog.get("english", []))

if query.isdigit():
    number = int(query)
    for ch in pool:
        if ch["number"] == number:
            print(json.dumps(ch))
            sys.exit(0)
    sys.exit(1)

q = query.lower()
matches = [ch for ch in pool if q in ch["label"].lower()]
if len(matches) == 1:
    print(json.dumps(matches[0]))
elif len(matches) > 1:
    print(json.dumps({"ambiguous": [m["number"] for m in matches], "matches": matches}))
else:
    sys.exit(1)
PY
}

launch_vlc() {
  local lang="$1"
  local channel_json="$2"
  local vlc playlist temp
  vlc="$(pick_vlc)"

  case "$lang" in
    hindi) playlist="$IPTV_DIR/hindi-news.m3u" ;;
    english) playlist="$IPTV_DIR/english-news.m3u" ;;
    all) playlist="$IPTV_DIR/all-news.m3u" ;;
  esac

  temp="$("$PYTHON" - "$playlist" "$channel_json" <<'PY'
import json, sys
from pathlib import Path

playlist_path = Path(sys.argv[1])
channel = json.loads(sys.argv[2])
lines = playlist_path.read_text(encoding="utf-8").splitlines()

blocks = []
current = []
for line in lines:
    if line.startswith("#EXTINF"):
        if current:
            blocks.append(current)
        current = [line]
    elif current:
        current.append(line)
if current:
    blocks.append(current)

selected = None
others = []
for block in blocks:
    if channel["url"] in block:
        selected = block
    else:
        others.append(block)

header = [line for line in lines if line.startswith("#EXTM3U") or line.startswith("#PLAYLIST")]
out = header[:]
if any(line.startswith("#EXTGRP") for line in lines):
    out.append(f"#EXTGRP:{channel['group']}")
if selected:
    out.extend(selected)
for block in others:
    out.extend(block)

temp = playlist_path.parent / ".start-channel.m3u"
temp.write_text("\n".join(out) + "\n", encoding="utf-8")
print(temp)
PY
)"

  local label number
  label="$(echo "$channel_json" | "$PYTHON" -c 'import json,sys; print(json.load(sys.stdin)["label"])')"
  number="$(echo "$channel_json" | "$PYTHON" -c 'import json,sys; print(json.load(sys.stdin)["number"])')"

  printf '\n%s▶ Starting channel %03d · %s%s\n' "$GREEN" "$number" "$label" "$RESET"
  printf '%s  Playlist tree enabled — use Ctrl+L to browse groups%s\n\n' "$DIM" "$RESET"

  exec "$vlc" \
    --playlist-autostart \
    --playlist-tree \
    "$temp"
}

pick_language() {
  print_header
  echo "Choose a language pack:"
  echo
  echo "  1) Hindi news   (channels 101–116)"
  echo "  2) English news (channels 201–220)"
  echo "  3) All news     (both groups)"
  echo "  q) Quit"
  echo
  read -r -p "Selection [1-3]: " choice
  case "$choice" in
    1) echo "hindi" ;;
    2) echo "english" ;;
    3) echo "all" ;;
    q|Q) exit 0 ;;
    *) echo "Invalid choice." >&2; pick_language ;;
  esac
}

interactive_loop() {
  local lang="$1"
  while true; do
    print_header
    echo "Language pack: ${lang}"
    echo
    print_channels "$lang"
    echo
    echo "Enter a channel number (e.g. 101 or 205), part of a name, or:"
    echo "  /hindi   /english   /all   — switch language pack"
    echo "  list     — show guide again"
    echo "  help     — VLC keyboard shortcuts"
    echo "  q        — quit"
    echo
    read -r -p "Channel › " input || exit 0
    input="$(echo "$input" | xargs)"
    [[ -z "$input" ]] && continue

    case "$input" in
      q|Q) exit 0 ;;
      list) continue ;;
      help|h)
        cat <<'HELP'

VLC shortcuts:
  Ctrl+L       Open playlist sidebar (channels grouped by language)
  PgUp / PgDn  Previous / next channel
  Up / Down    Step through playlist
  F            Fullscreen
  Space        Pause / play

HELP
        read -r -p "Press Enter to continue..."
        continue
        ;;
      /hindi) lang="hindi"; continue ;;
      /english) lang="english"; continue ;;
      /all) lang="all"; continue ;;
    esac

    local result
    if ! result="$(resolve_channel "$lang" "$input" 2>/dev/null)"; then
      echo
      echo "No channel matched '$input'. Try a number (101, 205) or name (aaj, bbc)."
      read -r -p "Press Enter to continue..."
      continue
    fi

    if echo "$result" | "$PYTHON" -c 'import json,sys; d=json.load(sys.stdin); sys.exit(0 if "ambiguous" not in d else 1)' 2>/dev/null; then
      launch_vlc "$lang" "$result"
    fi

    echo
    echo "Multiple matches:"
    echo "$result" | "$PYTHON" -c '
import json, sys
data = json.load(sys.stdin)
for ch in data["matches"]:
    print(f"  {ch[\"number\"]:03d}  {ch[\"label\"]} ({ch[\"language\"]})")
'
    read -r -p "Enter exact channel number: " exact || exit 0
    if result="$(resolve_channel "$lang" "$exact" 2>/dev/null)"; then
      launch_vlc "$lang" "$result"
    fi
  done
}

main() {
  ensure_catalog

  local lang=""
  local query=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --lang) shift; lang="${1:-}" ;;
      --channel|--search) shift; query="${1:-}" ;;
      --list)
        print_header
        print_channels all
        exit 0
        ;;
      --help|-h) usage; exit 0 ;;
      *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
    esac
    shift
  done

  if [[ -n "$query" ]]; then
    lang="${lang:-all}"
    local result
    result="$(resolve_channel "$lang" "$query")" || {
      echo "Channel not found: $query" >&2
      exit 1
    }
    launch_vlc "$lang" "$result"
  fi

  if [[ -z "$lang" ]]; then
    lang="$(pick_language)"
  fi

  interactive_loop "$lang"
}

main "$@"
