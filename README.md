# IPTV News Channels for VLC

Curated **English** and **Hindi** news channel playlists for an IPTV-like live TV experience in [VLC Media Player](https://www.videolan.org/vlc/).

## Navigate channels

### Interactive navigator (recommended)

```bash
./scripts/news-tv.sh
```

This opens a menu where you can:

- Choose **Hindi**, **English**, or **All** news packs
- Tune by **channel number** (`101`, `205`) or **name** (`aaj`, `bbc`)
- Launch VLC with the full playlist and your pick loaded first

Quick jumps:

```bash
./scripts/news-tv.sh --lang hindi --channel 101   # Aaj Tak
./scripts/news-tv.sh --search bbc                 # BBC News
./scripts/news-tv.sh --list                       # Print channel guide
```

### Channel numbers

| Range | Language |
|-------|----------|
| 101–199 | Hindi news |
| 201–299 | English news |

See [`iptv/channel-guide.txt`](iptv/channel-guide.txt) or the [web channel guide](guide.html).

### VLC controls while watching

| Key | Action |
|-----|--------|
| `Ctrl+L` | Open playlist sidebar (grouped by language) |
| `PgUp` / `PgDn` | Previous / next channel |
| `Up` / `Down` | Step through playlist |
| `F` | Fullscreen |

## Playlists

| Playlist | File | Description |
|----------|------|-------------|
| English News | [`iptv/english-news.m3u`](iptv/english-news.m3u) | International & Indian English news |
| Hindi News | [`iptv/hindi-news.m3u`](iptv/hindi-news.m3u) | Major Hindi news channels |
| All News | [`iptv/all-news.m3u`](iptv/all-news.m3u) | Combined, grouped with `#EXTGRP` |

## Quick start (manual)

1. Install VLC from [videolan.org](https://www.videolan.org/vlc/)
2. Run `./scripts/news-tv.sh` or open a playlist via **Media → Open File**
3. Press `Ctrl+L` to browse grouped channels

`./scripts/watch-news.sh` is an alias for the interactive navigator.

## Included channels

### English news

- Al Jazeera English, BBC News, France 24 English, DW English
- Sky News, Reuters, Euronews, CGTN, TRT World, NHK World
- NDTV 24x7, WION, Times Now, Republic TV, Mirror Now
- ABC News Australia, CBS News 24/7, Fox News, Bloomberg TV, CNBC

### Hindi news

- Aaj Tak, ABP News, NDTV India, DD News, Zee News
- Republic Bharat, TV9 Bharatvarsh, News18 India, News Nation
- India TV, Times Now Navbharat, Bharat Samachar, Good News Today
- Sudarshan News, News 24, Sansad TV

## Refresh playlists

```bash
python3 scripts/build-playlists.py
```

Regenerates M3U playlists, `channels.json`, and `channel-guide.txt`.

## Notes

- These are **free-to-air public streams** — availability varies by region and may change over time.
- Some channels may be geo-blocked or marked `[Not 24/7]`.
- The combined playlist uses VLC `#EXTGRP` tags so Hindi and English appear as separate groups in the playlist tree.
