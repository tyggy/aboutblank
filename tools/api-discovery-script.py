#!/usr/bin/env python3
"""
Discover how to use the YouTube Transcript API with list and fetch methods
"""

from youtube_transcript_api import YouTubeTranscriptApi
import json

def discover_api():
    """Figure out how this API version works"""
    
    print("🔍 API Discovery Tool")
    print("=" * 50)
    
    # Check available methods
    print("\n📚 Available methods on YouTubeTranscriptApi:")
    methods = [m for m in dir(YouTubeTranscriptApi) if not m.startswith('_')]
    for method in methods:
        print(f"  - {method}")
    
    # Test video ID
    video_id = "xaUknipwnpw"  # One of your Michael Levin videos
    print(f"\n🧪 Testing with video: {video_id}")
    print("=" * 50)
    
    # Try Method 1: list() directly
    print("\n📋 Method 1: Trying YouTubeTranscriptApi.list(video_id)")
    try:
        result = YouTubeTranscriptApi.list(video_id)
        print(f"  ✅ Success! Got: {type(result)}")
        
        # Explore what we got
        if hasattr(result, '__dict__'):
            print(f"  Attributes: {list(result.__dict__.keys())}")
        
        # Check if it's iterable
        try:
            for i, item in enumerate(result):
                if i == 0:  # Just show first item
                    print(f"  First item type: {type(item)}")
                    if hasattr(item, '__dict__'):
                        print(f"  Item attributes: {list(item.__dict__.keys())}")
                    
                    # Try to fetch from the item
                    if hasattr(item, 'fetch'):
                        print("  📥 Item has fetch() method, trying it...")
                        transcript = item.fetch()
                        print(f"  ✅ Fetch worked! Got {len(transcript)} entries")
                        print(f"  First entry: {transcript[0]}")
                        
                        # Save a test file
                        with open(f"test_{video_id}.md", 'w') as f:
                            f.write(f"# Test Transcript for {video_id}\n\n")
                            f.write("## First 5 entries:\n\n")
                            for entry in transcript[:5]:
                                f.write(f"- {entry}\n")
                        print(f"  💾 Saved test file: test_{video_id}.md")
                        return True
                        
                break
        except TypeError:
            print("  ℹ️  Result is not directly iterable")
        
        # Check for methods on the result
        if hasattr(result, 'find_transcript'):
            print("  📝 Has find_transcript method")
            try:
                transcript = result.find_transcript(['en'])
                if hasattr(transcript, 'fetch'):
                    data = transcript.fetch()
                    print(f"  ✅ Got transcript with {len(data)} entries")
                    return True
            except Exception as e:
                print(f"  ⚠️  find_transcript failed: {e}")
        
    except Exception as e:
        print(f"  ❌ Failed: {e}")
    
    # Try Method 2: fetch() directly
    print("\n📥 Method 2: Trying YouTubeTranscriptApi.fetch(video_id)")
    try:
        result = YouTubeTranscriptApi.fetch(video_id)
        print(f"  ✅ Success! Got: {type(result)}")
        if isinstance(result, list):
            print(f"  Got {len(result)} entries")
            print(f"  First entry: {result[0]}")
            return True
    except Exception as e:
        print(f"  ❌ Failed: {e}")
    
    # Try Method 3: Different import pattern
    print("\n🔄 Method 3: Trying different import pattern")
    try:
        import youtube_transcript_api
        
        # Check module-level functions
        print("  Module functions:", [f for f in dir(youtube_transcript_api) if not f.startswith('_')])
        
        # Try get_transcript if it exists at module level
        if hasattr(youtube_transcript_api, 'get_transcript'):
            print("  📝 Found get_transcript at module level")
            result = youtube_transcript_api.get_transcript(video_id)
            print(f"  ✅ Got {len(result)} entries")
            return True
            
    except Exception as e:
        print(f"  ❌ Failed: {e}")
    
    print("\n" + "=" * 50)
    print("❓ Could not find working method. Try manual exploration:")
    print("\nIn Python interactive mode, try:")
    print(">>> from youtube_transcript_api import YouTubeTranscriptApi")
    print(">>> result = YouTubeTranscriptApi.list('xaUknipwnpw')")
    print(">>> type(result)")
    print(">>> dir(result)")
    
    return False


def simple_working_solution():
    """A simple solution that should work based on what we know"""
    print("\n🎯 Attempting Simple Solution")
    print("=" * 50)
    
    video_id = "xaUknipwnpw"
    
    try:
        # Based on the available methods, try this approach
        from youtube_transcript_api import YouTubeTranscriptApi
        
        # The list method likely returns a TranscriptList object
        transcript_list = YouTubeTranscriptApi.list(video_id)
        
        # Try to get the first available transcript
        # This might work if transcript_list is iterable
        transcript = None
        
        # Attempt 1: Direct iteration
        try:
            for t in transcript_list:
                transcript = t.fetch()
                break
        except:
            pass
        
        # Attempt 2: Try find methods
        if not transcript:
            try:
                # Try to find English transcript
                t = transcript_list.find_transcript(['en'])
                transcript = t.fetch()
            except:
                try:
                    # Try any transcript
                    t = transcript_list.find_generated_transcript(['en'])
                    transcript = t.fetch()
                except:
                    pass
        
        if transcript:
            print(f"✅ Success! Got {len(transcript)} entries")
            
            # Format and save
            text = ' '.join([entry['text'] for entry in transcript])
            
            with open(f"{video_id}_transcript.md", 'w') as f:
                f.write(f"# Transcript for {video_id}\n\n")
                f.write(text)
            
            print(f"💾 Saved to {video_id}_transcript.md")
            return True
        else:
            print("❌ Could not get transcript")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    # Run discovery
    success = discover_api()
    
    if not success:
        print("\nTrying simple solution...")
        simple_working_solution()
    
    print("\n📚 Next Steps:")
    print("1. Check if a test file was created")
    print("2. If it worked, we can adapt the full processor")
    print("3. If not, we need to explore the API manually")
