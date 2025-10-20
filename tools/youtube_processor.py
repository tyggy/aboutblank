#!/usr/bin/env python3
"""
CORRECT YouTube Transcript Downloader
Using the right API method: list_transcripts (not list)
"""

import re
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

def download_transcript_correct(video_id: str) -> Optional[Dict]:
    """
    Download transcript using the CORRECT API method
    """
    from youtube_transcript_api import YouTubeTranscriptApi
    
    try:
        # The CORRECT method is list_transcripts (not list)
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Try to get English transcript
        transcript = None
        transcript_data = None
        
        # First try manually created English transcript
        try:
            transcript = transcript_list.find_manually_created_transcript(['en'])
            transcript_data = transcript.fetch()
            print(f"  ✅ Got manual English transcript")
        except:
            # Try auto-generated English transcript
            try:
                transcript = transcript_list.find_generated_transcript(['en'])
                transcript_data = transcript.fetch()
                print(f"  ✅ Got auto-generated English transcript")
            except:
                # Get any available transcript
                try:
                    for t in transcript_list:
                        transcript = t
                        transcript_data = t.fetch()
                        print(f"  ✅ Got transcript in {t.language_code}")
                        break
                except:
                    pass
        
        if transcript_data:
            return {
                'data': transcript_data,
                'language': transcript.language_code if transcript else 'unknown'
            }
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    return None


def process_youtube_videos():
    """
    Process your YouTube videos with correct API
    """
    print("🎬 YouTube Transcript Processor - CORRECT VERSION")
    print("=" * 50)
    
    # Your video IDs
    video_ids = [
        ("xaUknipwnpw", "Michael Levin: Intelligence Beyond Brains"),
        ("staFQw-_e6E", "Collective Intelligence"),
        ("BRJ48AU5gP4", "Bioelectric Networks"),
        ("nnk2Umxa3OY", "Xenobots and Synthetic Life"),
        ("xRGnSDtKu9c", "Morphogenetic Fields"),
        ("IZ6G50pqbIY", "Navigation in Problem Spaces"),
        ("Yt5NN0KcRlQ", "Collective Goals")
    ]
    
    # Create output directory
    output_dir = Path("knowledge_base/transcripts/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    
    for video_id, description in video_ids:
        print(f"\n📹 Processing: {video_id}")
        print(f"   {description}")
        
        result = download_transcript_correct(video_id)
        
        if result:
            # Format transcript
            transcript_data = result['data']
            
            # Extract text
            text_parts = []
            for entry in transcript_data:
                text = entry.get('text', '').strip()
                if text:
                    text_parts.append(text)
            
            # Join and format
            full_text = ' '.join(text_parts)
            
            # Create paragraphs at sentence boundaries
            sentences = full_text.split('. ')
            paragraphs = []
            current = []
            
            for sentence in sentences:
                current.append(sentence.strip())
                if len(' '.join(current)) > 300:
                    paragraphs.append(' '.join(current) + '.')
                    current = []
            
            if current:
                paragraphs.append(' '.join(current))
            
            formatted_text = '\n\n'.join(paragraphs)
            
            # Save to file
            safe_desc = re.sub(r'[^\w\s-]', '', description)[:50].strip()
            filename = f"{video_id}_{safe_desc}.md"
            filepath = output_dir / filename
            
            content = f"""# {description}

**Video ID:** {video_id}
**URL:** https://www.youtube.com/watch?v={video_id}
**Language:** {result['language']}
**Downloaded:** {datetime.now().isoformat()}

---

## Transcript

{formatted_text}

---

<!-- Transcript entries: {len(transcript_data)} -->
"""
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"  💾 Saved to: {filepath.name}")
            success_count += 1
        else:
            print(f"  ⏭️  Skipping - no transcript available")
    
    print("\n" + "=" * 50)
    print(f"✅ Successfully processed: {success_count}/{len(video_ids)} videos")
    print(f"📁 Transcripts saved in: {output_dir}")
    
    return success_count > 0


