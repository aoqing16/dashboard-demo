#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from dotenv import load_dotenv

class PodcastScraper:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    async def setup_browser(self):
        """设置浏览器"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--window-size=1920,1080',
                '--disable-notifications',
                '--disable-popup-blocking',
                '--disable-infobars',
                '--ignore-certificate-errors',
                '--no-default-browser-check',
                '--no-first-run'
            ]
        )
        
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Pragma': 'no-cache',
                'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1'
            }
        )
        
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'platform', {
                get: () => 'Win32'
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en-US', 'en']
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)
        
        self.page = await self.context.new_page()
        self.page.set_default_timeout(30000)
        
    async def get_podcast_episodes(self, podcast_url):
        """获取播客集信息"""
        episodes = []
        try:
            # 设置更长的超时时间
            self.page.set_default_timeout(60000)
            
            # 访问页面并等待加载
            await self.page.goto(podcast_url)
            
            # 等待播客标题元素出现
            await self.page.wait_for_selector('.product-header__title', timeout=60000)
            await asyncio.sleep(5)  # 额外等待以确保内容加载完成
            
            # 获取播客标题
            podcast_title = await self.page.text_content('.product-header__title')
            self.logger.info(f"正在获取播客: {podcast_title}")
            
            # 等待并获取所有剧集
            await self.page.wait_for_selector('.web-chrome-playback-track', timeout=60000)
            episode_items = await self.page.query_selector_all('.web-chrome-playback-track')
            
            # 只处理第一个（最新）剧集
            if episode_items:
                item = episode_items[0]
                try:
                    # 获取剧集标题
                    title = await item.query_selector('.track-title')
                    title_text = await title.text_content() if title else "未知标题"
                    
                    # 获取发布日期
                    date = await item.query_selector('time')
                    date_text = await date.text_content() if date else "未知日期"
                    
                    # 获取时长
                    duration = await item.query_selector('.time-duration')
                    duration_text = await duration.text_content() if duration else ""
                    
                    # 获取描述
                    description = await item.query_selector('.track-description')
                    description_text = await description.text_content() if description else ""
                    
                    # 获取剧集链接
                    link = await item.query_selector('a[href*="/episode/"]')
                    episode_url = await link.get_attribute('href') if link else ""
                    if episode_url and not episode_url.startswith('http'):
                        episode_url = f"https://podcasts.apple.com{episode_url}"
                    
                    episode = {
                        'title': title_text.strip(),
                        'date': date_text.strip(),
                        'duration': duration_text.strip(),
                        'description': description_text.strip(),
                        'podcast_title': podcast_title.strip(),
                        'platform': 'Apple Podcasts',
                        'url': episode_url,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    episodes.append(episode)
                    self.logger.info(f"获取到最新剧集: {title_text}")
                    
                except Exception as e:
                    self.logger.error(f"解析剧集时出错: {str(e)}")
            else:
                self.logger.warning("未找到任何剧集")
            
        except Exception as e:
            self.logger.error(f"获取播客信息时出错: {str(e)}")
        
        return episodes
            
    def save_episodes_to_json(self, episodes, output_file='podcast_episodes.json'):
        """保存剧集信息到JSON文件"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(episodes, f, ensure_ascii=False, indent=2)
            self.logger.info(f"已保存剧集信息到 {output_file}")
        except Exception as e:
            self.logger.error(f"保存JSON文件时出错: {str(e)}")
            
    def generate_html(self, episodes, output_file='podcast_episodes.html'):
        """生成剧集列表的HTML内容"""
        try:
            html_content = '\n'.join([
                '''
                <div class="episode-card">
                    <div class="episode-info">
                        <span class="platform-tag platform-podcast">Apple Podcasts</span>
                        <h3>{title}</h3>
                        <p class="podcast-title">{podcast_title}</p>
                        <p class="episode-meta">发布时间: {date} | 时长: {duration}</p>
                        <p class="episode-description">{description}</p>
                    </div>
                </div>
                '''.format(**episode) for episode in episodes
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
            
            # 获取播客列表
            podcasts = [
                'https://podcasts.apple.com/us/podcast/%E5%A4%A9%E7%9C%9F%E4%B8%8D%E5%A4%A9%E7%9C%9F/id1731784296?l=zh-Hans-CN',
                'https://podcasts.apple.com/us/podcast/%E6%96%87%E5%8C%96%E6%9C%89%E9%99%90/id1482731836?l=zh-Hans-CN'
            ]
            
            # 初始化浏览器
            await self.setup_browser()
            
            # 存储所有剧集
            all_episodes = []
            
            # 遍历每个播客
            for podcast_url in podcasts:
                print(f"\n开始获取播客: {podcast_url}")
                episodes = await self.get_podcast_episodes(podcast_url)
                if episodes:
                    all_episodes.extend(episodes)
                    print(f"成功获取到 {len(episodes)} 个剧集")
                else:
                    print(f"未能获取到播客剧集信息")
                
                # 添加延迟
                await asyncio.sleep(2)
            
            if all_episodes:
                # 保存剧集信息
                self.save_episodes_to_json(all_episodes)
                self.generate_html(all_episodes)
                print(f"\n总计获取到 {len(all_episodes)} 个剧集")
            else:
                print("\n未能获取到任何剧集信息")
            
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
            logging.FileHandler('podcast_scraper.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    scraper = PodcastScraper()
    await scraper.run_scraper()

if __name__ == "__main__":
    asyncio.run(main())
