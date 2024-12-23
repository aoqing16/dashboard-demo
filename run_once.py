#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from 油管爬取 import YouTubeScraper
from 手动爬取 import ManualUploader
import logging
import os
import shutil
import git
from datetime import datetime

def push_to_github(docs_dir):
    try:
        repo = git.Repo(os.path.dirname(docs_dir))
        
        # 添加所有变更
        repo.git.add('docs/*')
        
        # 提交变更
        commit_message = f"Update dashboard: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        repo.git.commit('-m', commit_message)
        
        # 推送到远程
        origin = repo.remote(name='origin')
        origin.push()
        
        print("已成功推送更新到 GitHub")
        print("请访问 https://aoqing16.github.io/dashboard-demo/ 查看更新后的内容")
        print("（可能需要等待1-2分钟GitHub Pages才会更新）")
        
    except Exception as e:
        print(f"推送到GitHub时出错: {str(e)}")

def main():
    try:
        # 创建日志目录
        log_dir = os.path.dirname(os.path.abspath(__file__))
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'youtube_scraper.log'), encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        logger = logging.getLogger(__name__)
        
        logger.info("="*50)
        logger.info("执行单次YouTube视频抓取")
        logger.info(f"当前工作目录: {os.getcwd()}")
        
        # 创建爬虫实例并运行
        scraper = YouTubeScraper()
        scraper.run_scraper()
        
        # 确保docs目录存在
        docs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docs')
        if not os.path.exists(docs_dir):
            os.makedirs(docs_dir)
        
        # 复制输出文件到docs目录
        files_to_copy = ['index.html', 'youtube_videos.html', 'youtube_videos.json']
        for file in files_to_copy:
            if os.path.exists(file):
                shutil.copy2(file, os.path.join(docs_dir, file))
                logger.info(f"已复制 {file} 到 docs 目录")
        
        logger.info("抓取完成，文件已更新到docs目录")
        
        # 自动推送到GitHub
        push_to_github(docs_dir)
        
    except Exception as e:
        logger.error(f"程序出错: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
