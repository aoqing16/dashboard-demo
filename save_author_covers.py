import os
import sys
import shutil
import codecs

# 设置stdout为utf-8编码
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

def copy_image(source_path, target_path):
    """复制图片文件"""
    try:
        shutil.copy2(source_path, target_path)
        print(f"已复制图片: {os.path.basename(target_path)}")
        return True
    except Exception as e:
        print(f"复制失败: {str(e)}")
        return False

def main():
    # 源图片目录
    source_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'author_covers')
    
    # 检查源目录是否存在
    if not os.path.exists(source_dir):
        print(f"错误: 源目录 {source_dir} 不存在")
        print("请确保以下图片已保存到 author_covers 目录:")
        print("1. aigclink_cover.jpg - 装饰字母A图片")
        print("2. dotey_cover.jpg - 武士图片")
        print("3. guizang_cover.jpg - 橘猫图片")
        print("4. axton_cover.jpg - 动漫眼镜人物图片")
        print("5. mckay_cover.jpg - 滑雪镜图片")
        print("6. levels_cover.jpg - 躺着用笔记本图片")
        print("7. wenhuayouxian_cover.jpg - WE KNOW NOTHING图片")
        print("8. tianzhen_cover.jpg - 不天真图片")
        return
    
    # 图片文件名列表
    cover_files = [
        'aigclink_cover.jpg',      # 装饰字母A图片
        'dotey_cover.jpg',         # 武士图片
        'guizang_cover.jpg',       # 橘猫图片
        'axton_cover.jpg',         # 动漫眼镜人物图片
        'mckay_cover.jpg',         # 滑雪镜图片
        'levels_cover.jpg',        # 躺着用笔记本图片
        'wenhuayouxian_cover.jpg', # WE KNOW NOTHING图片
        'tianzhen_cover.jpg'       # 不天真图片
    ]
    
    # 目标目录
    repo_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dashboard-demo')
    images_dir = os.path.join(repo_dir, 'images')
    os.makedirs(images_dir, exist_ok=True)
    
    # 复制每个图片
    for filename in cover_files:
        source_path = os.path.join(source_dir, filename)
        target_path = os.path.join(images_dir, filename)
        
        if not os.path.exists(source_path):
            print(f"错误: 源文件不存在 {filename}")
            continue
            
        print(f"\n正在复制 {filename}...")
        if os.path.exists(target_path):
            os.remove(target_path)
        if copy_image(source_path, target_path):
            print(f"成功: {filename} 复制完成")
        else:
            print(f"失败: {filename} 复制失败")

if __name__ == "__main__":
    main()
