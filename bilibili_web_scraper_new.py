#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import requests
from datetime import datetime
import time
import random
import logging
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import subprocess
import shutil
import schedule

# 设置默认编码为UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

class BilibiliWebScraper:
    def __init__(self):
        self.setup_logging()
        self.cache_file = 'bilibili_cache.json'
        
        # 设置请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1',
            'Origin': 'https://space.bilibili.com',
            'Referer': 'https://space.bilibili.com'
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
        self.logger = logging.getLogger(__name__)

    def get_user_latest_video(self, user_id):
        """获取用户的最新视频"""
        max_retries = 3
        retry_delay = 5  # 秒
        
        for retry in range(max_retries):
            try:
                # 使用API获取用户视频列表
                api_url = f'https://api.bilibili.com/x/space/arc/search'
                params = {
                    'mid': user_id,
                    'ps': 1,  # 只获取最新的1个视频
                    'tid': 0,
                    'pn': 1,
                    'keyword': '',
                    'order': 'pubdate',  # 按发布时间排序
                }
                
                self.logger.info(f"正在获取用户 {user_id} 的视频列表... (尝试 {retry + 1}/{max_retries})")
                response = requests.get(api_url, params=params, headers=self.headers)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data['code'] == 0 and data['data']['list']['vlist']:
                            video = data['data']['list']['vlist'][0]
                            
                            video_info = {
                                'title': video['title'],
                                'url': f"https://www.bilibili.com/video/{video['bvid']}",
                                'platform': 'bilibili',
                                'author': video['author'],
                                'user_id': user_id,
                                'bvid': video['bvid'],
                                'aid': str(video['aid']),
                                'description': video.get('description', ''),
                                'created': datetime.fromtimestamp(video['created']).strftime('%Y-%m-%d %H:%M:%S'),
                                'length': video.get('length', ''),
                                'play': video.get('play', 0),
                                'comment': video.get('comment', 0),
                                'thumbnail': video.get('pic', ''),
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            }
                            
                            self.logger.info(f"成功获取视频: {video_info['title']}")
                            return video_info
                        else:
                            error_msg = data.get('message', '未知错误')
                            if '请求过于频繁' in error_msg:
                                self.logger.warning(f"API请求频率限制，等待 {retry_delay} 秒后重试...")
                                time.sleep(retry_delay)
                                continue
                            else:
                                self.logger.error(f"API返回错误: {error_msg}")
                    except Exception as e:
                        self.logger.error(f"解析API响应时出错: {str(e)}")
                else:
                    self.logger.error(f"API请求失败，状态码: {response.status_code}")
                
                # 如果是最后一次重试，等待时间加倍
                if retry < max_retries - 1:
                    self.logger.info(f"等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                    
            except Exception as e:
                self.logger.error(f"获取用户 {user_id} 的视频时出错: {str(e)}")
                if retry < max_retries - 1:
                    self.logger.info(f"等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
        
        self.logger.warning(f"未找到用户 {user_id} 的视频数据")
        return None

    def save_videos_to_json(self, videos, filename='bilibili_videos.json'):
        """保存视频信息到JSON文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(videos, f, ensure_ascii=False, indent=2)
            self.logger.info(f"已保存视频信息到 {filename}")
        except Exception as e:
            self.logger.error(f"保存JSON文件时出错: {str(e)}")

    def load_video_cache(self):
        """加载视频缓存"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.error(f"加载缓存失败: {str(e)}")
            return {}

    def save_video_cache(self, cache):
        """保存视频缓存"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存缓存失败: {str(e)}")

    def has_new_videos(self, videos):
        """检查是否有新视频"""
        cache = self.load_video_cache()
        has_new = False
        
        for video in videos:
            user_id = video['user_id']
            bvid = video['bvid']
            if str(user_id) not in cache or cache[str(user_id)]['bvid'] != bvid:
                has_new = True
                cache[str(user_id)] = video
        
        self.save_video_cache(cache)
        return has_new

    def update_dashboard(self, video_info):
        """更新仪表板数据"""
        try:
            # 确保data目录存在
            data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
            os.makedirs(data_dir, exist_ok=True)
            
            # 准备仪表板数据
            dashboard_data = {
                'title': video_info['title'],
                'platform': video_info['platform'],
                'views': video_info['play'],
                'comments': video_info['comment'],
                'url': video_info['url'],
                'published': video_info['created'],
                'thumbnail': video_info['thumbnail'],
                'author': video_info['author'],
                'platform_id': video_info['bvid'],
                'updated_at': video_info['timestamp']
            }
            
            # 保存到data/bilibili_latest.json
            output_file = os.path.join(data_dir, 'bilibili_latest.json')
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(dashboard_data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"仪表板数据已更新: {output_file}")
            
            # 上传到GitHub Pages
            try:
                repo_url = "https://github.com/aoqing16/dashboard-demo.git"
                repo_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dashboard-demo')
                
                # 如果目录不存在，克隆仓库
                if not os.path.exists(repo_dir):
                    subprocess.run(['git', 'clone', repo_url, repo_dir], check=True)
                
                # 配置Git用户信息
                subprocess.run(['git', '-C', repo_dir, 'config', 'user.name', 'BilibiliScraper'], check=True)
                subprocess.run(['git', '-C', repo_dir, 'config', 'user.email', 'scraper@example.com'], check=True)
                
                # 复制数据文件到仓库
                data_dir_in_repo = os.path.join(repo_dir, 'data')
                os.makedirs(data_dir_in_repo, exist_ok=True)
                shutil.copy2(output_file, os.path.join(data_dir_in_repo, 'bilibili_latest.json'))
                
                # 提交并推送更改
                subprocess.run(['git', '-C', repo_dir, 'add', '.'], check=True)
                try:
                    subprocess.run(['git', '-C', repo_dir, 'commit', '-m', f'Update bilibili data: {video_info["title"]}'], check=True)
                except subprocess.CalledProcessError as e:
                    # 如果没有更改需要提交，继续执行
                    if 'nothing to commit' in str(e.output):
                        self.logger.info("没有新的更改需要提交")
                        return
                    raise
                
                subprocess.run(['git', '-C', repo_dir, 'push'], check=True)
                
                self.logger.info("数据已成功上传到GitHub Pages")
            except Exception as e:
                self.logger.error(f"上传到GitHub Pages失败: {str(e)}")
                
        except Exception as e:
            self.logger.error(f"更新仪表板时出错: {str(e)}")

    def run_scraper(self):
        """运行爬虫"""
        try:
            # B站用户ID列表
            user_ids = [
                14739873,   # 老师好我叫何同学
                520819684,  # 小Lin说
                482619845,  # 小Lin说游戏
                471000665,  # 小Lin说科技
                472599499,  # 小Lin说财经
                49574614    # 小Lin说电影
            ]
            
            print(f"\n开始获取用户最新视频...")
            all_videos = []
            
            for user_id in user_ids:
                video_info = self.get_user_latest_video(str(user_id))
                if video_info:
                    all_videos.append(video_info)
                    print(f"成功获取到视频: {video_info['title']}")
                else:
                    print(f"未能获取到用户 {user_id} 的视频信息")
                
                # 添加随机延迟，避免请求过快
                time.sleep(random.uniform(3, 5))
            
            if all_videos:
                # 保存所有视频信息到JSON
                self.save_videos_to_json(all_videos)
                
                # 更新仪表板（使用最新的视频）
                latest_video = max(all_videos, key=lambda x: x['created'])
                self.update_dashboard(latest_video)
                
                print(f"\n总计获取到 {len(all_videos)} 个用户的最新视频")
            else:
                print("\n未能获取到任何视频信息")
                
        except Exception as e:
            self.logger.error(f"运行爬虫时出错: {str(e)}")
            raise

def main():
    try:
        # 创建日志目录
        log_dir = os.path.dirname(os.path.abspath(__file__))
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # 设置启动日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(os.path.join(log_dir, 'bilibili_scraper.log'), encoding='utf-8')
            ]
        )
        logger = logging.getLogger(__name__)
        
        # 记录启动信息
        logger.info("="*50)
        logger.info("B站爬虫启动")
        logger.info(f"当前工作目录: {os.getcwd()}")
        logger.info(f"脚本位置: {os.path.abspath(__file__)}")
        
        # 设置每天早上8点运行
        schedule.every().day.at("08:00").do(BilibiliWebScraper().run_scraper)
        
        logger.info("定时任务已设置：每天早上8点运行")
        logger.info("开始执行第一次抓取...")
        
        # 立即运行一次
        BilibiliWebScraper().run_scraper()
        
        logger.info("进入定时任务循环...")
        # 保持程序运行
        while True:
            schedule.run_pending()
            time.sleep(60)
            
    except Exception as e:
        logger.error(f"程序出错: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
