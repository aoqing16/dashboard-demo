import re
import os
import json
from datetime import datetime
import time
from bilibili_api import video, sync
import requests
from urllib.parse import urlparse
import shutil
import feedparser
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import subprocess

class URLUploader:
    def __init__(self):
        """初始化上传器"""
        self.setup_paths()
        self.setup_browser_config()
        self.setup_special_authors()
        self.platform_patterns = {
            'bilibili': r'(https?://)?(www\.)?(bilibili\.com|b23\.tv)/.*',
            'twitter': r'(https?://)?(www\.)?(twitter\.com|x\.com)/.*',
            'podcast': r'(https?://)?(www\.)?(podcasts\.apple\.com|feeds\..*\.com|.*\.libsyn\.com|.*\.rss|.*\.xml)/.*',
            'xiaohongshu': r'(https?://)?(www\.)?(xiaohongshu\.com|xhs\.cn)/.*'
        }
    
    def setup_paths(self):
        """设置必要的路径"""
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.repo_dir = os.path.join(self.base_dir, 'dashboard-demo')
        self.repo_url = 'https://github.com/aoqing16/dashboard-demo.git'
        self.docs_dir = os.path.join(self.repo_dir, 'docs')
        self.images_dir = os.path.join(self.docs_dir, 'images')
        self.data_file = os.path.join(self.docs_dir, 'data.json')
        
        # 确保目录存在
        os.makedirs(self.repo_dir, exist_ok=True)
        os.makedirs(self.docs_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)

    def ensure_repo(self):
        """确保仪表盘仓库存在并更新"""
        try:
            if not os.path.exists(self.repo_dir):
                print("克隆仓库...")
                subprocess.run(['git', 'clone', self.repo_url, self.repo_dir], check=True)
            
            # 确保必要的目录存在
            os.makedirs(self.docs_dir, exist_ok=True)
            os.makedirs(self.images_dir, exist_ok=True)
            
        except Exception as e:
            print(f"仓库操作失败: {str(e)}")
            print("将使用本地目录")
            # 确保必要的目录存在
            os.makedirs(self.repo_dir, exist_ok=True)
            os.makedirs(self.docs_dir, exist_ok=True)
            os.makedirs(self.images_dir, exist_ok=True)

    def commit_and_push(self, message):
        """提交并推送更改"""
        try:
            original_dir = os.getcwd()
            os.chdir(self.repo_dir)
            
            try:
                # 强制覆盖本地更改
                subprocess.run(['git', 'fetch', 'origin'], check=True)
                subprocess.run(['git', 'reset', '--hard', 'origin/main'], check=True)
                subprocess.run(['git', 'clean', '-fd'], check=True)
                
                # 复制新文件到正确位置
                os.makedirs(self.docs_dir, exist_ok=True)
                os.makedirs(self.images_dir, exist_ok=True)
                
                # 创建一个空的.gitkeep文件以确保目录被跟踪
                with open(os.path.join(self.docs_dir, '.gitkeep'), 'w') as f:
                    pass
                with open(os.path.join(self.images_dir, '.gitkeep'), 'w') as f:
                    pass
                
                # 添加并提交所有更改
                subprocess.run(['git', 'add', '-A'], check=True)
                subprocess.run(['git', 'commit', '-m', message], check=True)
                subprocess.run(['git', 'push', '-f', 'origin', 'main'], check=True)
                
                print("更改已推送到仪表盘")
            finally:
                os.chdir(original_dir)
        except Exception as e:
            print(f"推送更改失败: {str(e)}")
            print("本地更改已保存，但未能同步到网页版仪表盘")

    def setup_browser_config(self):
        """设置浏览器配置"""
        self.browser_config = {
            'args': [
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--window-size=1920,1080',
            ],
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            }
        }

    def setup_special_authors(self):
        """设置特定作者的信息"""
        self.special_authors = {
            'op7418': {
                'name': '歸藏(guizang.ai)',
                'cover': os.path.join(self.base_dir, 'guizang_cover.jpg')
            },
            'aigclink': {
                'name': 'AIGCLINK',
                'cover': os.path.join(self.base_dir, 'aigclink_cover.jpg')
            },
            'mckaywrigley': {
                'name': 'Mckay Wrigley',
                'cover': os.path.join(self.base_dir, 'mckay_cover.jpg')
            },
            'dotey': {
                'name': '宝玉',
                'cover': os.path.join(self.base_dir, 'dotey_cover.jpg')
            },
            'AxtonLiu': {
                'name': 'Axton',
                'cover': os.path.join(self.base_dir, 'axton_cover.jpg')
            },
            'levelsio': {
                'name': 'Peter Levels',
                'cover': os.path.join(self.base_dir, 'levels_cover.jpg')
            }
        }

    def load_data(self):
        """加载现有数据"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"youtube": [], "bilibili": [], "twitter": [], "podcast": [], "xiaohongshu": []}

    def save_data(self, data):
        """保存数据到JSON文件"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def identify_platform(self, url):
        """识别URL属于哪个平台"""
        for platform, pattern in self.platform_patterns.items():
            if re.match(pattern, url):
                return platform
        return None

    async def get_bilibili_info(self, url):
        """获取B站视频信息"""
        try:
            # 处理短链接
            if 'b23.tv' in url:
                response = requests.get(url, allow_redirects=True)
                url = response.url

            # 从URL中提取视频ID
            bv_pattern = r'BV\w{10}'
            match = re.search(bv_pattern, url)
            if not match:
                return None

            bv_id = match.group()
            v = video.Video(bvid=bv_id)
            info = await v.get_info()

            return {
                'title': info['title'],
                'author': info['owner']['name'],
                'cover_url': info['pic'],
                'platform': 'bilibili'
            }
        except Exception as e:
            print(f"获取B站信息时出错: {str(e)}")
            return None

    async def get_podcast_info(self, url):
        """获取播客信息"""
        try:
            if 'podcasts.apple.com' in url:
                # 处理Apple Podcasts URL
                async with async_playwright() as p:
                    browser = await p.chromium.launch(
                        headless=True,
                        args=self.browser_config['args']
                    )
                    context = await browser.new_context(
                        user_agent=self.browser_config['headers']['User-Agent']
                    )
                    page = await context.new_page()
                    await page.goto(url)
                    await page.wait_for_load_state('networkidle')

                    # 获取标题
                    title_element = await page.query_selector('h1')
                    title = await title_element.text_content() if title_element else "未知标题"

                    # 获取作者
                    author_element = await page.query_selector('div.product-header__identity a')
                    author = await author_element.text_content() if author_element else "未知作者"

                    # 获取描述
                    description_element = await page.query_selector('div.product-hero-desc__section--description')
                    description = await description_element.text_content() if description_element else ""

                    await browser.close()

                    return {
                        'title': title,
                        'author': author,
                        'description': description,
                        'platform': 'podcast'
                    }
            else:
                # 处理RSS feed URL
                feed = feedparser.parse(url)
                if feed.bozo:  # 如果解析出错
                    return None
                
                latest_episode = feed.entries[0] if feed.entries else None
                if not latest_episode:
                    return None

                return {
                    'title': latest_episode.title,
                    'author': feed.feed.author if hasattr(feed.feed, 'author') else feed.feed.title,
                    'description': latest_episode.description if hasattr(latest_episode, 'description') else '',
                    'platform': 'podcast'
                }
        except Exception as e:
            print(f"获取播客信息时出错: {str(e)}")
            return None

    async def get_xiaohongshu_info(self, url):
        """获取小红书信息"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=self.browser_config['args']
                )
                context = await browser.new_context(
                    user_agent=self.browser_config['headers']['User-Agent']
                )
                page = await context.new_page()
                await page.goto(url)
                await page.wait_for_load_state('networkidle')

                # 获取作者名
                author = await page.query_selector('.user-nickname')
                author_name = await author.text_content() if author else "未知作者"

                # 获取文案内容
                content = await page.query_selector('.content')
                content_text = await content.text_content() if content else ""

                await browser.close()

                return {
                    'title': content_text[:50] + '...' if len(content_text) > 50 else content_text,
                    'author': author_name,
                    'content': content_text,
                    'platform': 'xiaohongshu'
                }
        except Exception as e:
            print(f"获取小红书信息时出错: {str(e)}")
            return None

    async def get_twitter_info(self, url):
        """获取X(Twitter)信息"""
        try:
            headers = {
                'User-Agent': self.browser_config['headers']['User-Agent'],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
            }
            
            # 将x.com转换为vxtwitter.com
            url = url.replace('x.com', 'vxtwitter.com')
            url = url.replace('twitter.com', 'vxtwitter.com')
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            # vxtwitter返回JSON格式的数据
            data = response.json()
            
            return {
                'title': data.get('text', '')[:50] + '...' if len(data.get('text', '')) > 50 else data.get('text', ''),
                'author': data.get('user_name', '未知作者'),
                'content': data.get('text', ''),
                'platform': 'twitter'
            }
        except Exception as e:
            print(f"获取X(Twitter)信息时出错: {str(e)}")
            return None

    def get_special_author_info(self, url):
        """获取特定作者信息"""
        for username, info in self.special_authors.items():
            if f'x.com/{username}' in url or f'twitter.com/{username}' in url:
                return info
        return None

    def copy_cover_image(self, source_path, platform):
        """复制封面图片到images目录"""
        if not os.path.exists(source_path):
            print(f"警告：封面图片不存在: {source_path}")
            return None
        
        timestamp = int(time.time())
        filename = f"{platform}_{timestamp}.jpg"
        target_path = os.path.join(self.images_dir, filename)
        
        try:
            shutil.copy2(source_path, target_path)
            return filename
        except Exception as e:
            print(f"复制图片时出错: {str(e)}")
            return None

    def download_image(self, url, platform):
        """下载图片到仪表盘目录"""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # 生成唯一的文件名
            timestamp = int(time.time())
            filename = f"{platform}_{timestamp}.jpg"
            save_path = os.path.join(self.images_dir, filename)
            
            # 确保保存路径存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return filename
        except Exception as e:
            print(f"下载图片时出错: {str(e)}")
            return None

    def add_content(self, platform, content):
        """添加内容到数据文件"""
        data = self.load_data()
        if platform not in data:
            data[platform] = []
        
        # 添加时间戳
        content['timestamp'] = datetime.now().isoformat()
        
        # 将新内容添加到列表开头
        data[platform].insert(0, content)
        
        # 保存更新后的数据
        self.save_data(data)

    def process_url(self, url):
        """处理输入的URL"""
        platform = self.identify_platform(url)
        if not platform:
            print("无法识别的URL平台")
            return None

        if platform == 'bilibili':
            # 由于bilibili API是异步的，需要在外部使用异步函数调用
            return platform
        else:
            print(f"检测到{platform}平台的URL")
            return platform

    def save_to_dashboard(self, title, author, url, image_path=None):
        """保存内容到仪表板"""
        try:
            # 确保目录存在
            os.makedirs(self.docs_dir, exist_ok=True)
            os.makedirs(self.images_dir, exist_ok=True)
            
            # 读取现有数据
            data_file = os.path.join(self.docs_dir, 'data.json')
            if os.path.exists(data_file):
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {
                    'youtube': [],
                    'bilibili': [],
                    'twitter': [],
                    'xiaohongshu': [],
                    'podcast': []
                }
            
            # 准备新内容
            new_content = {
                'title': title,
                'author': author,
                'url': url,
                'published': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 处理图片
            if image_path:
                # 生成唯一的图片文件名
                timestamp = int(time.time())
                image_filename = f'twitter_{timestamp}.jpg'
                target_path = os.path.join(self.images_dir, image_filename)
                
                # 复制图片文件
                shutil.copy2(image_path, target_path)
                new_content['thumbnail'] = f'docs/images/{image_filename}'
            
            # 添加新内容到对应平台
            if 'twitter.com' in url or 'x.com' in url:
                data['twitter'].insert(0, new_content)
            elif 'bilibili.com' in url:
                data['bilibili'].insert(0, new_content)
            elif 'youtube.com' in url:
                data['youtube'].insert(0, new_content)
            elif 'xiaohongshu.com' in url:
                data['xiaohongshu'].insert(0, new_content)
            
            # 保存更新后的数据
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 提交更改
            commit_message = f'添加新内容: {title}'
            self.commit_and_push(commit_message)
            
            print("内容已成功保存")
            
        except Exception as e:
            print(f"保存内容时出错: {str(e)}")

if __name__ == "__main__":
    import asyncio
    
    async def main():
        uploader = URLUploader()
        uploader.ensure_repo()
        
        while True:
            url = input("请输入URL（直接按回车退出）: ").strip()
            if not url:
                break

            platform = uploader.process_url(url)
            info = None
            
            if platform == 'bilibili':
                info = await uploader.get_bilibili_info(url)
            else:
                # 检查是否是特定作者
                special_info = uploader.get_special_author_info(url)
                
                # 获取用户输入
                title = input("请输入标题（可选，直接回车跳过）: ").strip()
                author = input("请输入作者名（可选，直接回车跳过）: ").strip() if not special_info else special_info['name']
                cover_path = input("请输入封面图片路径（可选，直接回车跳过）: ").strip() if not special_info else special_info['cover']
                
                info = {
                    'title': title if title else url,
                    'author': author if author else "未知作者",
                    'platform': platform,
                    'url': url
                }
                
                # 处理封面图片
                if cover_path:
                    image_filename = uploader.copy_cover_image(cover_path, platform)
                    if image_filename:
                        info['image'] = f'images/{image_filename}'
            
            if info:
                print(f"\n获取到的信息：")
                print(f"标题: {info['title']}")
                print(f"作者: {info['author']}")
                if 'content' in info:
                    print(f"内容: {info['content'][:100]}...")
                
                # 如果是B站视频且有封面图片
                if platform == 'bilibili' and 'cover_url' in info:
                    image_filename = uploader.download_image(info['cover_url'], platform)
                    if image_filename:
                        info['image'] = f'images/{image_filename}'
                
                # 添加到数据文件
                uploader.add_content(platform, info)
                uploader.commit_and_push(f"添加新内容: {info['title'][:50]}")
                print("内容已成功保存")
            else:
                print(f"无法获取{platform}平台的信息")

    asyncio.run(main())
