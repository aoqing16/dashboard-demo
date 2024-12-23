#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
from datetime import datetime
import requests
from dotenv import load_dotenv

class TwitterScraper:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://api.twitter.com/2"
        self.bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        
    def get_user_id(self, username):
        """获取用户ID"""
        url = f"{self.base_url}/users/by/username/{username}"
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "User-Agent": "v2UserLookupPython"
        }
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()['data']['id']
            else:
                self.logger.error(f"获取用户ID失败: {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"获取用户ID时出错: {str(e)}")
            return None
            
    def get_user_tweets(self, user_id, max_results=10):
        """获取用户的推文"""
        url = f"{self.base_url}/users/{user_id}/tweets"
        params = {
            "max_results": max_results,
            "tweet.fields": "created_at,public_metrics,entities,attachments",
            "expansions": "attachments.media_keys",
            "media.fields": "url,preview_image_url"
        }
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "User-Agent": "v2TweetLookupPython"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"获取推文失败: {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"获取推文时出错: {str(e)}")
            return None
            
    def process_tweets(self, tweets_data):
        """处理推文数据"""
        if not tweets_data or 'data' not in tweets_data:
            return []
            
        processed_tweets = []
        media_lookup = {}
        
        # 创建媒体查找表
        if 'includes' in tweets_data and 'media' in tweets_data['includes']:
            for media in tweets_data['includes']['media']:
                media_lookup[media['media_key']] = media.get('url') or media.get('preview_image_url')
        
        for tweet in tweets_data['data']:
            try:
                # 获取媒体URL
                media_urls = []
                if 'attachments' in tweet and 'media_keys' in tweet['attachments']:
                    for media_key in tweet['attachments']['media_keys']:
                        if media_key in media_lookup:
                            media_urls.append(media_lookup[media_key])
                
                # 获取链接
                urls = []
                if 'entities' in tweet and 'urls' in tweet['entities']:
                    urls = [url['expanded_url'] for url in tweet['entities']['urls']]
                
                processed_tweet = {
                    'text': tweet['text'],
                    'created_at': tweet['created_at'],
                    'tweet_id': tweet['id'],
                    'likes': tweet['public_metrics']['like_count'],
                    'retweets': tweet['public_metrics']['retweet_count'],
                    'replies': tweet['public_metrics']['reply_count'],
                    'quotes': tweet['public_metrics']['quote_count'],
                    'media_urls': media_urls,
                    'urls': urls,
                    'platform': 'Twitter',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                processed_tweets.append(processed_tweet)
                
            except Exception as e:
                self.logger.error(f"处理推文时出错: {str(e)}")
                continue
                
        return processed_tweets
            
    def save_tweets_to_json(self, tweets, output_file='twitter_posts.json'):
        """保存推文信息到JSON文件"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(tweets, f, ensure_ascii=False, indent=2)
            self.logger.info(f"已保存推文信息到 {output_file}")
        except Exception as e:
            self.logger.error(f"保存JSON文件时出错: {str(e)}")
            
    def generate_html(self, tweets, output_file='twitter_posts.html'):
        """生成推文列表的HTML内容"""
        try:
            html_content = '\n'.join([
                '''
                <div class="tweet-card">
                    <div class="tweet-info">
                        <span class="platform-tag platform-twitter">Twitter</span>
                        <p class="tweet-text">{text}</p>
                        <div class="tweet-media">
                            {media_html}
                        </div>
                        <div class="tweet-meta">
                            <span>❤️ {likes}</span>
                            <span>🔄 {retweets}</span>
                            <span>💬 {replies}</span>
                            <span>📝 {quotes}</span>
                        </div>
                        <p class="tweet-time">发布时间: {created_at}</p>
                        <div class="tweet-links">
                            {links_html}
                        </div>
                    </div>
                </div>
                '''.format(
                    text=tweet['text'],
                    likes=tweet['likes'],
                    retweets=tweet['retweets'],
                    replies=tweet['replies'],
                    quotes=tweet['quotes'],
                    created_at=tweet['created_at'],
                    media_html='\n'.join([f'<img src="{url}" alt="Media">' for url in tweet['media_urls']]),
                    links_html='\n'.join([f'<a href="{url}" target="_blank">{url}</a>' for url in tweet['urls']])
                ) for tweet in tweets
            ])
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            self.logger.info(f"已生成HTML内容: {output_file}")
            
        except Exception as e:
            self.logger.error(f"生成HTML内容时出错: {str(e)}")
            
    def run_scraper(self):
        """运行爬虫"""
        try:
            # 加载环境变量
            load_dotenv()
            
            if not self.bearer_token:
                print("错误：未在.env文件中找到TWITTER_BEARER_TOKEN配置")
                return
            
            # 获取用户ID
            username = "op7418"
            user_id = self.get_user_id(username)
            
            if not user_id:
                print(f"未能获取到用户 {username} 的ID")
                return
            
            # 获取用户推文
            print(f"\n开始获取用户 {username} 的推文")
            tweets_data = self.get_user_tweets(user_id)
            
            if tweets_data:
                # 处理推文数据
                processed_tweets = self.process_tweets(tweets_data)
                
                if processed_tweets:
                    # 保存推文信息
                    self.save_tweets_to_json(processed_tweets)
                    self.generate_html(processed_tweets)
                    print(f"\n总计获取到 {len(processed_tweets)} 条推文")
                else:
                    print("\n未能获取到任何推文信息")
            else:
                print(f"\n未能获取到用户 {username} 的推文")
            
        except Exception as e:
            self.logger.error(f"运行爬虫时出错: {str(e)}")
            raise

def main():
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('twitter_scraper.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    scraper = TwitterScraper()
    scraper.run_scraper()

if __name__ == "__main__":
    main()
