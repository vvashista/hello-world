#!/usr/bin/env python3
"""Build curated Hindi and English news M3U playlists from iptv-org sources."""

import re
import sys
import urllib.request
from pathlib import Path

IPTV_ORG_HIN = "https://iptv-org.github.io/iptv/languages/hin.m3u"
IPTV_ORG_ENG = "https://iptv-org.github.io/iptv/languages/eng.m3u"

# Curated channels by tvg-id (preferred) with display name fallback patterns.
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
        channel_name = info.rsplit(",", 1)[-1] if "," in info else ""
        entries.append(
            {
                "tvg_id": tvg_id_match.group(1) if tvg_id_match else "",
                "name": channel_name,
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


def build_playlist(title: str, group: str, channel_specs: list[tuple[str, str]], entries: list[dict]) -> str:
    lines = [
        '#EXTM3U x-tvg-url="https://iptv-org.github.io/epg/guides.xml"',
        f"#PLAYLIST:{title}",
    ]
    seen_urls: set[str] = set()

    for tvg_id, label in channel_specs:
        entry = find_entry(entries, tvg_id, label)
        if not entry or not entry["url"]:
            print(f"  - missing: {label} ({tvg_id})", file=sys.stderr)
            continue
        if entry["url"] in seen_urls:
            continue
        seen_urls.add(entry["url"])

        info = re.sub(r'group-title="[^"]*"', f'group-title="{group}"', entry["info"])
        lines.append(info)
        lines.extend(entry["extras"])
        lines.append(entry["url"])
        print(f"  + {label}: {entry['name']}", file=sys.stderr)

    return "\n".join(lines) + "\n"


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    out_dir = root / "iptv"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Fetching Hindi channels...", file=sys.stderr)
    hin_entries = parse_m3u(fetch_m3u(IPTV_ORG_HIN))
    print("Fetching English channels...", file=sys.stderr)

    eng_entries = parse_m3u(fetch_m3u(IPTV_ORG_ENG))

    print("\nHindi news:", file=sys.stderr)
    hindi = build_playlist("Hindi News Channels", "Hindi News", HINDI_CHANNELS, hin_entries)

    print("\nEnglish news:", file=sys.stderr)
    english = build_playlist("English News Channels", "English News", ENGLISH_CHANNELS, eng_entries)

    (out_dir / "hindi-news.m3u").write_text(hindi, encoding="utf-8")
    (out_dir / "english-news.m3u").write_text(english, encoding="utf-8")

    combined_lines = hindi.splitlines()[:2]
    for block in (hindi, english):
        for line in block.splitlines():
            if line.startswith("#EXTINF") or line.startswith("#EXTVLCOPT") or (
                line.startswith("http") and line.strip()
            ):
                if line not in combined_lines:
                    combined_lines.append(line)

    (out_dir / "all-news.m3u").write_text("\n".join(combined_lines) + "\n", encoding="utf-8")
    print(f"\nWrote playlists to {out_dir}", file=sys.stderr)


if __name__ == "__main__":
    main()
