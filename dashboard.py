import os
import json
from datetime import datetime
import concurrent.futures
import subprocess
import sys
from jinja2 import Template
import shutil

class Dashboard:
    def __init__(self):
        self.output_dir = os.path.dirname(os.path.abspath(__file__))
        self.docs_dir = os.path.join(self.output_dir, 'docs')
        self.data = {
            'youtube': [],
            'twitter': [],
            'bilibili': []
        }
        
        # 确保 docs 目录存在
        os.makedirs(self.docs_dir, exist_ok=True)
    
    def run_scraper(self, scraper_name):
        """运行爬虫脚本"""
        try:
            script_name = f"{scraper_name}_scraper.py"
            if scraper_name == 'x':
                script_name = "x_scraper.py"
                
            script_path = os.path.join(self.output_dir, script_name)
            print(f"\n正在运行 {scraper_name} 爬虫...")
            
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(f"[{scraper_name}] {output.strip()}")
            
            _, stderr = process.communicate()
            if process.returncode != 0:
                print(f"{scraper_name} 爬虫运行失败:")
                print(stderr)
            else:
                print(f"{scraper_name} 爬虫运行完成")
                
        except Exception as e:
            print(f"运行 {scraper_name} 爬虫时出错: {str(e)}")
    
    def run_scrapers(self):
        """并行运行所有爬虫"""
        scrapers = ['youtube', 'x', 'bilibili']
        
        print("\n开始并行运行爬虫...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(self.run_scraper, scraper): scraper for scraper in scrapers}
            
            for future in concurrent.futures.as_completed(futures):
                scraper = futures[future]
                try:
                    future.result()
                except Exception as e:
                    print(f"{scraper} 爬虫执行失败: {str(e)}")
    
    def load_youtube_videos(self):
        """加载YouTube视频数据"""
        try:
            json_file = os.path.join(self.output_dir, 'youtube_videos.json')
            if os.path.exists(json_file):
                with open(json_file, 'r', encoding='utf-8') as f:
                    self.data['youtube'] = json.load(f)
                    print(f"加载了 {len(self.data['youtube'])} 个YouTube视频")
        except Exception as e:
            print(f"加载YouTube视频失败: {str(e)}")
    
    def load_twitter_tweets(self):
        """加载Twitter推文数据"""
        try:
            json_file = os.path.join(self.output_dir, 'tweets.json')
            if os.path.exists(json_file):
                with open(json_file, 'r', encoding='utf-8') as f:
                    self.data['twitter'] = json.load(f)
                    print(f"加载了 {len(self.data['twitter'])} 条推文")
        except Exception as e:
            print(f"加载推文失败: {str(e)}")
    
    def load_bilibili_videos(self):
        """加载B站视频数据"""
        try:
            json_file = os.path.join(self.output_dir, 'bilibili_videos.json')
            if os.path.exists(json_file):
                with open(json_file, 'r', encoding='utf-8') as f:
                    self.data['bilibili'] = json.load(f)
                    print(f"加载了 {len(self.data['bilibili'])} 个B站视频")
        except Exception as e:
            print(f"加载B站视频失败: {str(e)}")
    
    def generate_dashboard(self):
        """生成仪表板HTML"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 读取模板文件
        template_path = os.path.join(os.path.dirname(__file__), 'dashboard_template.html')
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # 渲染模板
        template = Template(template_content)
        html = template.render(
            current_time=current_time,
            data=self.data
        )
        
        # 生成HTML文件到 docs 目录
        dashboard_file = os.path.join(self.docs_dir, 'index.html')
        with open(dashboard_file, 'w', encoding='utf-8') as f:
            f.write(html)
            
        # 复制模板文件到 docs 目录
        shutil.copy2(template_path, os.path.join(self.docs_dir, 'dashboard_template.html'))
        
        print(f"\n仪表板已生成: {dashboard_file}")
        return dashboard_file

def main():
    # 创建仪表板实例
    dashboard = Dashboard()
    
    # 并行运行所有爬虫
    print("\n=== 第一步：运行爬虫 ===")
    dashboard.run_scrapers()
    
    # 等待3秒确保文件写入完成
    print("\n等待文件写入完成...")
    import time
    time.sleep(3)
    
    # 加载各种数据
    print("\n=== 第二步：加载数据 ===")
    dashboard.load_youtube_videos()
    dashboard.load_twitter_tweets()
    dashboard.load_bilibili_videos()
    
    # 生成仪表板
    print("\n=== 第三步：生成仪表板 ===")
    dashboard_file = dashboard.generate_dashboard()
    
    # 提示用户如何部署
    print("\n=== 如何部署到 GitHub Pages ===")
    print("1. 在 GitHub 上创建一个新的仓库")
    print("2. 运行以下命令：")
    print("   git add docs/*")
    print("   git commit -m 'Update dashboard'")
    print("   git push")
    print("3. 在仓库设置中启用 GitHub Pages，选择 docs 目录作为源")
    print("4. 访问 https://[用户名].github.io/[仓库名] 查看仪表板")

if __name__ == '__main__':
    main()
