#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import random
import asyncio
import logging
from datetime import datetime
from playwright.async_api import async_playwright
from dotenv import load_dotenv

class XiaohongshuScraper:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    async def setup_browser(self):
        """设置浏览器"""
        self.playwright = await async_playwright().start()
        
        # 添加更多浏览器配置来绕过反爬
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials',
                '--disable-web-security',
                '--disable-features=BlockInsecurePrivateNetworkRequests',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
                '--window-size=1920,1080'
            ]
        )
        
        # 添加更多上下文配置
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Connection': 'keep-alive',
                'Cache-Control': 'max-age=0',
                'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-User': '?1',
                'Sec-Fetch-Dest': 'document'
            }
        )
        
        # 修改 navigator.webdriver
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'platform', {
                get: () => 'Win32'
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)
        
        self.page = await self.context.new_page()
        
        # 设置更长的超时时间
        self.page.set_default_timeout(60000)
        
    async def get_user_videos(self, user_url):
        """获取用户的视频信息"""
        videos = []
        try:
            # 添加随机延迟
            await asyncio.sleep(random.uniform(2, 5))
            
            # 访问页面并等待加载
            await self.page.goto(user_url, wait_until='networkidle')
            await asyncio.sleep(random.uniform(3, 6))
            
            # 获取用户名
            username = "未知用户"
            try:
                username_element = await self.page.wait_for_selector('.user-name')
                username = await username_element.text_content()
            except Exception:
                self.logger.warning("无法获取用户名")
            
            # 多次滚动页面以加载更多内容
            for _ in range(3):
                await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await asyncio.sleep(random.uniform(1, 2))
            
            # 获取视频列表
            note_items = await self.page.query_selector_all('.note-item')
            
            if not note_items:
                self.logger.warning("未找到视频列表，尝试其他选择器")
                # 尝试其他可能的选择器
                note_items = await self.page.query_selector_all('[data-v-6e5b4cc1]')
            
            # 只检查前5个视频，找到第一个非置顶的就返回
            for element in note_items[:5]:
                try:
                    # 检查是否是置顶视频
                    pin_element = await element.query_selector('.pin, .sticky, [class*="pin"], [class*="sticky"]')
                    if pin_element:
                        self.logger.info("跳过置顶视频")
                        continue
                    
                    # 找到第一个非置顶视频，获取信息并返回
                    title = await element.wait_for_selector('.note-title, .title, h3')
                    title_text = await title.text_content()
                    
                    link = await element.wait_for_selector('a[href*="/explore/"]')
                    link_url = await link.get_attribute('href')
                    if not link_url.startswith('http'):
                        link_url = f"https://www.xiaohongshu.com{link_url}"
                    
                    # 获取缩略图
                    thumbnail = ""
                    try:
                        img = await element.wait_for_selector('img')
                        thumbnail = await img.get_attribute('src')
                    except Exception:
                        self.logger.warning(f"无法获取视频 {title_text} 的缩略图")
                    
                    # 获取发布时间
                    publish_time = "未知时间"
                    try:
                        time_element = await element.wait_for_selector('.note-time, .time')
                        publish_time = await time_element.text_content()
                    except Exception:
                        self.logger.warning(f"无法获取视频 {title_text} 的发布时间")
                    
                    video = {
                        'title': title_text,
                        'url': link_url,
                        'thumbnail': thumbnail,
                        'platform': '小红书',
                        'author': username,
                        'publish_time': publish_time,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    videos.append(video)
                    self.logger.info(f"获取到最新非置顶视频: {title_text}")
                    return videos
                    
                except Exception as e:
                    self.logger.error(f"解析视频元素时出错: {str(e)}")
                    continue
            
        except Exception as e:
            self.logger.error(f"获取用户视频时出错: {str(e)}")
        
        return videos
            
    def save_videos_to_json(self, videos, output_file='xiaohongshu_videos.json'):
        """保存视频信息到JSON文件"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(videos, f, ensure_ascii=False, indent=2)
            self.logger.info(f"已保存视频信息到 {output_file}")
        except Exception as e:
            self.logger.error(f"保存JSON文件时出错: {str(e)}")
            
    def generate_html(self, videos, output_file='xiaohongshu_videos.html'):
        """生成视频列表的HTML内容"""
        try:
            html_content = '\n'.join([
                '''
                <div class="video-card">
                    <div class="thumbnail">
                        <a href="{url}" target="_blank">
                            <img src="{thumbnail}" alt="{title}" onerror="this.src='https://via.placeholder.com/300x200?text=No+Image'">
                        </a>
                    </div>
                    <div class="video-info">
                        <span class="platform-tag platform-xiaohongshu">小红书</span>
                        <h3>{title}</h3>
                        <p>作者: {author}</p>
                        <p>发布时间: {publish_time}</p>
                    </div>
                </div>
                '''.format(**video) for video in videos
            ])
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            self.logger.info(f"已生成HTML内容: {output_file}")
            
        except Exception as e:
            self.logger.error(f"生成HTML内容时出错: {str(e)}")
            
    async def run_scraper(self):
        """运行爬虫"""
        try:
            # 加载环境变量
            load_dotenv()
            
            # 获取小红书用户列表
            users = os.getenv('XIAOHONGSHU_USERS', '').split(',')
            if not users or users[0] == '':
                print("错误：未在.env文件中找到XIAOHONGSHU_USERS配置")
                return
            
            # 初始化浏览器
            await self.setup_browser()
            
            # 存储所有用户的视频
            all_videos = []
            
            # 遍历每个用户
            for user in users:
                user = user.strip()
                if not user:
                    continue
                
                print(f"\n开始获取用户页面: {user}")
                videos = await self.get_user_videos(user)
                if videos:
                    all_videos.extend(videos)
                    print(f"成功获取到 {len(videos)} 个视频")
                else:
                    print(f"未能获取到用户视频信息")
                
                # 在用户之间添加随机延迟
                await asyncio.sleep(random.uniform(3, 6))
            
            if all_videos:
                # 保存视频信息
                self.save_videos_to_json(all_videos)
                self.generate_html(all_videos)
                print(f"\n总计获取到 {len(all_videos)} 个视频")
            else:
                print("\n未能获取到任何视频信息")
            
        except Exception as e:
            self.logger.error(f"运行爬虫时出错: {str(e)}")
            raise
        finally:
            # 关闭浏览器
            if hasattr(self, 'browser'):
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()

async def main():
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('xiaohongshu_scraper.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    scraper = XiaohongshuScraper()
    await scraper.run_scraper()

if __name__ == "__main__":
    asyncio.run(main())
