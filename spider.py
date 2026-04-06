import yt_dlp
import os
def download_music(url,save_dir):
    ydl_opts={
        'format':'bestaudio',
        'outtmpl':os.path.join(save_dir,'%(title)s.%(ext)s'),
        'nocheckcertificate':True,
        'retries':10,
        'postprocessors':[{
            'key':'FFmpegExtractAudio',
            'preferredcodec':'mp3',
            'preferredquality':'128',
        }],
        'quiet':False,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("下载完成！")
        return True
    except Exception as e:
        print(f"因为爬虫内部问题下载失败：{e}")
        return False