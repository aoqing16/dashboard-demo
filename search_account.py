import os
import time
import hashlib
import requests
from dotenv import load_dotenv

def search_wechat_account(keyword):
    # 加载环境变量
    load_dotenv()
    api_key = os.getenv('NEWRANK_KEY')  # 使用新榜的API密钥
    
    if not api_key:
        print("错误：未找到新榜API密钥，请在.env文件中设置NEWRANK_KEY")
        return
    
    print(f"正在搜索公众号: {keyword}")
    
    try:
        # 发送请求
        url = "https://api.newrank.cn/api/v2/wx/account/search"
        print(f"\n发送请求到: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Key': api_key
        }
        
        params = {
            'keyword': keyword,
            'pageSize': 10,
            'pageNumber': 1
        }
        
        print("\n请求参数:")
        for k, v in params.items():
            print(f"{k}: {v}")
        
        response = requests.post(url, json=params, headers=headers, timeout=10)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text[:500]}...")  # 只显示前500个字符
        
        response.raise_for_status()  # 检查HTTP错误
        data = response.json()
        
        if data.get('code') == 0 and data.get('data', {}).get('list'):
            print("\n找到以下公众号：")
            for account in data['data']['list']:
                print(f"\n名称: {account.get('name', 'N/A')}")
                print(f"微信号: {account.get('account', 'N/A')}")
                print(f"简介: {account.get('introduction', '无')}")
                print(f"粉丝数: {account.get('fans_num', 'N/A')}")
                print(f"头条平均阅读: {account.get('avg_read_num', 'N/A')}")
                print("-" * 50)
        else:
            print(f"\n搜索失败或未找到结果: {data.get('msg', '未知错误')}")
            print(f"错误代码: {data.get('code', 'N/A')}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n网络请求错误: {str(e)}")
    except ValueError as e:
        print(f"\nJSON解析错误: {str(e)}")
    except Exception as e:
        print(f"\n未知错误: {str(e)}")

if __name__ == '__main__':
    search_wechat_account("请辩")
