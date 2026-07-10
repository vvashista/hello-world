# IPTV News Channels for VLC

Curated **English** and **Hindi** news channel playlists for an IPTV-like live TV experience in [VLC Media Player](https://www.videolan.org/vlc/).

## Playlists

| Playlist | File | Description |
|----------|------|-------------|
| English News | [`iptv/english-news.m3u`](iptv/english-news.m3u) | International & Indian English news |
| Hindi News | [`iptv/hindi-news.m3u`](iptv/hindi-news.m3u) | Major Hindi news channels |
| All News | [`iptv/all-news.m3u`](iptv/all-news.m3u) | Combined English + Hindi |

## Quick start

### Option 1: VLC GUI

1. Install VLC from [videolan.org](https://www.videolan.org/vlc/)
2. **Media → Open File** and select a playlist (e.g. `iptv/hindi-news.m3u`)
3. **View → Playlist** (`Ctrl+L` / `Cmd+L`) to browse channels
4. Use **Up/Down** or **PgUp/PgDn** to switch channels

### Option 2: Command line

```bash
./scripts/watch-news.sh              # English news (default)
./scripts/watch-news.sh hindi        # Hindi news
./scripts/watch-news.sh all          # All news channels
./scripts/watch-news.sh hindi --channel 3
./scripts/watch-news.sh --list       # List all channels
```

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

Streams are pulled from the community-maintained [iptv-org/iptv](https://github.com/iptv-org/iptv) project. To update local playlists:

```bash
python3 scripts/build-playlists.py
```

## Notes

- These are **free-to-air public streams** — availability varies by region and may change over time.
- Some channels may be geo-blocked or marked `[Not 24/7]`.
- VLC groups channels under **English News** and **Hindi News** in the playlist sidebar.
