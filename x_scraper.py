import os
import json
import time
import random
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import feedparser
import re

class XScraper:
    def __init__(self):
        self.session = self._create_session()
        
    def _create_session(self):
        """创建一个带有请求头的会话"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/rss+xml,application/xml',
        })
        return session
    
    def get_user_latest_tweet(self, username):
        """获取用户最新推文"""
        # 使用Nitter作为替代前端
        nitter_instances = [
            'https://nitter.net',
            'https://nitter.cz',
            'https://nitter.ca',
            'https://nitter.it',
            'https://nitter.nl',
            'https://nitter.hu',
            'https://nitter.moomoo.me',
            'https://nitter.privacydev.net',
            'https://nitter.poast.org',
            'https://nitter.unixfox.eu',
            'https://nitter.foss.wtf',
            'https://nitter.priv.pw',
            'https://nitter.tokhmi.xyz',
            'https://nitter.projectsegfau.lt',
            'https://nitter.cutelab.space'
        ]
        
        # 随机打乱实例顺序
        random.shuffle(nitter_instances)
        
        for base_url in nitter_instances:
            try:
                print(f"正在尝试使用 {base_url} 获取用户 @{username} 的推文...")
                
                url = f"{base_url}/{username}"
                
                # 添加随机延迟
                delay = random.uniform(1, 2)  # 减少延迟时间
                print(f"等待 {delay:.1f} 秒...")
                time.sleep(delay)
                
                print("正在发送请求...")
                response = self.session.get(url, timeout=5)  # 减少超时时间
                response.raise_for_status()
                
                print("正在解析页面...")
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 获取第一条推文
                tweet_container = soup.find('div', class_='timeline-item')
                if not tweet_container:
                    print(f"未找到用户 {username} 的推文，尝试下一个实例...")
                    continue
                
                # 获取推文内容
                tweet_content = tweet_container.find('div', class_='tweet-content')
                tweet_text = tweet_content.get_text(strip=True) if tweet_content else ''
                
                # 获取推文时间
                time_element = tweet_container.find('span', class_='tweet-date')
                tweet_time = None
                if time_element and time_element.find('a'):
                    time_str = time_element.find('a').get('title', '')
                    try:
                        tweet_time = datetime.strptime(time_str, '%b %d, %Y · %I:%M %p UTC')
                    except:
                        print(f"无法解析时间: {time_str}")
                
                # 获取推文图片
                tweet_image = None
                image_container = tweet_container.find('div', class_='attachment')
                if image_container:
                    img = image_container.find('img')
                    if img and 'src' in img.attrs:
                        tweet_image = img['src']
                        if not tweet_image.startswith('http'):
                            tweet_image = base_url + tweet_image
                
                # 获取推文统计数据
                stats = {}
                stat_container = tweet_container.find('div', class_='tweet-stats')
                if stat_container:
                    for stat in stat_container.find_all('span', class_='tweet-stat'):
                        value = stat.find('span', class_='tweet-stat-count')
                        icon = stat.find('span', class_='icon-')
                        if value and icon:
                            stat_type = icon['class'][0].replace('icon-', '')
                            stats[stat_type] = value.get_text(strip=True)
                
                # 获取推文链接和ID
                tweet_link = tweet_container.find('a', class_='tweet-link')
                tweet_id = tweet_link['href'].split('/')[-1] if tweet_link else None
                
                tweet_info = {
                    'title': tweet_text[:100] + ('...' if len(tweet_text) > 100 else ''),
                    'author': username,
                    'url': f"https://twitter.com/{username}/status/{tweet_id}" if tweet_id else f"https://twitter.com/{username}",
                    'thumbnail': tweet_image,
                    'description': tweet_text,
                    'time': tweet_time,
                    'metrics': {
                        'replies': stats.get('reply', '0'),
                        'retweets': stats.get('retweet', '0'),
                        'likes': stats.get('heart', '0'),
                    }
                }
                
                print(f"成功获取推文: {tweet_info['title']}")
                if tweet_time:
                    print(f"推文时间: {tweet_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                return tweet_info
                
            except requests.RequestException as e:
                print(f"请求失败 ({base_url}): {str(e)}")
                continue
            except Exception as e:
                print(f"处理失败 ({base_url}): {str(e)}")
                continue
        
        print("所有实例都尝试失败")
        return None

def generate_html(tweets):
    """生成展示推文信息的HTML页面"""
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Latest Tweets</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f9f9f9;
            }
            .tweet-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 20px;
                padding: 20px 0;
            }
            .tweet-card {
                background: white;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }
            .tweet-card:hover {
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
            .tweet-info {
                padding: 15px;
            }
            .tweet-title {
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
            .tweet-author {
                color: #606060;
                font-size: 14px;
                margin-bottom: 8px;
            }
            .tweet-metrics {
                color: #606060;
                font-size: 13px;
                display: flex;
                gap: 15px;
            }
            .metric {
                display: flex;
                align-items: center;
                gap: 4px;
            }
            .tweet-description {
                color: #606060;
                font-size: 13px;
                line-height: 1.4;
                margin-top: 8px;
                display: -webkit-box;
                -webkit-line-clamp: 3;
                -webkit-box-orient: vertical;
                overflow: hidden;
            }
            .tweet-time {
                color: #606060;
                font-size: 13px;
                margin-top: 8px;
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
            <h1>Latest Tweets</h1>
        </div>
        <div class="tweet-grid">
    """
    
    for tweet in tweets:
        metrics = tweet.get('metrics', {})
        html_template += f"""
            <div class="tweet-card">
                <a href="{tweet['url']}" target="_blank">
                    {f'''<div class="thumbnail-container">
                        <img class="thumbnail" src="{tweet['thumbnail']}" alt="Tweet media">
                    </div>''' if tweet.get('thumbnail') else ''}
                    <div class="tweet-info">
                        <h3 class="tweet-title">{tweet['title']}</h3>
                        <div class="tweet-author">@{tweet['author']}</div>
                        <div class="tweet-metrics">
                            <div class="metric">
                                <span>💬</span>
                                <span>{metrics.get('replies', '0')}</span>
                            </div>
                            <div class="metric">
                                <span>🔄</span>
                                <span>{metrics.get('retweets', '0')}</span>
                            </div>
                            <div class="metric">
                                <span>❤️</span>
                                <span>{metrics.get('likes', '0')}</span>
                            </div>
                        </div>
                        <div class="tweet-description">{tweet['description']}</div>
                        <div class="tweet-time">{tweet['time'].strftime('%Y-%m-%d %H:%M:%S UTC')} UTC</div>
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
    html_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'x_tweets.html')
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    return html_file

def save_tweets(tweets):
    """保存推文到JSON文件"""
    # 将datetime对象转换为字符串
    serializable_tweets = []
    for tweet in tweets:
        tweet_copy = tweet.copy()
        if 'time' in tweet_copy:
            tweet_copy['time'] = tweet_copy['time'].strftime('%Y-%m-%d %H:%M:%S')
        serializable_tweets.append(tweet_copy)
    
    output_file = os.path.join(os.path.dirname(__file__), 'tweets.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(serializable_tweets, f, ensure_ascii=False, indent=2)
    print(f"\n推文已保存到: {output_file}")

def main():
    # 创建X爬虫实例
    scraper = XScraper()
    
    # X用户名列表
    usernames = [
        'dotey',  # 宝玉
    ]
    
    all_tweets = []
    for username in usernames:
        tweet = scraper.get_user_latest_tweet(username)
        if tweet:
            all_tweets.append(tweet)
    
    if all_tweets:
        html_file = generate_html(all_tweets)
        save_tweets(all_tweets)
        print(f"\n共获取到 {len(all_tweets)} 条推文")
    else:
        print("\n未找到任何推文。")

if __name__ == '__main__':
    main()
