#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import base64
from datetime import datetime
import logging
import os

class DashboardUploader:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        
        # 从配置文件加载GitHub Token
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.github_token = config.get('github_token', '')
                if not self.github_token:
                    self.logger.error("GitHub Token not found in config.json")
                    raise ValueError("GitHub Token is required")
        except Exception as e:
            self.logger.error(f"Failed to load config: {str(e)}")
            raise

        # GitHub API设置
        self.api_base = "https://api.github.com"
        self.repo_owner = "aoqing16"
        self.repo_name = "dashboard-demo"
        self.branch = "main"  # 或者是 "master"，取决于仓库设置

    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('dashboard_upload.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )

    def get_file_content(self, path):
        """获取文件当前内容"""
        url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/contents/{path}"
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return None
        else:
            response.raise_for_status()

    def update_file(self, path, content, message):
        """更新或创建文件"""
        url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/contents/{path}"
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

        # 获取文件当前内容（如果存在）
        current_file = self.get_file_content(path)
        
        # 准备请求数据
        data = {
            "message": message,
            "content": base64.b64encode(content.encode()).decode(),
            "branch": self.branch
        }
        
        if current_file:
            data["sha"] = current_file["sha"]
        
        # 发送请求
        response = requests.put(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()

    def process_bilibili_data(self):
        """处理B站数据并上传到仪表盘"""
        try:
            # 读取B站视频数据
            with open('bilibili_videos.json', 'r', encoding='utf-8') as f:
                videos = json.load(f)
            
            if not videos:
                self.logger.warning("No videos found in bilibili_videos.json")
                return
            
            # 获取最新的视频
            latest_video = videos[0]
            
            # 准备要上传的数据
            dashboard_data = {
                "title": latest_video['title'],
                "platform": "bilibili",
                "views": latest_video['play'],
                "comments": latest_video['comment'],
                "url": f"https://www.bilibili.com/video/{latest_video['bvid']}",
                "published": latest_video['created'],
                "thumbnail": latest_video['pic'],
                "author": latest_video['author'],
                "platform_id": latest_video['bvid'],
                "updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 转换为JSON字符串
            json_content = json.dumps(dashboard_data, ensure_ascii=False, indent=2)
            
            # 上传到仪表盘仓库
            self.logger.info("Uploading data to dashboard...")
            result = self.update_file(
                "data/bilibili_latest.json",
                json_content,
                f"Update Bilibili data: {latest_video['title']}"
            )
            
            self.logger.info("Successfully uploaded data to dashboard")
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing and uploading data: {str(e)}")
            raise

def main():
    uploader = DashboardUploader()
    uploader.process_bilibili_data()

if __name__ == "__main__":
    main()
