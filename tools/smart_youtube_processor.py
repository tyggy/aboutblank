#!/usr/bin/env python3
"""
Fixed Smart YouTube Transcript Processor
With correct youtube-transcript-api usage
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Correct import
from youtube_transcript_api import YouTubeTranscriptApi

class SmartYouTubeProcessor:
    def __init__(self, 
                 youtube_list: str = "knowledge_base/sources/youtube_talks.md",
                 transcripts_dir: str = "knowledge_base/transcripts/raw"):
        self.youtube_list = Path(youtube_list)
        self.transcripts_dir = Path(transcripts_dir)
        self.transcripts_dir.mkdir(parents=True, exist_ok=True)
        
        # Processing log for tracking
        self.log_file = self.transcripts_dir.parent / "processing_log.json"
        self.processing_log = self._load_processing_log()
        
    def _load_processing_log(self) -> Dict:
        """Load or create processing log"""
        if self.log_file.exists():
            with open(self.log_file, 'r') as f:
                return json.load(f)
        return {
            "processed": {},
            "failed": {},
            "last_run": None
        }
    
    def _save_processing_log(self):
        """Save processing log"""
        self.processing_log["last_run"] = datetime.now().isoformat()
        with open(self.log_file, 'w') as f:
            json.dump(self.processing_log, f, indent=2)
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL"""
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',
        ]
        
        # Clean URL of any timestamp parameters for ID extraction
        url = url.split('&')[0] if '&' in url else url
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def parse_youtube_list(self) -> List[Dict]:
        """Parse the chronological YouTube list with automatic status detection"""
        if not self.youtube_list.exists():
            print(f"Creating new YouTube list at {self.youtube_list}")
            self.youtube_list.parent.mkdir(parents=True, exist_ok=True)
            with open(self.youtube_list, 'w') as f:
                f.write("# YouTube Talks - Buddhism & AI Knowledge Base\n\n")
                f.write("<!-- Add YouTube URLs below, one per line with optional description -->\n")
                f.write("<!-- Format: URL - Description #tags -->\n\n")
            return []
        
        entries = []
        with open(self.youtube_list, 'r') as f:
            lines = f.readlines()
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#') or line.startswith('<!--'):
                continue
            
            # Extract URL and metadata
            url_match = re.search(r'(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)[^\s]+)', line)
            
            if url_match:
                url = url_match.group(1)
                video_id = self.extract_video_id(url)
                
                if video_id:
                    # Extract description if present
                    description = ""
                    tags = []
                    
                    # Check for description after URL
                    remaining = line[url_match.end():].strip()
                    if remaining.startswith('-'):
                        remaining = remaining[1:].strip()
                        
                        # Extract tags
                        tag_matches = re.findall(r'#(\w+)', remaining)
                        tags = tag_matches
                        
                        # Remove tags from description
                        description = re.sub(r'#\w+', '', remaining).strip()
                    
                    # Check if already processed
                    is_processed = self._check_if_processed(video_id)
                    
                    entries.append({
                        'line_num': line_num,
                        'url': url.split('&')[0],  # Clean URL without timestamp for API
                        'full_url': url,  # Keep full URL with timestamp for reference
                        'video_id': video_id,
                        'description': description,
                        'tags': tags,
                        'is_processed': is_processed,
                        'original_line': line
                    })
        
        return entries
    
    def _check_if_processed(self, video_id: str) -> bool:
        """Check if a video has already been processed"""
        # Check for any file starting with the video ID
        for file in self.transcripts_dir.glob(f"{video_id}*.md"):
            return True
        
        # Also check processing log
        return video_id in self.processing_log.get("processed", {})
    
    def download_transcript(self, entry: Dict) -> Optional[Dict]:
        """Download transcript for a single video using correct API"""
        video_id = entry['video_id']
        url = entry['full_url']
        
        try:
            print(f"  ⬇️  Downloading: {video_id}")
            
            # Get available transcripts using the correct API method
            try:
                # First try to get transcript directly (faster)
                transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
                is_generated = False  # We don't know for sure, but likely manual if 'en' works
                
            except Exception as e:
                # If that fails, try with auto-generated
                try:
                    # Try getting list of available transcripts
                    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                    
                    # Try to find English transcript
                    transcript = None
                    for available_transcript in transcript_list:
                        if available_transcript.language_code == 'en':
                            transcript = available_transcript
                            break
                    
                    if not transcript:
                        # Try auto-generated
                        transcript = transcript_list.find_generated_transcript(['en'])
                    
                    transcript_data = transcript.fetch()
                    is_generated = transcript.is_generated if hasattr(transcript, 'is_generated') else True
                    
                except Exception as inner_e:
                    # Last resort - try any language
                    transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
                    is_generated = True
            
            # Get basic metadata (we can't use pytube as it might fail)
            metadata = {
                'title': f"Video {video_id}",  # Will be updated if we can get it
                'author': 'Unknown',
                'url': url,
                'video_id': video_id,
                'tags': entry['tags'],
                'description': entry['description'],
                'downloaded_at': datetime.now().isoformat(),
                'is_generated': is_generated
            }
            
            # Try to get better metadata using a simpler approach
            try:
                import requests
                # Quick request to get page title
                response = requests.get(f"https://www.youtube.com/watch?v={video_id}", timeout=5)
                if response.status_code == 200:
                    # Extract title from page
                    title_match = re.search(r'<title>([^<]+)</title>', response.text)
                    if title_match:
                        title = title_match.group(1)
                        # Clean up YouTube suffix
                        title = title.replace(' - YouTube', '')
                        metadata['title'] = title
                    
                    # Try to extract author
                    author_match = re.search(r'"author":"([^"]+)"', response.text)
                    if author_match:
                        metadata['author'] = author_match.group(1)
            except:
                pass  # Use defaults if this fails
            
            # Format transcript
            formatted_transcript = self._format_transcript(transcript_data)
            
            # Save transcript
            self._save_transcript(video_id, metadata, formatted_transcript, transcript_data)
            
            # Update log
            self.processing_log["processed"][video_id] = {
                "title": metadata['title'],
                "processed_at": metadata['downloaded_at'],
                "line_num": entry['line_num']
            }
            
            print(f"  ✅ Saved: {metadata['title'][:60]}")
            return metadata
            
        except Exception as e:
            error_msg = str(e)
            print(f"  ❌ Failed: {error_msg[:100]}")
            
            self.processing_log["failed"][video_id] = {
                "error": error_msg,
                "attempted_at": datetime.now().isoformat(),
                "line_num": entry['line_num']
            }
            return None
    
    def _format_transcript(self, transcript_data: List[Dict]) -> str:
        """Format transcript for readability"""
        if not transcript_data:
            return "No transcript data available."
        
        paragraphs = []
        current_paragraph = []
        
        for entry in transcript_data:
            # Handle different possible formats
            if isinstance(entry, dict):
                text = entry.get('text', '').strip()
            else:
                text = str(entry).strip()
            
            if text:
                current_paragraph.append(text)
                
                # Create paragraph breaks at natural pauses
                if text.endswith(('.', '!', '?')) and len(' '.join(current_paragraph)) > 200:
                    paragraphs.append(' '.join(current_paragraph))
                    current_paragraph = []
        
        if current_paragraph:
            paragraphs.append(' '.join(current_paragraph))
        
        return '\n\n'.join(paragraphs) if paragraphs else "Transcript processing failed."
    
    def _save_transcript(self, video_id: str, metadata: Dict, 
                         formatted_transcript: str, raw_transcript: List[Dict]):
        """Save transcript to file"""
        # Clean filename
        safe_title = re.sub(r'[^\w\s-]', '', metadata['title'])[:50].strip()
        if not safe_title:
            safe_title = video_id
        
        filename = f"{video_id}_{safe_title}.md"
        filepath = self.transcripts_dir / filename
        
        # Create markdown content
        content = f"""# {metadata['title']}

**Video ID:** {video_id}
**URL:** {metadata['url']}
**Author:** {metadata['author']}
**Downloaded:** {metadata['downloaded_at']}
**Transcript Type:** {'Auto-generated' if metadata.get('is_generated') else 'Manual/Unknown'}
"""
        
        if metadata.get('tags'):
            content += f"**Tags:** #{' #'.join(metadata['tags'])}\n"
        
        if metadata.get('description'):
            content += f"\n## Description\n{metadata['description']}\n"
        
        content += f"""
---

## Transcript

{formatted_transcript}

---

<!-- 
Raw Transcript Data (hidden)
Video ID: {video_id}
Entries: {len(raw_transcript)}
-->
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def generate_status_report(self, entries: List[Dict]) -> str:
        """Generate a status report with automatic markings"""
        total = len(entries)
        processed = sum(1 for e in entries if e['is_processed'])
        pending = total - processed
        
        report = []
        report.append("# YouTube Processing Status Report")
        report.append(f"\n📊 **Summary**: {processed}/{total} videos processed")
        report.append(f"⏳ **Pending**: {pending} videos")
        report.append(f"📅 **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        
        if pending > 0:
            report.append("## 🔄 Pending Videos\n")
            for entry in entries:
                if not entry['is_processed']:
                    line = f"- Line {entry['line_num']}: `{entry['video_id']}`"
                    if entry['description']:
                        line += f" - {entry['description']}"
                    report.append(line)
        
        if processed > 0:
            report.append("\n## ✅ Processed Videos\n")
            for entry in entries:
                if entry['is_processed']:
                    line = f"- Line {entry['line_num']}: `{entry['video_id']}`"
                    if entry['description']:
                        line += f" - {entry['description']}"
                    report.append(line)
        
        if self.processing_log.get("failed"):
            report.append("\n## ❌ Failed Videos\n")
            for video_id, info in self.processing_log["failed"].items():
                error = info.get('error', 'Unknown error')[:100]
                report.append(f"- `{video_id}`: {error}")
        
        return "\n".join(report)
    
    def process_new_videos(self, force_all: bool = False):
        """Main processing function - only downloads new videos"""
        print("🎬 Smart YouTube Transcript Processor")
        print("=" * 50)
        
        # Parse the YouTube list
        entries = self.parse_youtube_list()
        
        if not entries:
            print("No YouTube URLs found in the list.")
            print(f"Add URLs to: {self.youtube_list}")
            return
        
        # Filter to unprocessed videos
        if force_all:
            to_process = entries
        else:
            to_process = [e for e in entries if not e['is_processed']]
        
        print(f"📋 Found {len(entries)} total videos")
        print(f"✅ Already processed: {len(entries) - len(to_process)}")
        print(f"📥 To download: {len(to_process)}\n")
        
        if not to_process:
            print("All videos have been processed! 🎉")
            print("Add new URLs to the list to process more.")
            return
        
        # Process each video
        success_count = 0
        for i, entry in enumerate(to_process, 1):
            print(f"\n[{i}/{len(to_process)}] Processing {entry['video_id']}")
            if entry.get('description'):
                print(f"  📝 {entry['description']}")
            
            result = self.download_transcript(entry)
            if result:
                success_count += 1
        
        # Save processing log
        self._save_processing_log()
        
        # Generate status report
        print("\n" + "=" * 50)
        print(f"✅ Successfully processed: {success_count}/{len(to_process)}")
        
        if self.processing_log.get("failed"):
            print(f"❌ Failed: {len(self.processing_log['failed'])}")
            print("\nTip: Some videos might not have transcripts available.")
            print("Failed videos are logged in processing_log.json")
        
        # Save status report
        report_path = self.transcripts_dir.parent / "processing_status.md"
        entries = self.parse_youtube_list()  # Re-parse to get updated status
        report = self.generate_status_report(entries)
        
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"\n📊 Status report: {report_path}")
        print(f"📁 Transcripts saved to: {self.transcripts_dir}")
    
    def show_status(self):
        """Show current processing status"""
        entries = self.parse_youtube_list()
        report = self.generate_status_report(entries)
        print(report)
    
    def show_queue(self):
        """Show only unprocessed videos"""
        entries = self.parse_youtube_list()
        pending = [e for e in entries if not e['is_processed']]
        
        if not pending:
            print("🎉 No videos in queue - all processed!")
        else:
            print(f"📋 Queue: {len(pending)} videos to process\n")
            for i, entry in enumerate(pending, 1):
                print(f"{i}. {entry['full_url']}")
                if entry['description']:
                    print(f"   {entry['description']}")
                print()

# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Smart YouTube Transcript Processor')
    parser.add_argument('command', nargs='?', default='process',
                       choices=['process', 'status', 'queue'],
                       help='Command to run (default: process)')
    parser.add_argument('--list', default='knowledge_base/sources/youtube_talks.md',
                       help='Path to YouTube list file')
    parser.add_argument('--output', default='knowledge_base/transcripts/raw',
                       help='Output directory for transcripts')
    parser.add_argument('--force-all', action='store_true',
                       help='Force re-download all videos')
    
    args = parser.parse_args()
    
    processor = SmartYouTubeProcessor(args.list, args.output)
    
    if args.command == 'status':
        processor.show_status()
    elif args.command == 'queue':
        processor.show_queue()
    else:
        processor.process_new_videos(force_all=args.force_all)
