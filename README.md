# YouTube Channel Video Scraper

这是一个简单的Python脚本，用于爬取指定YouTube频道的最新视频链接。

## 功能特点

- 获取指定YouTube频道的最新视频
- 支持自定义获取视频数量
- 将视频信息保存为JSON格式
- 包含视频标题、链接和上传日期

## 安装依赖

1. 确保已安装Python 3.6或更高版本
2. 安装所需依赖包：

```bash
pip install -r requirements.txt
```

## 使用方法

1. 打开 `youtube_scraper.py` 文件
2. 修改 `main()` 函数中的 `channel_url` 变量为你想要爬取的YouTube频道URL
3. 可选：调整 `max_videos` 参数来设置要获取的视频数量
4. 运行脚本：

```bash
python youtube_scraper.py
```

## 输出

脚本会在当前目录下创建一个JSON文件，文件名格式为 `youtube_videos_时间戳.json`。
文件包含以下信息：
- 视频标题
- 视频URL
- 上传日期

## 注意事项

- 请确保遵守YouTube的服务条款和API使用政策
- 建议适当控制爬取频率，避免频繁请求
