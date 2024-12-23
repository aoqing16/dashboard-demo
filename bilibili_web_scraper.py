#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import locale
import requests
from bs4 import BeautifulSoup
import json
import logging
from datetime import datetime
import time
import random
from typing import List, Dict, Any

# 设置默认编码为UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

class BilibiliWebScraper:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        
        # 从配置文件加载Cookie
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                bilibili_config = config['bilibili']
                self.cookies = {
                    'SESSDATA': bilibili_config['sessdata'],
                    'bili_jct': bilibili_config['bili_jct'],
                    'buvid3': bilibili_config['buvid3']
                }
                self.logger.info("成功加载B站Cookie")
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {str(e)}")
            self.cookies = None
            
        # 设置请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.bilibili.com/'
        }

    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('bilibili_scraper.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )

    def get_latest_video(self, user_id: int) -> Dict[str, Any]:
        """获取用户的最新视频
        
        Args:
            user_id: B站用户ID
            
        Returns:
            包含视频信息的字典
        """
        try:
            # 使用移动端API获取视频信息
            api_url = f'https://api.bilibili.com/x/space/arc/search'  # 修改API端点
            params = {
                'mid': user_id,
                'ps': 1,
                'pn': 1,
                'order': 'pubdate',
                'jsonp': 'jsonp'
            }
            
            mobile_headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Origin': 'https://m.bilibili.com',
                'Referer': f'https://m.bilibili.com/space/{user_id}'
            }
            
            self.logger.info("正在获取最新视频信息...")
            time.sleep(random.uniform(5, 8))
            
            response = requests.get(
                api_url,
                params=params,
                headers=mobile_headers,
                cookies=self.cookies
            )
            response.raise_for_status()
            
            data = response.json()
            self.logger.info(f"API响应: {data}")
            
            if data['code'] == -799:  # 请求频率限制
                self.logger.warning("触发请求频率限制，等待更长时间后重试...")
                time.sleep(random.uniform(10, 15))
                
                response = requests.get(
                    api_url,
                    params=params,
                    headers=mobile_headers,
                    cookies=self.cookies
                )
                response.raise_for_status()
                data = response.json()
                self.logger.info(f"重试后API响应: {data}")
            
            if data['code'] == 0 and 'data' in data and 'list' in data['data'] and 'vlist' in data['data']['list'] and data['data']['list']['vlist']:
                video = data['data']['list']['vlist'][0]
                
                time.sleep(random.uniform(3, 5))
                
                # 获取用户信息
                user_info_api = f'https://api.bilibili.com/x/space/acc/info'  # 修改API端点
                user_params = {
                    'mid': user_id,
                    'jsonp': 'jsonp'
                }
                
                user_response = requests.get(
                    user_info_api,
                    params=user_params,
                    headers=mobile_headers,
                    cookies=self.cookies
                )
                user_response.raise_for_status()
                user_data = user_response.json()
                
                username = user_data['data']['name'] if user_data['code'] == 0 and 'data' in user_data and 'name' in user_data['data'] else str(user_id)
                
                video_info = {
                    'title': video['title'],
                    'bvid': video['bvid'],
                    'aid': video['aid'],
                    'description': video['description'],
                    'created': datetime.fromtimestamp(video['created']).strftime('%Y-%m-%d %H:%M:%S'),
                    'length': video['length'],
                    'play': video['play'],
                    'comment': video.get('comment', 0),
                    'pic': video['pic'],
                    'author': username,
                    'mid': user_id,
                    'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                self.logger.info(f"成功获取视频: {video_info['title']}")
                return video_info
            else:
                self.logger.warning(f"未找到用户 {user_id} 的视频")
                return None
            
        except Exception as e:
            self.logger.error(f"获取用户 {user_id} 的视频时出错: {str(e)}")
            return None

    def save_videos_to_json(self, videos: List[Dict[str, Any]], output_file: str = 'bilibili_videos.json') -> None:
        """保存视频信息到JSON文件"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(videos, f, ensure_ascii=False, indent=2)
            self.logger.info(f"已保存视频信息到 {output_file}")
        except Exception as e:
            self.logger.error(f"保存JSON文件时出错: {str(e)}")

    def run_scraper(self) -> None:
        """运行爬虫"""
        # B站用户ID列表
        user_ids = [
            5758057  # 用户ID
        ]
        
        print(f"\n开始获取用户最新视频...")
        all_videos = []
        
        for user_id in user_ids:
            video = self.get_latest_video(user_id)
            if video:
                all_videos.append(video)
                time.sleep(random.uniform(3, 5))  # 添加延迟
        
        if all_videos:
            self.save_videos_to_json(all_videos)
            print(f"\n总计获取到 {len(all_videos)} 个视频")
            
            # 打印每个视频的基本信息
            for video in all_videos:
                print(f"\n作者: {video['author']}")
                print(f"标题: {video['title']}")
                print(f"播放量: {video['play']}")
                print(f"发布时间: {video['created']}")
                print(f"BV号: {video['bvid']}")
        else:
            print("\n未能获取到任何视频信息")

if __name__ == "__main__":
    scraper = BilibiliWebScraper()
    scraper.run_scraper()
