#!/usr/bin/env python3
"""Parse IPTV playlists into a channel catalog for navigation tools."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IPTV_DIR = ROOT / "iptv"
CATALOG = IPTV_DIR / "channels.json"


def load_catalog() -> dict:
    if CATALOG.exists():
        return json.loads(CATALOG.read_text(encoding="utf-8"))

    channels: dict[str, list[dict]] = {"hindi": [], "english": []}
    for lang, playlist in (("hindi", "hindi-news.m3u"), ("english", "english-news.m3u")):
        path = IPTV_DIR / playlist
        if not path.exists():
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            if not line.startswith("#EXTINF"):
                i += 1
                continue
            display = line.rsplit(",", 1)[-1]
            number_match = re.search(r"^(\d{3})", display)
            label_match = re.search(r"·\s*(.+?)(?:\s*\(|$)", display)
            logo_match = re.search(r'tvg-logo="([^"]+)"', line)
            group_match = re.search(r'group-title="([^"]+)"', line)
            i += 1
            while i < len(lines) and lines[i].startswith("#"):
                i += 1
            url = lines[i] if i < len(lines) else ""
            i += 1
            channels[lang].append(
                {
                    "number": int(number_match.group(1)) if number_match else 0,
                    "label": label_match.group(1).strip() if label_match else display,
                    "display": display,
                    "logo": logo_match.group(1) if logo_match else "",
                    "group": group_match.group(1) if group_match else lang.title(),
                    "language": "Hindi" if lang == "hindi" else "English",
                    "url": url,
                }
            )
    return channels


def all_channels(catalog: dict, language: str = "all") -> list[dict]:
    if language == "hindi":
        return catalog.get("hindi", [])
    if language == "english":
        return catalog.get("english", [])
    return catalog.get("hindi", []) + catalog.get("english", [])


def find_channel(catalog: dict, query: str, language: str = "all") -> dict | None:
    query = query.strip()
    if not query:
        return None

    pool = all_channels(catalog, language)
    if query.isdigit():
        number = int(query)
        for channel in pool:
            if channel["number"] == number:
                return channel
        return None

    lowered = query.lower()
    matches = [ch for ch in pool if lowered in ch["label"].lower()]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        return matches[0]
    return None


def playlist_path(language: str) -> Path:
    mapping = {
        "hindi": IPTV_DIR / "hindi-news.m3u",
        "english": IPTV_DIR / "english-news.m3u",
        "all": IPTV_DIR / "all-news.m3u",
    }
    return mapping[language]


def write_start_playlist(selected: dict, language: str) -> Path:
    """Write a temp playlist with the selected channel first for easy zapping."""
    source = playlist_path(language)
    lines = source.read_text(encoding="utf-8").splitlines()
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.startswith("#EXTINF"):
            if current:
                blocks.append(current)
            current = [line]
        elif current:
            current.append(line)
    if current:
        blocks.append(current)

    selected_block = None
    other_blocks: list[list[str]] = []
    for block in blocks:
        if block and block[0].startswith("#EXTINF") and selected["url"] in block:
            selected_block = block
        else:
            other_blocks.append(block)

    if not selected_block:
        selected_block = [selected["extinf"]] if "extinf" in selected else []
        if selected.get("url"):
            selected_block.append(selected["url"])

    header = [line for line in lines[:2] if line.startswith("#")]
    output_lines = header[:]
    if language == "all":
        output_lines.append(f"#EXTGRP:{selected['group']}")
    output_lines.extend(selected_block)
    for block in other_blocks:
        output_lines.extend(block)

    temp = IPTV_DIR / ".start-channel.m3u"
    temp.write_text("\n".join(output_lines) + "\n", encoding="utf-8")
    return temp


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps(load_catalog(), indent=2))
    elif sys.argv[1] == "find":
        catalog = load_catalog()
        channel = find_channel(catalog, sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "all")
        print(json.dumps(channel or {}, indent=2))
    else:
        print("Usage: channel-data.py [find <query> [language]]", file=sys.stderr)
        sys.exit(1)
