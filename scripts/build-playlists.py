#!/usr/bin/env python3
"""Build curated Hindi and English news M3U playlists from iptv-org sources."""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

IPTV_ORG_HIN = "https://iptv-org.github.io/iptv/languages/hin.m3u"
IPTV_ORG_ENG = "https://iptv-org.github.io/iptv/languages/eng.m3u"

HINDI_CHANNELS = [
    ("AajTak.in@HD", "Aaj Tak"),
    ("ABPNews.in@SD", "ABP News"),
    ("NDTVIndia.in@SD", "NDTV India"),
    ("DDNews.in@HD", "DD News"),
    ("ZeeNews.in@SD", "Zee News"),
    ("RepublicBharat.in@SD", "Republic Bharat"),
    ("TV9Bharatvarsh.in@SD", "TV9 Bharatvarsh"),
    ("News18India.in@SD", "News18 India"),
    ("NewsNation.in@SD", "News Nation"),
    ("IndiaTV.in@SD", "India TV"),
    ("TimesNowNavbharat.in@SD", "Times Now Navbharat"),
    ("BharatSamachar.in@SD", "Bharat Samachar"),
    ("GoodNewsToday.in@SD", "Good News Today"),
    ("SudarshanNews.in@SD", "Sudarshan News"),
    ("News24.in@SD", "News 24"),
    ("SansadTV1.in@HD", "Sansad TV"),
]

ENGLISH_CHANNELS = [
    ("AlJazeera.qa@English", "Al Jazeera English"),
    ("France24.fr@English", "France 24 English"),
    ("DW.de@English", "DW English"),
    ("BBCNews.uk@UK", "BBC News"),
    ("BBCNews.uk@Europe", "BBC News"),
    ("SkyNews.uk@SD", "Sky News"),
    ("SkyNews.ie@SD", "Sky News"),
    ("ReutersTV.us@SD", "Reuters"),
    ("NDTV24x7.in@SD", "NDTV 24x7"),
    ("ABCNews.au@Sydney", "ABC News Australia"),
    ("CBSNews247.us@SD", "CBS News 24/7"),
    ("FoxNewsChannel.us@SD", "Fox News"),
    ("EuronewsEnglish.fr@SD", "Euronews English"),
    ("CGTN.cn@SD", "CGTN"),
    ("TRTWorld.tr@SD", "TRT World"),
    ("WION.in@SD", "WION"),
    ("TimesNow.in@SD", "Times Now"),
    ("RepublicTV.in@SD", "Republic TV"),
    ("MirrorNow.in@SD", "Mirror Now"),
    ("BloombergTV.us@US", "Bloomberg TV"),
    ("CNBCUK.uk@SD", "CNBC"),
    ("NHKWorldJapan.jp@SD", "NHK World"),
]

HINDI_BASE = 101
ENGLISH_BASE = 201


def fetch_m3u(url: str) -> str:
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_m3u(content: str) -> list[dict]:
    entries = []
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.startswith("#EXTINF"):
            i += 1
            continue

        info = line
        extras = []
        i += 1
        while i < len(lines) and lines[i].startswith("#EXT"):
            extras.append(lines[i])
            i += 1

        url = lines[i] if i < len(lines) and not lines[i].startswith("#") else ""
        i += 1

        tvg_id_match = re.search(r'tvg-id="([^"]+)"', info)
        logo_match = re.search(r'tvg-logo="([^"]+)"', info)
        channel_name = info.rsplit(",", 1)[-1] if "," in info else ""
        entries.append(
            {
                "tvg_id": tvg_id_match.group(1) if tvg_id_match else "",
                "name": channel_name,
                "logo": logo_match.group(1) if logo_match else "",
                "info": info,
                "extras": extras,
                "url": url,
            }
        )
    return entries


def find_entry(entries: list[dict], tvg_id: str, label: str) -> dict | None:
    for entry in entries:
        if entry["tvg_id"] == tvg_id:
            return entry
    for entry in entries:
        if label.lower() in entry["name"].lower() and "News" in entry["info"]:
            return entry
    return None


def quality_suffix(name: str) -> str:
    match = re.search(r"\((\d+p|Not 24/7|Geo-blocked)[^)]*\)", name, re.I)
    return match.group(0) if match else ""


