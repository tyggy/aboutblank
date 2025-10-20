#!/usr/bin/env python3
"""
YouTube Transcript Downloader for Knowledge Base Creation
Extracts transcripts from YouTube videos and prepares them for editing
"""

import os
import re
import argparse
from typing import List, Dict, Optional
from datetime import datetime

# Install required packages:
# pip install youtube-transcript-api pytube yt-dlp

from youtube_transcript_api import YouTubeTranscriptApi
from pytube import YouTube
import json

class TranscriptDownloader:
    def __init__(self, output_dir: str = "transcripts"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from various URL formats"""
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def get_video_metadata(self, video_id: str) -> Dict:
        """Get video title, author, and other metadata"""
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            yt = YouTube(url)
            return {
                'title': yt.title,
                'author': yt.author,
                'length': yt.length,
                'publish_date': str(yt.publish_date) if yt.publish_date else 'Unknown',
                'description': yt.description[:500] if yt.description else '',
                'url': url
            }
        except Exception as e:
            print(f"Could not fetch metadata: {e}")
            return {
                'title': f'Video_{video_id}',
                'author': 'Unknown',
                'url': f"https://www.youtube.com/watch?v={video_id}"
            }
    
    def download_transcript(self, video_url: str, languages: List[str] = ['en']) -> Optional[Dict]:
        """Download transcript for a single video"""
        video_id = self.extract_video_id(video_url)
        if not video_id:
            print(f"Could not extract video ID from: {video_url}")
            return None
        
        try:
            # Get transcript
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Try to get manually created transcript first
            try:
                transcript = transcript_list.find_manually_created_transcript(languages)
            except:
                # Fall back to auto-generated
                transcript = transcript_list.find_generated_transcript(languages)
            
            # Fetch the actual transcript
            transcript_data = transcript.fetch()
            
            # Get metadata
            metadata = self.get_video_metadata(video_id)
            
            # Format transcript
            formatted_transcript = self.format_transcript(transcript_data)
            
            return {
                'video_id': video_id,
                'metadata': metadata,
                'raw_transcript': transcript_data,
                'formatted_transcript': formatted_transcript,
                'language': transcript.language_code,
                'is_generated': transcript.is_generated,
            }
            
        except Exception as e:
            print(f"Error downloading transcript for {video_url}: {e}")
            return None
    
    def format_transcript(self, transcript_data: List[Dict]) -> str:
        """Format transcript for readability"""
        paragraphs = []
        current_paragraph = []
        
        for entry in transcript_data:
            text = entry['text'].strip()
            if text:
                current_paragraph.append(text)
                
                # Create paragraph breaks at natural pauses
                if text.endswith(('.', '!', '?')) and len(' '.join(current_paragraph)) > 200:
                    paragraphs.append(' '.join(current_paragraph))
                    current_paragraph = []
        
        # Add remaining text
        if current_paragraph:
            paragraphs.append(' '.join(current_paragraph))
        
        return '\n\n'.join(paragraphs)
    
    def save_transcript(self, transcript_data: Dict) -> str:
        """Save transcript to file with metadata"""
        video_id = transcript_data['video_id']
        metadata = transcript_data['metadata']
        
        # Clean filename
        safe_title = re.sub(r'[^\w\s-]', '', metadata['title'])[:50]
        filename = f"{video_id}_{safe_title}.md"
        filepath = os.path.join(self.output_dir, filename)
        
        # Create markdown content
        content = f"""# {metadata['title']}

**Author:** {metadata['author']}
**URL:** {metadata['url']}
**Published:** {metadata['publish_date']}
**Transcript Type:** {'Auto-generated' if transcript_data['is_generated'] else 'Manual'}
**Downloaded:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Description
{metadata['description']}

---

## Transcript

{transcript_data['formatted_transcript']}

---

## Raw Transcript Data
<!-- 
This section contains the raw timestamp data for reference.
Hidden in markdown but available for processing.

{json.dumps(transcript_data['raw_transcript'], indent=2)}
-->
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Saved transcript to: {filepath}")
        return filepath
    
    def batch_download(self, urls: List[str]) -> List[str]:
        """Download transcripts for multiple videos"""
        saved_files = []
        
        for i, url in enumerate(urls, 1):
            print(f"\nProcessing {i}/{len(urls)}: {url}")
            transcript_data = self.download_transcript(url)
            
            if transcript_data:
                filepath = self.save_transcript(transcript_data)
                saved_files.append(filepath)
            else:
                print(f"Failed to download transcript for: {url}")
        
        return saved_files

def create_claude_prompt(transcript_file: str) -> str:
    """Generate a Claude prompt for copyediting"""
    prompt = f"""Please copyedit the following YouTube transcript. Focus on:

1. **Clarity**: Fix unclear sentences and improve flow
2. **Grammar**: Correct grammatical errors from auto-transcription
3. **Punctuation**: Add appropriate punctuation
4. **Paragraph Structure**: Create logical paragraph breaks
5. **Speaker Identification**: If multiple speakers, identify them clearly
6. **Technical Terms**: Ensure technical terms are correctly transcribed
7. **Readability**: Make the text readable while preserving the speaker's voice

Keep the original meaning and tone. Mark any sections that are unclear or potentially mistranscribed with [?].

Transcript file: {transcript_file}

Please provide:
1. The edited transcript
2. A brief summary of main changes made
3. Any sections that need human review"""
    
    return prompt

def extract_urls_from_file(filepath: str) -> List[str]:
    """Extract YouTube URLs from a markdown or text file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all YouTube URLs
    pattern = r'https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)[A-Za-z0-9_-]+'
    urls = re.findall(pattern, content)
    
    return list(set(urls))  # Remove duplicates

def main():
    parser = argparse.ArgumentParser(description='Download YouTube transcripts for knowledge base')
    parser.add_argument('input', help='YouTube URL or file containing URLs')
    parser.add_argument('-o', '--output', default='transcripts', help='Output directory')
    parser.add_argument('-l', '--languages', nargs='+', default=['en'], help='Preferred languages')
    parser.add_argument('--prompt', action='store_true', help='Generate Claude editing prompt')
    
    args = parser.parse_args()
    
    downloader = TranscriptDownloader(args.output)
    
    # Determine if input is URL or file
    if args.input.startswith('http'):
        urls = [args.input]
    elif os.path.exists(args.input):
        urls = extract_urls_from_file(args.input)
        print(f"Found {len(urls)} YouTube URLs in file")
    else:
        print(f"Error: {args.input} is not a valid URL or file")
        return
    
    # Download transcripts
    saved_files = downloader.batch_download(urls)
    
    print(f"\n{'='*50}")
    print(f"Downloaded {len(saved_files)} transcripts")
    
    # Generate Claude prompts if requested
    if args.prompt and saved_files:
        prompt_file = os.path.join(args.output, 'claude_prompts.txt')
        with open(prompt_file, 'w', encoding='utf-8') as f:
            for filepath in saved_files:
                f.write(f"\n{'='*50}\n")
                f.write(create_claude_prompt(filepath))
                f.write('\n')
        print(f"Claude prompts saved to: {prompt_file}")

if __name__ == "__main__":
    main()
