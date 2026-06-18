#
# To run the program: python Source/main.py "url"
#
import sys
import os
import re
import json
import requests
import yt_dlp
import anthropic
from dotenv import load_dotenv

load_dotenv()


def extract_video_id(url):
    """Extract the 11-character video ID from various YouTube URL formats."""
    match = re.search(r'(?:v=|/v/|youtu\.be/|/embed/)([a-zA-Z0-9_-]{11})', url)
    return match.group(1) if match else None


def get_metadata(url):
    """Return (title, channel) using yt-dlp."""
    opts = {'quiet': True, 'no_warnings': True, 'skip_download': True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    title = info.get('title', 'Untitled')
    channel = info.get('channel') or info.get('uploader') or 'Unknown'
    return title, channel


# ---------------------------------------------------------------------------
# AI Summary (best-effort scrape from YouTube's page data)
# ---------------------------------------------------------------------------

def get_ai_summary(video_id):
    """Try to extract YouTube's AI-generated summary from the watch page."""
    try:
        url = f'https://www.youtube.com/watch?v={video_id}'
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/131.0.0.0 Safari/537.36'
            ),
            'Accept-Language': 'en-US,en;q=0.9',
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()

        data = _extract_yt_initial_data(resp.text)
        if data is None:
            return None

        return _find_ai_summary_in_panels(data)
    except Exception:
        return None


def _extract_yt_initial_data(html):
    """Pull the ytInitialData JSON object out of the page HTML."""
    marker = 'var ytInitialData = '
    idx = html.find(marker)
    if idx == -1:
        return None
    start = idx + len(marker)
    end = html.find(';</script>', start)
    if end == -1:
        return None
    try:
        return json.loads(html[start:end])
    except json.JSONDecodeError:
        return None


def _find_ai_summary_in_panels(data):
    """Walk the engagement panels looking for an AI-generated summary."""
    for panel in data.get('engagementPanels', []):
        renderer = panel.get('engagementPanelSectionListRenderer', {})
        panel_id = renderer.get('panelIdentifier', '')
        if 'structured-description' not in panel_id:
            continue

        items = (
            renderer
            .get('content', {})
            .get('structuredDescriptionContentRenderer', {})
            .get('items', [])
        )
        for item in items:
            for key in item:
                if 'summary' in key.lower():
                    text = _extract_text(item[key])
                    if text and len(text) > 30:
                        return text
    return None


def _extract_text(obj):
    """Recursively pull readable text from a YouTube JSON fragment."""
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        if 'runs' in obj:
            joined = ''.join(run.get('text', '') for run in obj['runs'])
            if joined:
                return joined
        for key in ('simpleText', 'text', 'content'):
            if key in obj and isinstance(obj[key], str):
                return obj[key]
        for val in obj.values():
            result = _extract_text(val)
            if result and len(result) > 30:
                return result
    if isinstance(obj, list):
        for item in obj:
            result = _extract_text(item)
            if result and len(result) > 30:
                return result
    return None


# ---------------------------------------------------------------------------
# Transcript
# ---------------------------------------------------------------------------

def get_transcript(video_id):
    """Fetch the transcript and return it formatted with minute-level timestamps."""
    from youtube_transcript_api import YouTubeTranscriptApi
    raw = YouTubeTranscriptApi().fetch(video_id)
    entries = [{'text': s.text, 'start': s.start, 'duration': s.duration} for s in raw]
    return _format_transcript(entries)


def _format_transcript(entries):
    """Join transcript entries, inserting a [M:00] marker at each whole-minute boundary."""
    paragraphs = []
    current = []
    next_minute = 1

    for entry in entries:
        text = entry['text'].replace('\n', ' ').strip()
        if not text:
            continue
        start = entry['start']

        if start >= next_minute * 60:
            # Flush current paragraph
            if current:
                paragraphs.append(' '.join(current))
                current = []
            current.append(f'[{next_minute}:00] {text}')
            next_minute += 1
            # Skip past any further minute boundaries this segment crosses
            while start >= next_minute * 60:
                next_minute += 1
        else:
            current.append(text)

    if current:
        paragraphs.append(' '.join(current))

    return '\n\n'.join(paragraphs)


# ---------------------------------------------------------------------------
# AI-generated summary via Claude
# ---------------------------------------------------------------------------

def generate_summary(transcript):
    """Generate a one-paragraph summary of the transcript using Claude."""
    try:
        client = anthropic.Anthropic()
        message = client.messages.create(
            model='claude-sonnet-4-20250514',
            max_tokens=300,
            messages=[{
                'role': 'user',
                'content': (
                    'Write a single concise paragraph summarizing this video transcript. '
                    'Focus on the key points and main takeaways.\n\n'
                    f'{transcript[:12000]}'
                ),
            }],
        )
        return message.content[0].text
    except Exception as e:
        print(f'  Warning: Could not generate summary: {e}')
        return None


# ---------------------------------------------------------------------------
# Markdown assembly & file output
# ---------------------------------------------------------------------------

def sanitize_filename(name):
    """Remove characters that are illegal in Windows filenames."""
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = name.strip('. ')
    return name[:25] if name else 'video'


def build_markdown(title, channel, summary, transcript, url):
    lines = [
        f'# {title}',
        '',
        url,
        '',
        f'**Channel:** {channel}',
        '',
        '## Summary',
        '',
    ]
    lines.append(summary if summary else '*AI summary not available for this video.*')
    lines += ['', '## Transcript', '', transcript, '']
    return '\n'.join(lines)


def main():
    # --- Get URL ---
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input('Enter YouTube URL: ').strip()

    video_id = extract_video_id(url)
    if not video_id:
        print('Error: Could not extract a video ID from that URL.')
        sys.exit(1)

    print(f'Video ID: {video_id}')

    # --- Metadata ---
    print('Fetching video metadata...')
    title, channel = get_metadata(url)
    print(f'  Title:   {title}')
    print(f'  Channel: {channel}')

    # --- AI Summary ---
    print('Looking for AI summary...')
    summary = get_ai_summary(video_id)
    print('  AI summary found.' if summary else '  AI summary not available.')

    # --- Transcript ---
    print('Fetching transcript...')
    transcript = get_transcript(video_id)

    # --- Generate summary if none found ---
    if not summary:
        print('Generating summary with Claude...')
        summary = generate_summary(transcript)

    # --- Write file ---
    markdown = build_markdown(title, channel, summary, transcript, url)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, '..', 'Output')
    os.makedirs(output_dir, exist_ok=True)

    filename = sanitize_filename(title) + '.md'
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(markdown)

    print(f'Saved to: {filepath}')


if __name__ == '__main__':
    main()
