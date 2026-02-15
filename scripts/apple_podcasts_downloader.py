#!/usr/bin/env python3
"""
Apple Podcasts Downloader
Downloads sermon audio and metadata from Gospel in Life podcast RSS feed.
"""

import sys
import requests
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    import feedparser
except ImportError:
    print("❌ Error: feedparser not installed")
    print("Run: pip3 install feedparser")
    sys.exit(1)


class PodcastDownloader:
    """Downloads podcast episodes from RSS feed"""

    # Gospel in Life podcast RSS feed
    RSS_FEED_URL = "https://feeds.gospelinlife.com/gospelinlife-podcast"

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.downloads_dir = base_dir / "downloads"
        self.downloads_dir.mkdir(exist_ok=True)

    def fetch_feed(self) -> Optional[feedparser.FeedParserDict]:
        """Fetch and parse the RSS feed"""
        print(f"📡 Fetching podcast feed...")
        print(f"   URL: {self.RSS_FEED_URL}")

        try:
            feed = feedparser.parse(self.RSS_FEED_URL)

            if feed.bozo:
                print(f"⚠️  Warning: Feed parsing issues")

            if not feed.entries:
                print(f"❌ No episodes found in feed")
                return None

            print(f"✅ Found {len(feed.entries)} episodes")
            return feed

        except Exception as e:
            print(f"❌ Error fetching feed: {e}")
            return None

    def list_episodes(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List episodes from the feed"""
        feed = self.fetch_feed()
        if not feed:
            return []

        episodes = []
        for i, entry in enumerate(feed.entries[:limit]):
            episode = self._parse_entry(entry, i)
            episodes.append(episode)

        return episodes

    def _parse_entry(self, entry: Any, index: int) -> Dict[str, Any]:
        """Parse a feed entry into episode metadata"""
        # Extract audio URL
        audio_url = None
        audio_type = None

        if hasattr(entry, 'enclosures') and entry.enclosures:
            audio_url = entry.enclosures[0].get('href')
            audio_type = entry.enclosures[0].get('type')
        elif hasattr(entry, 'links'):
            for link in entry.links:
                if 'audio' in link.get('type', ''):
                    audio_url = link.get('href')
                    audio_type = link.get('type')
                    break

        # Parse published date
        pub_date = None
        if hasattr(entry, 'published_parsed'):
            try:
                pub_date = datetime(*entry.published_parsed[:6]).strftime('%Y-%m-%d')
            except:
                pub_date = entry.get('published', 'Unknown date')
        elif hasattr(entry, 'published'):
            pub_date = entry.published

        # Extract description (clean HTML if present)
        description = entry.get('summary', '')
        if hasattr(entry, 'summary_detail'):
            description = entry.summary_detail.get('value', description)

        return {
            "index": index,
            "title": entry.get('title', 'Untitled'),
            "pub_date": pub_date,
            "audio_url": audio_url,
            "audio_type": audio_type,
            "description": description,
            "link": entry.get('link', '')
        }

    def download_episode(self, episode_id: int, output_dir: Optional[Path] = None) -> Optional[Path]:
        """
        Download an episode by index.
        Returns path to downloaded file.
        """
        episodes = self.list_episodes(limit=100)

        if episode_id < 0 or episode_id >= len(episodes):
            print(f"❌ Invalid episode ID: {episode_id}")
            print(f"   Valid range: 0-{len(episodes)-1}")
            return None

        episode = episodes[episode_id]

        if not episode['audio_url']:
            print(f"❌ No audio URL found for episode: {episode['title']}")
            return None

        # Determine output directory
        if output_dir is None:
            output_dir = self.downloads_dir

        output_dir.mkdir(parents=True, exist_ok=True)

        # Sanitize filename
        filename = self._sanitize_filename(episode['title'])
        audio_file = output_dir / f"{filename}.mp3"

        print(f"\n📥 Downloading: {episode['title']}")
        print(f"   Date: {episode['pub_date']}")
        print(f"   URL: {episode['audio_url']}")
        print(f"   Output: {audio_file}")

        try:
            # Download with progress
            response = requests.get(episode['audio_url'], stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(audio_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        # Progress indicator
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\r   Progress: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='')

            print(f"\n✅ Download complete: {audio_file}")
            print(f"   Size: {audio_file.stat().st_size:,} bytes")

            return audio_file

        except Exception as e:
            print(f"\n❌ Download failed: {e}")
            if audio_file.exists():
                audio_file.unlink()
            return None

    def download_latest(self, count: int = 5) -> List[Path]:
        """Download the latest N episodes"""
        episodes = self.list_episodes(limit=count)

        print(f"\n📥 Downloading {count} latest episodes...")

        downloaded = []
        for episode in episodes:
            result = self.download_episode(episode['index'])
            if result:
                downloaded.append(result)

        print(f"\n✅ Downloaded {len(downloaded)}/{count} episodes")
        return downloaded

    @staticmethod
    def _sanitize_filename(title: str) -> str:
        """Sanitize title for use as filename"""
        # Remove/replace problematic characters
        safe = title.replace('/', '_')
        safe = safe.replace('\\', '_')
        safe = safe.replace(':', '_')
        safe = safe.replace('*', '_')
        safe = safe.replace('?', '_')
        safe = safe.replace('"', '_')
        safe = safe.replace('<', '_')
        safe = safe.replace('>', '_')
        safe = safe.replace('|', '_')
        safe = safe.replace("'", "")

        # Limit length
        if len(safe) > 200:
            safe = safe[:200]

        return safe.strip()


def main():
    parser = argparse.ArgumentParser(
        description="Download Gospel in Life podcast episodes"
    )
    parser.add_argument(
        "--search",
        help="Search for podcasts (currently only supports Gospel in Life)"
    )
    parser.add_argument(
        "--list-episodes",
        action="store_true",
        help="List available episodes"
    )
    parser.add_argument(
        "--download",
        type=int,
        metavar="EPISODE_ID",
        help="Download episode by ID (use --list-episodes to see IDs)"
    )
    parser.add_argument(
        "--download-latest",
        type=int,
        metavar="COUNT",
        help="Download the latest N episodes"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output directory for downloads (default: downloads/)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Limit number of episodes to list (default: 20)"
    )

    args = parser.parse_args()

    # Determine base directory
    base_dir = Path(__file__).parent.parent

    downloader = PodcastDownloader(base_dir)

    # Handle commands
    if args.search:
        print(f"🔍 Searching for: {args.search}")
        print(f"   Currently only Gospel in Life podcast is supported")
        print(f"   RSS: {PodcastDownloader.RSS_FEED_URL}")

    elif args.list_episodes:
        episodes = downloader.list_episodes(limit=args.limit)

        if episodes:
            print(f"\n📻 Gospel in Life Podcast Episodes:\n")
            for ep in episodes:
                print(f"ID: {ep['index']:3d} | {ep['pub_date']:12s} | {ep['title']}")
                if ep['audio_url']:
                    print(f"           Audio: ✅")
                else:
                    print(f"           Audio: ❌ (no URL)")
                print()

    elif args.download is not None:
        output_dir = args.output if args.output else None
        downloader.download_episode(args.download, output_dir)

    elif args.download_latest:
        downloader.download_latest(args.download_latest)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
