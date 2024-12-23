import os
import sys
import shutil
import codecs

# 设置stdout为utf-8编码
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

def save_image(source_path, save_path):
    """复制图片到目标位置"""
    try:
        shutil.copy2(source_path, save_path)
        return True
    except Exception as e:
        print(f"保存失败: {str(e)}")
    return False

def main():
    # 创建保存目录
    save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'author_covers')
    os.makedirs(save_dir, exist_ok=True)
    
    # 要保存的图片
    images = [
        ('aigclink_cover.jpg', '装饰字母A图片'),  # AIGCLINK
        ('dotey_cover.jpg', '武士图片'),  # 宝玉
        ('guizang_cover.jpg', '橘猫图片'),  # 歸藏
    ]
    
    # 保存每个图片
    for filename, desc in images:
        source_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        save_path = os.path.join(save_dir, filename)
        
        if not os.path.exists(source_path):
            print(f"\n错误: 找不到源文件 {filename} ({desc})")
            continue
            
        print(f"\n正在保存 {filename}...")
        if save_image(source_path, save_path):
            print(f"成功: {filename} 已保存")
        else:
            print(f"失败: {filename} 保存失败")

if __name__ == "__main__":
    main()
