import random
import requests
from fake_useragent import UserAgent
import time
import json
import os
import concurrent.futures

class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.user_agent = UserAgent()
        self.last_update = 0
        self.update_interval = 300  # 5分钟更新一次代理列表
        
        # 从文件加载代理
        self.proxy_file = 'working_proxies.json'
        self.load_proxies()
    
    def load_proxies(self):
        """从文件加载可用代理"""
        if os.path.exists(self.proxy_file):
            try:
                with open(self.proxy_file, 'r') as f:
                    data = json.load(f)
                    if time.time() - data.get('timestamp', 0) < 3600:  # 1小时内的代理仍然有效
                        self.proxies = data.get('proxies', [])
                        print(f"从文件加载了 {len(self.proxies)} 个代理")
                        return
            except Exception as e:
                print(f"加载代理文件失败: {str(e)}")
        
        self.update_proxies()
    
    def save_proxies(self):
        """保存可用代理到文件"""
        try:
            with open(self.proxy_file, 'w') as f:
                json.dump({
                    'timestamp': time.time(),
                    'proxies': self.proxies
                }, f)
            print(f"保存了 {len(self.proxies)} 个代理到文件")
        except Exception as e:
            print(f"保存代理文件失败: {str(e)}")
    
    def update_proxies(self):
        """更新代理列表"""
        print("正在更新代理列表...")
        
        # 从多个免费代理源获取代理
        proxy_sources = [
            'https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt',
            'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt',
            'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt',
            'https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list/data.txt',
            'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt',
            'https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt',
            'https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt',
            'https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt',
            'https://raw.githubusercontent.com/RX4096/proxy-list/main/online/http.txt',
            'https://raw.githubusercontent.com/RX4096/proxy-list/main/online/https.txt'
        ]
        
        new_proxies = set()
        for source in proxy_sources:
            try:
                response = requests.get(source, timeout=10)
                if response.status_code == 200:
                    proxies = response.text.strip().split('\n')
                    new_proxies.update(proxies)
                    print(f"从 {source} 获取了 {len(proxies)} 个代理")
            except Exception as e:
                print(f"从 {source} 获取代理失败: {str(e)}")
                continue
        
        # 验证代理
        working_proxies = []
        total_proxies = len(new_proxies)
        print(f"正在验证 {total_proxies} 个代理...")
        
        # 使用多线程验证代理
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            future_to_proxy = {executor.submit(self._verify_proxy, proxy): proxy for proxy in new_proxies}
            for future in concurrent.futures.as_completed(future_to_proxy):
                proxy = future_to_proxy[future]
                try:
                    proxy_dict = future.result()
                    if proxy_dict:
                        working_proxies.append(proxy_dict)
                        print(f"找到可用代理: {proxy} ({len(working_proxies)}/{total_proxies})")
                except Exception as e:
                    continue
        
        self.proxies = working_proxies
        self.last_update = time.time()
        self.save_proxies()
        print(f"代理更新完成，共有 {len(self.proxies)} 个可用代理")
    
    def _verify_proxy(self, proxy):
        """验证单个代理"""
        try:
            proxy_dict = {
                'http': f'http://{proxy.strip()}',
                'https': f'http://{proxy.strip()}'
            }
            
            # 使用多个网站测试代理
            test_urls = [
                'http://www.google.com',
                'http://www.example.com',
                'http://www.httpbin.org/ip'
            ]
            
            for url in test_urls:
                response = requests.get(
                    url,
                    proxies=proxy_dict,
                    timeout=5,
                    verify=False  # 忽略SSL错误
                )
                if response.status_code == 200:
                    return proxy_dict
            
            return None
        except:
            return None
    
    def get_proxy(self):
        """获取一个随机代理"""
        if not self.proxies or time.time() - self.last_update > self.update_interval:
            self.update_proxies()
        
        return random.choice(self.proxies) if self.proxies else None
    
    def get_headers(self):
        """获取随机User-Agent的请求头"""
        return {
            'User-Agent': self.user_agent.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

proxy_manager = ProxyManager()
