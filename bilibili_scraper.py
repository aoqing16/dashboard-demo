import requests
import os
import json
import webbrowser
from datetime import datetime
import re
import time
import random

def get_user_latest_video(uid):
    """
    获取B站用户最新视频信息
    参数:
        uid: B站用户ID
    """
    max_retries = 3  # 最大重试次数
    base_wait = 30   # 基础等待时间（秒）
    
    for retry in range(max_retries + 1):
        try:
            print(f"\n正在获取用户 {uid} 的最新视频...")
            if retry > 0:
                wait_time = base_wait * retry  # 递增等待时间
                print(f"\n第 {retry} 次重试，等待 {wait_time} 秒...")
                time.sleep(wait_time)
            
            print("正在发送请求...")
            # 使用简化的API
            api_url = f"https://api.bilibili.com/x/space/arc/search?mid={uid}&ps=1&pn=1"
            
            # 随机生成一些常见的User-Agent
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edge/120.0.0.0',
            ]
            
            headers = {
                'User-Agent': random.choice(user_agents),
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Origin': 'https://space.bilibili.com',
                'Referer': f'https://space.bilibili.com/{uid}/video',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
            }

            session = requests.Session()
            
            # 获取视频列表
            print("正在发送请求...")
            response = session.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            print("正在解析响应...")
            data = response.json()
            code = data.get('code', -1)
            message = data.get('message', '')
            
            print(f"API响应状态码: {code}")
            print(f"API响应消息: {message}")
            
            if code == 0:
                # 解析视频信息
                if 'data' not in data or 'list' not in data['data'] or 'vlist' not in data['data']['list']:
                    print("响应数据结构不完整")
                    print(f"完整响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
                    return None

                vlist = data['data']['list']['vlist']
                if not vlist:
                    print(f"用户 {uid} 没有发布任何视频")
                    return None

                # 获取最新视频信息
                video = vlist[0]
                video_info = {
                    'title': video['title'],
                    'author': video['author'],
                    'url': f"https://www.bilibili.com/video/{video['bvid']}",
                    'thumbnail': video.get('pic', '').replace('http:', 'https:'),
                    'description': video.get('description', ''),
                    'time': datetime.fromtimestamp(video['created']).strftime('%Y-%m-%d %H:%M:%S')
                }

                print(f"成功获取视频信息: {video_info['title']}")
                return video_info
            elif code == -799:  # 请求过于频繁
                print(f"获取视频列表失败: {message}")
                if retry < max_retries:
                    print("遇到频率限制，正在重试...")
                    continue
                else:
                    print("达到最大重试次数，跳过该用户")
                    return None
            else:
                print(f"获取视频列表失败: {message}")
                return None
                
        except requests.RequestException as e:
            print(f"网络请求失败: {str(e)}")
            if 'response' in locals():
                print(f"响应状态码: {response.status_code}")
                print(f"响应头: {dict(response.headers)}")
                print(f"响应内容: {response.text}")
            if retry < max_retries:
                print("发生错误，正在重试...")
                continue
            else:
                print("达到最大重试次数，跳过该用户")
                return None
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {str(e)}")
            if 'response' in locals():
                print(f"原始响应: {response.text}")
            if retry < max_retries:
                print("发生错误，正在重试...")
                continue
            else:
                print("达到最大重试次数，跳过该用户")
                return None
        except Exception as e:
            print(f"发生未知错误: {str(e)}")
            import traceback
            print(f"错误堆栈: {traceback.format_exc()}")
            if retry < max_retries:
                print("发生错误，正在重试...")
                continue
            else:
                print("达到最大重试次数，跳过该用户")
                return None

def generate_html(videos):
    """
    生成展示视频信息的HTML页面
    """
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Latest Videos</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f9f9f9;
            }
            .video-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 20px;
                padding: 20px 0;
            }
            .video-card {
                background: white;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }
            .video-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 5px 20px rgba(0,0,0,0.15);
            }
            .thumbnail-container {
                position: relative;
                width: 100%;
                padding-top: 56.25%;
                background-color: #f0f0f0;
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
                margin: 0;
                font-size: 16px;
                font-weight: 600;
                line-height: 1.4;
                margin-bottom: 8px;
                color: #000;
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
                overflow: hidden;
            }
            .video-author {
                color: #606060;
                font-size: 14px;
                margin-bottom: 8px;
            }
            .video-description {
                color: #606060;
                font-size: 13px;
                line-height: 1.4;
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
                overflow: hidden;
            }
            .video-time {
                color: #606060;
                font-size: 13px;
                margin-bottom: 8px;
            }
            a {
                text-decoration: none;
                color: inherit;
            }
            .header {
                text-align: center;
                margin-bottom: 30px;
                color: #030303;
            }
            .header h1 {
                font-size: 24px;
                font-weight: 600;
            }
            .timestamp {
                text-align: center;
                color: #606060;
                font-size: 14px;
                margin-top: 30px;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Latest Videos</h1>
        </div>
        <div class="video-grid">
    """
    
    for video in videos:
        html_template += f"""
            <div class="video-card">
                <a href="{video['url']}" target="_blank">
                    <div class="thumbnail-container">
                        <img class="thumbnail" src="{video['thumbnail']}" alt="{video['title']}">
                    </div>
                    <div class="video-info">
                        <h3 class="video-title">{video['title']}</h3>
                        <div class="video-author">{video['author']}</div>
                        <div class="video-time">{video.get('time', '')}</div>
                        <div class="video-description">{video.get('description', '')}</div>
                    </div>
                </a>
            </div>
        """
    
    html_template += f"""
        </div>
        <div class="timestamp">
            Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </body>
    </html>
    """
    
    # 保存HTML文件
    html_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bilibili_videos.html')
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    return html_file

def save_videos_to_json(videos):
    """保存视频信息到JSON文件"""
    output_file = os.path.join(os.path.dirname(__file__), 'bilibili_videos.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)
    print(f"\n视频信息已保存到: {output_file}")

def main():
    # B站用户ID列表
    users = [
        '5758057',     # 用户ID
    ]
    
    all_videos = []
    for uid in users:
        video = get_user_latest_video(uid)
        if video:
            all_videos.append(video)
    
    if all_videos:
        html_file = generate_html(all_videos)
        save_videos_to_json(all_videos)
        print(f"\n共获取到 {len(all_videos)} 个视频的信息")
    else:
        print("\n未找到任何视频。")

if __name__ == '__main__':
    main()
