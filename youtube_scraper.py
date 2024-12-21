import os
import json
import time
import requests
from bs4 import BeautifulSoup
import yt_dlp
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_youtube_videos(channel_url):
    """
    获取YouTube频道的最新视频
    """
    try:
        print(f"正在获取YouTube频道 {channel_url} 的最新视频...")
        
        # 使用yt-dlp获取频道信息
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'force_generic_extractor': False,
            'playlist_items': '1',  # 只获取最新的一个视频
            'ignoreerrors': True,
            'format': 'best[height<=1080]',  # 限制最高分辨率为1080p
            'no_warnings': True,
            'no_color': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'http_headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://www.youtube.com/',
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                # 尝试获取频道的视频列表
                videos_url = f"{channel_url}/videos"
                print(f"尝试获取视频列表: {videos_url}")
                channel_info = ydl.extract_info(videos_url, download=False)
                
                if not channel_info or not channel_info.get('entries'):
                    print(f"尝试直接从频道获取: {channel_url}")
                    channel_info = ydl.extract_info(channel_url, download=False)
                
                if not channel_info:
                    print(f"无法获取频道 {channel_url} 的信息")
                    return []
                
                videos = []
                entries = channel_info.get('entries', [])
                if not entries and 'title' in channel_info:  # 单个视频的情况
                    entries = [channel_info]
                
                if entries and entries[0]:  # 只处理最新的一个视频
                    entry = entries[0]
                    video_id = entry.get('id', '')
                    if not video_id:
                        print("未找到视频ID")
                        return []
                    
                    # 获取视频详细信息，不下载视频
                    try:
                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                        print(f"获取视频详细信息: {video_url}")
                        
                        # 修改选项，只获取元数据
                        info_opts = ydl_opts.copy()
                        info_opts.update({
                            'format': None,
                            'extract_flat': False,
                            'youtube_include_dash_manifest': False
                        })
                        
                        with yt_dlp.YoutubeDL(info_opts) as info_ydl:
                            video_info = info_ydl.extract_info(video_url, download=False)
                        
                        if video_info:
                            # 使用默认的高质量缩略图
                            thumbnail = f'https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg'
                            
                            videos.append({
                                'channel': video_info.get('uploader', '未知频道'),
                                'title': video_info.get('title', '未知标题'),
                                'url': video_url,
                                'thumbnail': thumbnail
                            })
                            print(f"成功获取视频信息: {video_info.get('title', '未知标题')}")
                    except Exception as e:
                        print(f"获取视频详细信息时发生错误: {str(e)}")
                        return []
                
                return videos
                
            except Exception as e:
                print(f"获取频道信息时发生错误: {str(e)}")
                return []
            
    except Exception as e:
        print(f"获取YouTube视频时发生错误: {str(e)}")
        return []

def get_latest_content(url, max_items=1):
    """
    根据URL类型获取最新内容
    """
    if url.startswith('http'):  # YouTube频道
        return get_youtube_videos(url)

def generate_html(videos, filename='youtube_videos.html'):
    """
    生成HTML页面展示视频列表
    """
    try:
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>最新视频</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    margin: 20px;
                    background-color: #f9f9f9;
                }
                .video-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                    gap: 20px;
                    padding: 20px;
                }
                .video-card {
                    background: white;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    transition: transform 0.2s;
                }
                .video-card:hover {
                    transform: translateY(-5px);
                }
                .thumbnail-container {
                    position: relative;
                    width: 100%;
                    padding-top: 56.25%; /* 16:9 宽高比 */
                }
                .thumbnail {
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                }
                .video-info {
                    padding: 15px;
                }
                .video-title {
                    font-size: 16px;
                    font-weight: bold;
                    margin-bottom: 8px;
                    color: #333;
                }
                .channel-name {
                    color: #606060;
                    font-size: 14px;
                }
                h1 {
                    text-align: center;
                    color: #333;
                    margin-bottom: 30px;
                }
            </style>
        </head>
        <body>
            <h1>最新视频</h1>
            <div class="video-grid">
        """
        
        for video in videos:
            html_content += f"""
            <div class="video-card">
                <a href="{video['url']}" target="_blank">
                    <div class="thumbnail-container">
                        <img class="thumbnail" src="{video['thumbnail']}" alt="{video['title']}">
                    </div>
                </a>
                <div class="video-info">
                    <div class="video-title">{video['title']}</div>
                    <div class="channel-name">{video['channel']}</div>
                </div>
            </div>
            """
            
        html_content += """
            </div>
        </body>
        </html>
        """
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        print(f"HTML文件已保存到 {filename}")
        
    except Exception as e:
        print(f"保存HTML文件时发生错误: {str(e)}")

def save_videos_to_json(videos):
    """保存视频信息到JSON文件"""
    output_file = os.path.join(os.path.dirname(__file__), 'youtube_videos.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)
    print(f"\n视频信息已保存到: {output_file}")

def main():
    """
    主函数
    """
    # YouTube频道列表
    channels = [
        'https://www.youtube.com/@nicolevdh',  # Nicole van der Hoeven
        'https://www.youtube.com/@TheVerge',   # The Verge
        'https://www.youtube.com/@mkbhd',      # Marques Brownlee (MKBHD)
        'https://www.youtube.com/@lexfridman', # Lex Fridman
    ]
    
    all_videos = []
    
    # 使用线程池并发获取视频信息
    with ThreadPoolExecutor(max_workers=4) as executor:
        # 创建future对象的字典，用于跟踪每个任务
        future_to_channel = {executor.submit(get_youtube_videos, channel): channel for channel in channels}
        
        # 处理完成的任务
        for future in as_completed(future_to_channel):
            channel = future_to_channel[future]
            try:
                videos = future.result()
                if videos:
                    all_videos.extend(videos)
                    print(f"已完成频道 {channel} 的视频获取")
                else:
                    print(f"无法获取频道 {channel} 的视频")
            except Exception as e:
                print(f"处理频道 {channel} 时发生错误: {str(e)}")
    
    if all_videos:
        generate_html(all_videos)
        save_videos_to_json(all_videos)
        print(f"\n共获取到 {len(all_videos)} 个视频的信息")
    else:
        print("\n未找到任何视频。")

if __name__ == "__main__":
    main()