def test_single_video():
    """
    Test with a single video to verify it works
    """
    print("\n🧪 Testing with single video...")
    
    test_id = "xaUknipwnpw"  # Michael Levin video
    result = download_transcript_correct(test_id)
    
    if result:
        print(f"✅ TEST PASSED! Got {len(result['data'])} transcript entries")
        print(f"   Language: {result['language']}")
        print(f"   First entry: {result['data'][0]['text'][:100]}...")
        return True
    else:
        print("❌ TEST FAILED")
        return False


def process_from_file(filepath: str = "knowledge_base/sources/youtube_talks.md"):
    """
    Process videos from your chronological list file
    """
    list_path = Path(filepath)
    
    if not list_path.exists():
        print(f"❌ File not found: {list_path}")
        print("\nCreating example file...")
        list_path.parent.mkdir(parents=True, exist_ok=True)
        with open(list_path, 'w') as f:
            f.write("""# YouTube Talks - Buddhism & AI

https://www.youtube.com/watch?v=xaUknipwnpw - Michael Levin: Intelligence Beyond Brains
https://www.youtube.com/watch?v=staFQw-_e6E - Collective Intelligence
https://www.youtube.com/watch?v=BRJ48AU5gP4 - Bioelectric Networks
https://www.youtube.com/watch?v=nnk2Umxa3OY - Xenobots
https://www.youtube.com/watch?v=xRGnSDtKu9c - Morphogenetic Fields
https://www.youtube.com/watch?v=IZ6G50pqbIY - Navigation in Problem Spaces
https://www.youtube.com/watch?v=Yt5NN0KcRlQ - Collective Goals
""")
        print(f"✅ Created example file: {list_path}")
    
    # Parse file
    videos = []
    with open(list_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('<!--'):
                continue
            
            # Extract URL and description
            url_match = re.search(r'(https?://[^\s]+)', line)
            if url_match:
                url = url_match.group(1)
                # Extract video ID
                id_match = re.search(r'[?&]v=([^&]+)', url)
                if id_match:
                    video_id = id_match.group(1)
                    # Get description (everything after URL)
                    desc = line[url_match.end():].strip()
                    if desc.startswith('-'):
                        desc = desc[1:].strip()
                    videos.append((video_id, desc or f"Video {video_id}"))
    
    print(f"📋 Found {len(videos)} videos in {list_path}")
    
    # Create output directory
    output_dir = Path("knowledge_base/transcripts/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check what's already processed
    existing = list(output_dir.glob("*.md"))
    existing_ids = {f.name.split('_')[0] for f in existing}
    
    to_process = [(vid, desc) for vid, desc in videos if vid not in existing_ids]
    
    print(f"✅ Already processed: {len(videos) - len(to_process)}")
    print(f"📥 To download: {len(to_process)}")
    
    if not to_process:
        print("\n🎉 All videos already processed!")
        return
    
    # Process each video
    success = 0
    for i, (video_id, description) in enumerate(to_process, 1):
        print(f"\n[{i}/{len(to_process)}] Processing: {video_id}")
        print(f"     {description}")
        
        result = download_transcript_correct(video_id)
        if result:
            # Save transcript (same as above)
            transcript_data = result['data']
            text = ' '.join([e.get('text', '') for e in transcript_data])
            
            # Simple formatting
            paragraphs = []
            words = text.split()
            current = []
            for word in words:
                current.append(word)
                if len(current) > 50 and word.endswith('.'):
                    paragraphs.append(' '.join(current))
                    current = []
            if current:
                paragraphs.append(' '.join(current))
            
            # Save
            safe_desc = re.sub(r'[^\w\s-]', '', description)[:40]
            filename = f"{video_id}_{safe_desc}.md"
            filepath = output_dir / filename
            
            with open(filepath, 'w') as f:
                f.write(f"# {description}\n\n")
                f.write(f"**Video:** https://www.youtube.com/watch?v={video_id}\n\n")
                f.write("## Transcript\n\n")
                f.write('\n\n'.join(paragraphs))
            
            print(f"  ✅ Saved: {filename}")
            success += 1
    
    print("\n" + "=" * 50)
    print(f"✅ Successfully processed: {success}/{len(to_process)}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            # Run test
            test_single_video()
        elif sys.argv[1] == "all":
            # Process all known videos
            process_youtube_videos()
        else:
            # Process from file
            process_from_file(sys.argv[1])
    else:
        # Default: process from your list file
        process_from_file()
