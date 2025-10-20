#!/usr/bin/env python3
"""
YouTube Transcript Processor using yt-dlp

Downloads and processes YouTube transcripts using yt-dlp.
Features:
- Automatic detection of already-processed videos
- Idempotent operation (safe to run multiple times)
- Converts subtitles to clean markdown
- Maintains processing log
- Robust error handling
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from vtt_to_markdown import convert_subtitle_to_markdown


class YouTubeTranscriptProcessor:
    """Process YouTube transcripts using yt-dlp."""

    def __init__(self, base_dir: Path = None, verbose: bool = False):
        """
        Initialize the processor.

        Args:
            base_dir: Base directory for the project (defaults to repo root)
            verbose: Enable verbose output
        """
        self.verbose = verbose
        self.base_dir = base_dir or Path(__file__).parent.parent
        self.sources_file = self.base_dir / 'knowledge_base' / 'sources' / 'youtube_talks.md'
        self.transcripts_dir = self.base_dir / 'knowledge_base' / 'transcripts' / 'raw'
        self.log_file = self.base_dir / 'knowledge_base' / 'transcripts' / 'processing_log.json'
        self.temp_dir = self.base_dir / 'temp_downloads'

        # Create directories if they don't exist
        self.transcripts_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def log(self, message: str, force: bool = False):
        """Log a message if verbose mode is enabled."""
        if self.verbose or force:
            print(message)

    def check_ytdlp_installed(self) -> bool:
        """Check if yt-dlp is installed."""
        try:
            result = subprocess.run(
                ['yt-dlp', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def extract_video_id(self, url: str) -> Optional[str]:
        """
        Extract video ID from YouTube URL.

        Args:
            url: YouTube URL

        Returns:
            Video ID or None if not found
        """
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    def read_video_urls(self) -> List[Tuple[str, str]]:
        """
        Read video URLs from the sources file.

        Returns:
            List of (video_id, url) tuples
        """
        if not self.sources_file.exists():
            self.log(f"Error: Sources file not found: {self.sources_file}", force=True)
            return []

        videos = []
        content = self.sources_file.read_text(encoding='utf-8')

        for line_num, line in enumerate(content.split('\n'), 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Extract URL (everything before any dash or comment)
            url = line.split()[0] if line else ''

            video_id = self.extract_video_id(url)
            if video_id:
                videos.append((video_id, url))
                self.log(f"Found video: {video_id}")
            elif url:
                self.log(f"Warning: Could not extract video ID from line {line_num}: {line}")

        self.log(f"Found {len(videos)} videos in {self.sources_file.name}", force=True)
        return videos

    def is_already_processed(self, video_id: str) -> bool:
        """
        Check if a video has already been processed.

        Args:
            video_id: YouTube video ID

        Returns:
            True if already processed
        """
        # Check for any markdown file starting with the video ID
        pattern = f"{video_id}*.md"
        existing_files = list(self.transcripts_dir.glob(pattern))

        return len(existing_files) > 0

    def get_video_metadata(self, video_id: str) -> Optional[Dict]:
        """
        Get video metadata using yt-dlp.

        Args:
            video_id: YouTube video ID

        Returns:
            Metadata dict or None if failed
        """
        try:
            self.log(f"Fetching metadata for {video_id}...")
            cmd = [
                'yt-dlp',
                '--dump-json',
                '--skip-download',
                '--no-warnings',
                '--no-check-certificate',  # Handle SSL issues in some environments
                f'https://www.youtube.com/watch?v={video_id}'
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.temp_dir
            )

            if result.returncode == 0 and result.stdout:
                metadata = json.loads(result.stdout)
                self.log(f"Got metadata: {metadata.get('title', 'Unknown')}")
                return metadata

            self.log(f"Failed to get metadata: {result.stderr}")
            return None

        except Exception as e:
            self.log(f"Error getting metadata: {e}")
            return None

    def download_subtitles(self, video_id: str) -> Optional[Path]:
        """
        Download subtitles for a video using yt-dlp.

        Args:
            video_id: YouTube video ID

        Returns:
            Path to downloaded subtitle file or None if failed
        """
        try:
            self.log(f"Downloading subtitles for {video_id}...")

            # Clean up any existing subtitle files for this video
            for old_file in self.temp_dir.glob(f"{video_id}.*"):
                if old_file.suffix in ['.vtt', '.srt', '.en.vtt', '.en.srt']:
                    old_file.unlink()

            cmd = [
                'yt-dlp',
                '--write-auto-sub',      # Get auto-generated if no manual subs
                '--write-sub',           # Prefer manual subtitles
                '--sub-lang', 'en',
                '--skip-download',       # Don't download video
                '--sub-format', 'vtt/srt/best',
                '--output', f'{video_id}.%(ext)s',
                '--no-warnings',
                '--no-check-certificate',  # Handle SSL issues in some environments
                f'https://www.youtube.com/watch?v={video_id}'
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.temp_dir
            )

            if result.returncode != 0:
                self.log(f"yt-dlp error: {result.stderr}")
                return None

            # Find the downloaded subtitle file
            subtitle_files = list(self.temp_dir.glob(f"{video_id}*.vtt")) + \
                           list(self.temp_dir.glob(f"{video_id}*.srt"))

            if subtitle_files:
                self.log(f"Downloaded subtitle: {subtitle_files[0].name}")
                return subtitle_files[0]

            self.log("No subtitles found for this video")
            return None

        except subprocess.TimeoutExpired:
            self.log("Timeout while downloading subtitles")
            return None
        except Exception as e:
            self.log(f"Error downloading subtitles: {e}")
            return None

    def format_duration(self, seconds: int) -> str:
        """Format duration in seconds to HH:MM:SS."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def create_markdown_document(self, video_id: str, metadata: Dict, transcript: str) -> str:
        """
        Create a formatted markdown document.

        Args:
            video_id: YouTube video ID
            metadata: Video metadata
            transcript: Formatted transcript text

        Returns:
            Complete markdown document
        """
        title = metadata.get('title', 'Unknown Title')
        channel = metadata.get('channel', metadata.get('uploader', 'Unknown Channel'))
        upload_date = metadata.get('upload_date', '')
        if upload_date:
            # Convert YYYYMMDD to YYYY-MM-DD
            upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"

        duration = metadata.get('duration', 0)
        duration_str = self.format_duration(duration)
        description = metadata.get('description', 'No description available')

        # Extract tags from description or metadata
        tags = metadata.get('tags', [])
        tags_str = ' '.join([f'#{tag.replace(" ", "")}' for tag in tags[:10]])

        now = datetime.now().isoformat()

        doc = f"""# {title}

**Video ID:** {video_id}
**URL:** https://www.youtube.com/watch?v={video_id}
**Channel:** {channel}
**Published:** {upload_date}
**Duration:** {duration_str}
**Downloaded:** {now}
{f'**Tags:** {tags_str}' if tags_str else ''}

## Description

{description[:500]}{'...' if len(description) > 500 else ''}

---

## Transcript

{transcript}

---

## Metadata
<!--
Video metadata for reference:
{json.dumps(metadata, indent=2)}
-->
"""
        return doc

    def sanitize_filename(self, title: str, max_length: int = 100) -> str:
        """
        Sanitize a title for use as a filename.

        Args:
            title: Video title
            max_length: Maximum filename length

        Returns:
            Sanitized filename
        """
        # Remove invalid filename characters
        title = re.sub(r'[<>:"/\\|?*]', '', title)
        # Replace spaces with underscores
        title = title.replace(' ', '_')
        # Remove multiple underscores
        title = re.sub(r'_+', '_', title)
        # Truncate if too long
        if len(title) > max_length:
            title = title[:max_length]
        # Remove trailing underscores
        title = title.rstrip('_')

        return title

    def process_video(self, video_id: str, url: str) -> bool:
        """
        Process a single video.

        Args:
            video_id: YouTube video ID
            url: Video URL

        Returns:
            True if successful
        """
        self.log(f"\n{'='*60}", force=True)
        self.log(f"Processing: {video_id}", force=True)
        self.log(f"{'='*60}", force=True)

        try:
            # Get metadata first
            metadata = self.get_video_metadata(video_id)
            if not metadata:
                self.log("Failed to get video metadata", force=True)
                return False

            # Download subtitles
            subtitle_file = self.download_subtitles(video_id)
            if not subtitle_file:
                self.log("No subtitles available for this video", force=True)
                return False

            # Convert to markdown
            self.log("Converting subtitles to markdown...")
            try:
                transcript = convert_subtitle_to_markdown(subtitle_file)
            except Exception as e:
                self.log(f"Error converting subtitle: {e}", force=True)
                return False

            # Create full markdown document
            markdown_doc = self.create_markdown_document(video_id, metadata, transcript)

            # Save to file
            title = metadata.get('title', 'Unknown')
            safe_title = self.sanitize_filename(title)
            output_file = self.transcripts_dir / f"{video_id}_{safe_title}.md"

            output_file.write_text(markdown_doc, encoding='utf-8')
            self.log(f"✓ Saved to: {output_file.name}", force=True)

            # Clean up temp file
            if subtitle_file.exists():
                subtitle_file.unlink()

            return True

        except Exception as e:
            self.log(f"Error processing video: {e}", force=True)
            return False

    def load_processing_log(self) -> Dict:
        """Load the processing log."""
        if self.log_file.exists():
            try:
                return json.loads(self.log_file.read_text())
            except Exception:
                pass

        return {
            'processed': {},
            'failed': {},
            'last_run': None
        }

    def save_processing_log(self, log_data: Dict):
        """Save the processing log."""
        log_data['last_run'] = datetime.now().isoformat()
        self.log_file.write_text(json.dumps(log_data, indent=2))

    def process_all(self, force_redownload: bool = False) -> Dict:
        """
        Process all videos from the sources file.

        Args:
            force_redownload: Force redownload even if already processed

        Returns:
            Processing statistics
        """
        # Read video URLs
        videos = self.read_video_urls()
        if not videos:
            self.log("No videos found to process", force=True)
            return {'total': 0, 'processed': 0, 'skipped': 0, 'failed': 0}

        # Load processing log
        log_data = self.load_processing_log()

        stats = {
            'total': len(videos),
            'processed': 0,
            'skipped': 0,
            'failed': 0
        }

        for video_id, url in videos:
            # Check if already processed
            if not force_redownload and self.is_already_processed(video_id):
                self.log(f"✓ Skipping {video_id} (already processed)", force=True)
                stats['skipped'] += 1
                continue

            # Process the video
            success = self.process_video(video_id, url)

            if success:
                stats['processed'] += 1
                log_data['processed'][video_id] = {
                    'url': url,
                    'processed_at': datetime.now().isoformat()
                }
                # Remove from failed if it was there
                log_data['failed'].pop(video_id, None)
            else:
                stats['failed'] += 1
                log_data['failed'][video_id] = {
                    'url': url,
                    'attempted_at': datetime.now().isoformat()
                }

            # Save log after each video
            self.save_processing_log(log_data)

        return stats

    def show_status(self):
        """Show processing status without downloading."""
        videos = self.read_video_urls()
        log_data = self.load_processing_log()

        print("\n" + "="*60)
        print("YouTube Transcript Processing Status")
        print("="*60 + "\n")

        print(f"Total videos in list: {len(videos)}\n")

        processed_count = 0
        pending_count = 0

        for video_id, url in videos:
            if self.is_already_processed(video_id):
                status = "✓ PROCESSED"
                processed_count += 1
            else:
                status = "⧗ PENDING"
                pending_count += 1

            print(f"{status}: {video_id}")

        print(f"\nSummary:")
        print(f"  Processed: {processed_count}")
        print(f"  Pending:   {pending_count}")

        if log_data.get('failed'):
            print(f"  Failed:    {len(log_data['failed'])}")

        if log_data.get('last_run'):
            print(f"\nLast run: {log_data['last_run']}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Download and process YouTube transcripts using yt-dlp',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all unprocessed videos
  python ytdlp_processor.py

  # Check status without downloading
  python ytdlp_processor.py --status

  # Process a specific video
  python ytdlp_processor.py --video xaUknipwnpw

  # Force reprocess all videos
  python ytdlp_processor.py --force

  # Verbose output
  python ytdlp_processor.py --verbose
        """
    )

    parser.add_argument(
        '--status',
        action='store_true',
        help='Show processing status without downloading'
    )

    parser.add_argument(
        '--video',
        type=str,
        help='Process a specific video by ID'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='Force redownload even if already processed'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    # Initialize processor
    processor = YouTubeTranscriptProcessor(verbose=args.verbose)

    # Check if yt-dlp is installed
    if not processor.check_ytdlp_installed():
        print("\nError: yt-dlp is not installed!")
        print("\nTo install yt-dlp:")
        print("  pip install yt-dlp")
        print("\nOr with your package manager:")
        print("  brew install yt-dlp  # macOS")
        print("  apt install yt-dlp   # Ubuntu/Debian")
        sys.exit(1)

    # Show status only
    if args.status:
        processor.show_status()
        return

    # Process specific video
    if args.video:
        video_id = args.video
        url = f"https://www.youtube.com/watch?v={video_id}"
        success = processor.process_video(video_id, url)
        sys.exit(0 if success else 1)

    # Process all videos
    print("\nStarting YouTube transcript processing...")
    print(f"Source file: {processor.sources_file}")
    print(f"Output directory: {processor.transcripts_dir}\n")

    stats = processor.process_all(force_redownload=args.force)

    # Print summary
    print("\n" + "="*60)
    print("Processing Complete!")
    print("="*60)
    print(f"Total videos:    {stats['total']}")
    print(f"Processed:       {stats['processed']}")
    print(f"Already done:    {stats['skipped']}")
    print(f"Failed:          {stats['failed']}")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
