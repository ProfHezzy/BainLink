from django import template
from urllib.parse import urlparse, parse_qs
import re

register = template.Library()

@register.filter(name='embed_url')
def embed_url(url):
    """
    Converts video URLs into embed URLs with additional parameters for better display.
    Supports:
    - YouTube (regular and shortened URLs)
    - Vimeo
    - Facebook (basic support)
    - DailyMotion
    - TikTok (basic support)
    """
    if not url:
        return ''
    
    try:
        # YouTube handling
        if 'youtube.com' in url or 'youtu.be' in url:
            parsed = urlparse(url)
            
            # Extract video ID from different YouTube URL formats
            if 'youtube.com' in url:
                if 'embed' in url:  # Already an embed URL
                    return url.split('?')[0] + '?rel=0&modestbranding=1'
                video_id = parse_qs(parsed.query).get('v', [''])[0]
            else:  # youtu.be
                video_id = parsed.path[1:].split('?')[0]
            
            if video_id:
                return (f'https://www.youtube.com/embed/{video_id}'
                       '?rel=0&modestbranding=1&showinfo=0&autoplay=0')
        
        # Vimeo handling
        elif 'vimeo.com' in url:
            video_id = urlparse(url).path[1:].split('?')[0]
            if video_id.isdigit():
                return (f'https://player.vimeo.com/video/{video_id}'
                       '?title=0&byline=0&portrait=0')
        
        # DailyMotion handling
        elif 'dailymotion.com' in url or 'dai.ly' in url:
            parsed = urlparse(url)
            if 'dailymotion.com' in url:
                video_id = parsed.path.split('/')[-1].split('_')[0]
            else:  # dai.ly
                video_id = parsed.path[1:]
            if video_id:
                return f'https://www.dailymotion.com/embed/video/{video_id}'
        
        # Facebook handling (basic)
        elif 'facebook.com' in url or 'fb.watch' in url:
            # Facebook requires their own embed code, but we can try to extract the video ID
            match = re.search(r'videos?/(\d+)', url)
            if match:
                return f'https://www.facebook.com/plugins/video.php?href={url}&show_text=0'
        
        # TikTok handling (basic)
        elif 'tiktok.com' in url:
            video_id = url.split('/')[-1]
            if video_id:
                return f'https://www.tiktok.com/embed/v2/{video_id}'
    
    except Exception as e:
        # Log error in production
        # import logging
        # logger = logging.getLogger(__name__)
        # logger.error(f"Error processing video URL {url}: {str(e)}")
        pass
    
    # Return original URL if no embed pattern matched
    return url


@register.filter(name='video_thumbnail')
def video_thumbnail(url):
    """
    Generates a thumbnail URL for video platforms
    """
    try:
        # YouTube thumbnails
        if 'youtube.com' in url or 'youtu.be' in url:
            embed_url = embed_url(url)  # Reuse our embed function
            video_id = embed_url.split('/')[-1].split('?')[0]
            if video_id:
                return f'https://img.youtube.com/vi/{video_id}/hqdefault.jpg'
        
        # Vimeo thumbnails (would require API call in practice)
        elif 'vimeo.com' in url:
            video_id = urlparse(url).path[1:].split('?')[0]
            if video_id.isdigit():
                # Note: This would require a Vimeo API call in reality
                return f'https://vumbnail.com/{video_id}.jpg'
    
    except Exception:
        pass
    
    return None


@register.filter(name='is_video_url')
def is_video_url(url):
    """
    Checks if a URL is from a supported video platform
    """
    platforms = [
        'youtube.com',
        'youtu.be',
        'vimeo.com',
        'dailymotion.com',
        'dai.ly',
        'facebook.com',
        'fb.watch',
        'tiktok.com'
    ]
    return any(platform in url for platform in platforms) if url else False