def build_extinf(entry: dict, *, number: int, label: str, group: str, language: str) -> str:
    suffix = quality_suffix(entry["name"])
    flags = ""
    if suffix:
        flags = f" {suffix}"
    display = f"{number:03d} · {label}{flags}"

    info = entry["info"]
    info = re.sub(r'tvg-chno="[^"]*"', "", info)
    info = re.sub(r'group-title="[^"]*"', f'group-title="{group}"', info)
    if 'tvg-language="' not in info:
        info = info.replace("#EXTINF:-1", f'#EXTINF:-1 tvg-language="{language}"', 1)
    else:
        info = re.sub(r'tvg-language="[^"]*"', f'tvg-language="{language}"', info)

    if 'tvg-chno="' not in info:
        info = info.replace("#EXTINF:-1", f'#EXTINF:-1 tvg-chno="{number}"', 1)
    else:
        info = re.sub(r'tvg-chno="[^"]*"', f'tvg-chno="{number}"', info)

    if 'tvg-name="' not in info:
        info = info.replace("#EXTINF:-1", f'#EXTINF:-1 tvg-name="{label}"', 1)

    info = re.sub(r",[^,]+$", f",{display}", info)
    return info


def collect_channels(
    channel_specs: list[tuple[str, str]],
    entries: list[dict],
    *,
    base_number: int,
    group: str,
    language: str,
) -> list[dict]:
    channels: list[dict] = []
    seen_urls: set[str] = set()
    number = base_number

    for tvg_id, label in channel_specs:
        entry = find_entry(entries, tvg_id, label)
        if not entry or not entry["url"]:
            print(f"  - missing: {label} ({tvg_id})", file=sys.stderr)
            continue
        if entry["url"] in seen_urls:
            continue
        seen_urls.add(entry["url"])

        extinf = build_extinf(entry, number=number, label=label, group=group, language=language)
        channels.append(
            {
                "number": number,
                "label": label,
                "group": group,
                "language": language,
                "display": extinf.rsplit(",", 1)[-1],
                "logo": entry["logo"],
                "url": entry["url"],
                "extinf": extinf,
                "extras": entry["extras"],
            }
        )
        print(f"  + {number:03d} {label}: {entry['name']}", file=sys.stderr)
        number += 1

    return channels


def render_playlist(title: str, channels: list[dict], *, grouped: bool = False) -> str:
    lines = [
        '#EXTM3U x-tvg-url="https://iptv-org.github.io/epg/guides.xml"',
        f"#PLAYLIST:{title}",
    ]
    current_group = None
    for channel in channels:
        if grouped and channel["group"] != current_group:
            current_group = channel["group"]
            lines.append(f"#EXTGRP:{current_group}")
        lines.append(channel["extinf"])
        lines.extend(channel["extras"])
        lines.append(channel["url"])
    return "\n".join(lines) + "\n"


def write_channel_map(path: Path, hindi: list[dict], english: list[dict]) -> None:
    lines = [
        "NEWS TV — Channel Guide",
        "=======================",
        "",
        "Hindi News (101–199)",
        "--------------------",
    ]
    for ch in hindi:
        lines.append(f"  {ch['number']:03d}  {ch['label']}")
    lines.extend(["", "English News (201–299)", "----------------------"])
    for ch in english:
        lines.append(f"  {ch['number']:03d}  {ch['label']}")
    lines.extend(
        [
            "",
            "VLC shortcuts",
            "-------------",
            "  Ctrl+L     Open playlist sidebar",
            "  PgUp/PgDn  Previous / next channel",
            "  Up/Down    Fine channel step",
            "  F          Fullscreen",
            "",
            "Launch: ./scripts/news-tv.sh",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    out_dir = root / "iptv"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Fetching Hindi channels...", file=sys.stderr)
    hin_entries = parse_m3u(fetch_m3u(IPTV_ORG_HIN))
    print("Fetching English channels...", file=sys.stderr)
    eng_entries = parse_m3u(fetch_m3u(IPTV_ORG_ENG))

    print("\nHindi news:", file=sys.stderr)
    hindi = collect_channels(
        HINDI_CHANNELS, hin_entries, base_number=HINDI_BASE, group="Hindi News", language="Hindi"
    )
    print("\nEnglish news:", file=sys.stderr)
    english = collect_channels(
        ENGLISH_CHANNELS, eng_entries, base_number=ENGLISH_BASE, group="English News", language="English"
    )

    (out_dir / "hindi-news.m3u").write_text(
        render_playlist("Hindi News Channels", hindi), encoding="utf-8"
    )
    (out_dir / "english-news.m3u").write_text(
        render_playlist("English News Channels", english), encoding="utf-8"
    )
    (out_dir / "all-news.m3u").write_text(
        render_playlist("All News Channels", hindi + english, grouped=True), encoding="utf-8"
    )

    catalog = {
        "hindi": [
            {k: ch[k] for k in ("number", "label", "group", "language", "display", "logo", "url")}
            for ch in hindi
        ],
        "english": [
            {k: ch[k] for k in ("number", "label", "group", "language", "display", "logo", "url")}
            for ch in english
        ],
    }
    (out_dir / "channels.json").write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    write_channel_map(out_dir / "channel-guide.txt", hindi, english)

    print(f"\nWrote playlists to {out_dir}", file=sys.stderr)


if __name__ == "__main__":
    main()
