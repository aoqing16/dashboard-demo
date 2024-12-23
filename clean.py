import os
import shutil
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def clean_data():
    """清理所有爬取的数据文件"""
    try:
        # 要清理的文件和目录列表
        to_clean = [
            'data/dashboard_data.json',
            'dashboard-demo',
            'data/videos_*.json',  # 通配符匹配所有视频JSON文件
            'youtube_videos.json',
            'bilibili_videos.json',
            '*.log'  # 清理所有日志文件
        ]
        
        cleaned = False
        
        for item in to_clean:
            if '*' in item:
                # 处理通配符模式
                directory = os.path.dirname(item) or '.'
                pattern = os.path.basename(item)
                if directory == '.':
                    files = [f for f in os.listdir('.') if f.endswith(pattern.replace('*', ''))]
                else:
                    if os.path.exists(directory):
                        files = [os.path.join(directory, f) for f in os.listdir(directory) 
                                if f.endswith(pattern.replace('*', ''))]
                    else:
                        files = []
                
                for file in files:
                    if os.path.exists(file):
                        if os.path.isfile(file):
                            os.remove(file)
                        else:
                            shutil.rmtree(file)
                        logger.info(f"已删除: {file}")
                        cleaned = True
            else:
                # 处理具体文件或目录
                if os.path.exists(item):
                    if os.path.isfile(item):
                        os.remove(item)
                    else:
                        shutil.rmtree(item)
                    logger.info(f"已删除: {item}")
                    cleaned = True
        
        if cleaned:
            logger.info("所有数据已清理完成！")
        else:
            logger.info("没有找到需要清理的文件。")
            
    except Exception as e:
        logger.error(f"清理数据时出错: {str(e)}")
        raise

def main():
    """主函数"""
    print("\n开始清理爬虫数据...")
    clean_data()
    print("\n清理完成！")

if __name__ == "__main__":
    main()
