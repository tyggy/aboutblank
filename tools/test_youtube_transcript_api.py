import youtube_transcript_api
print("Package version:", youtube_transcript_api.__version__ if hasattr(youtube_transcript_api, '__version__') else "unknown")

from youtube_transcript_api import YouTubeTranscriptApi
print("Available methods:", [m for m in dir(YouTubeTranscriptApi) if not m.startswith('_')])

# Try the correct syntax
try:
    transcript = YouTubeTranscriptApi.get_transcript("xaUknipwnpw")
    print(f"✅ Success! Got {len(transcript)} entries")
except Exception as e:
    print(f"❌ Error: {e}")