import os
import json
import time
import random
import requests
from datetime import datetime
import webbrowser
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import urllib.parse

class WeChatScraper:
    def __init__(self):
        load_dotenv()
        self.session = self._create_session()
        self.newrank_key = os.getenv('NEWRANK_KEY')
        
    def _create_session(self):
        """创建一个带有请求头的会话"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        return session
    
    def get_latest_articles(self, account_name, num_pages=1):
        """获取公众号最新文章"""
        try:
            print(f"正在获取公众号 {account_name} 的最新文章...")
            articles = []
            
            # 新榜API接口
            url = "https://gw.newrank.cn/api/wechat/wechat/account/detail"
            
            # 构造请求数据
            data = {
                "keyword": account_name,
                "pageSize": 20,
                "pageNumber": 1,
                "hasDeal": False
            }
            
            # 添加新榜API密钥
            headers = {
                'Key': self.newrank_key
            }
            
            print("\n正在搜索公众号...")
            response = self.session.post(url, json=data, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"请求失败: {response.status_code}")
                return None
            
            try:
                result = response.json()
                if not result.get('success'):
                    print(f"API返回错误: {result.get('msg', '未知错误')}")
                    return None
                
                # 获取公众号信息
                account_data = result.get('data', {}).get('list', [])
                if not account_data:
                    print("未找到公众号")
                    return None
                
                account = account_data[0]
                account_id = account.get('accountId')
                
                if not account_id:
                    print("未找到公众号ID")
                    return None
                
                print(f"找到公众号: {account.get('accountName')}")
                
                # 获取文章列表
                url = "https://gw.newrank.cn/api/wechat/wechat/detail/articles"
                data = {
                    "accountId": account_id,
                    "pageSize": 20,
                    "pageNumber": 1,
                    "hasDeal": False
                }
                
                print("\n正在获取文章列表...")
                response = self.session.post(url, json=data, headers=headers, timeout=10)
                
                if response.status_code != 200:
                    print(f"获取文章列表失败: {response.status_code}")
                    return None
                
                result = response.json()
                if not result.get('success'):
                    print(f"获取文章列表失败: {result.get('msg', '未知错误')}")
                    return None
                
                article_list = result.get('data', {}).get('list', [])
                
                for article_data in article_list:
                    article = {
                        'title': article_data.get('title', ''),
                        'url': article_data.get('url', ''),
                        'time': article_data.get('publishTime', ''),
                        'description': article_data.get('digest', ''),
                        'author': account_name
                    }
                    
                    if article['title'] and article['url']:
                        articles.append(article)
                        print(f"\n找到文章: {article['title']}")
                        print(f"发布时间: {article['time']}")
                
            except ValueError as e:
                print(f"解析响应失败: {str(e)}")
                return None
            
            if articles:
                self._generate_html(articles)
                print(f"\n共获取到 {len(articles)} 篇文章")
                return articles
            else:
                print("\n未找到任何文章")
                return None
                
        except Exception as e:
            print(f"处理失败: {str(e)}")
            return None
    
    def _generate_html(self, articles):
        """生成展示文章信息的HTML页面"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Latest WeChat Articles</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f9f9f9;
                }
                .article-card {
                    background: white;
                    border-radius: 12px;
                    padding: 20px;
                    margin-bottom: 20px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    transition: transform 0.2s ease;
                }
                .article-card:hover {
                    transform: translateY(-5px);
                }
                .article-title {
                    margin: 0;
                    font-size: 18px;
                    font-weight: 600;
                    margin-bottom: 10px;
                }
                .article-title a {
                    color: #1a1a1a;
                    text-decoration: none;
                }
                .article-title a:hover {
                    color: #0066cc;
                }
                .article-meta {
                    color: #666;
                    font-size: 14px;
                    margin-bottom: 10px;
                }
                .article-author {
                    color: #666;
                    font-size: 14px;
                    margin-bottom: 10px;
                }
                .article-description {
                    color: #444;
                    font-size: 14px;
                    line-height: 1.6;
                }
                .header {
                    text-align: center;
                    margin-bottom: 30px;
                }
                .header h1 {
                    color: #1a1a1a;
                    font-size: 24px;
                }
                .timestamp {
                    text-align: center;
                    color: #666;
                    font-size: 14px;
                    margin-top: 30px;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Latest WeChat Articles</h1>
            </div>
        """
        
        for article in articles:
            html_template += f"""
            <div class="article-card">
                <h2 class="article-title">
                    <a href="{article['url']}" target="_blank">{article['title']}</a>
                </h2>
                <div class="article-meta">
                    发布时间: {article['time']}
                </div>
                <div class="article-author">
                    作者: {article['author']}
                </div>
                <div class="article-description">
                    {article['description']}
                </div>
            </div>
            """
        
        html_template += f"""
            <div class="timestamp">
                Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </body>
        </html>
        """
        
        # 保存HTML文件
        html_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wechat_articles.html')
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_template)
        
        # 在浏览器中打开
        webbrowser.open(html_file)

def main():
    # 创建微信爬虫实例
    scraper = WeChatScraper()
    
    # 获取指定公众号的文章
    account_name = "请辩"  # 直接使用公众号名称
    print(f"\n开始获取公众号 '{account_name}' 的文章...")
    scraper.get_latest_articles(account_name)

if __name__ == '__main__':
    main()
