import customtkinter as ctk
from tkinter import filedialog
import os
import threading
import spider
import time
import pygame
from mutagen.mp3 import MP3
import json
# 全局设置
# 设置外观模式为系统颜色
pygame.init()
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")
class Music(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("纯净无广告音乐播放器")
        self.geometry("700x500")
        self.grid_columnconfigure(1,weight=1)
        self.grid_rowconfigure(0,weight=1)
        self.sidebar = ctk.CTkFrame(self,width=200,corner_radius=0)
        self.sidebar.grid(row=0,column=0,sticky="nsnew")
        self.logo_label = ctk.CTkLabel(self.sidebar,text="纯净无广告音乐播放器",font=ctk.CTkFont(size=20,weight="bold"))
        self.logo_label.grid(row=0,column=0,padx=20,pady=20)
        self.load_button = ctk.CTkButton(self.sidebar,text="从本地导入音乐",command=self.load_music_folder,anchor="center")
        self.load_button.grid(row=1,column=0,padx=20,pady=10)
        self.main_playlist_frame = ctk.CTkScrollableFrame(self,label_text="播放列表")
        self.main_playlist_frame.grid(row=0,column=1,sticky="nsew",padx=20,pady=20)
        self.all_playlists={}
        self.load_history()
        self.song_list = []
        self.theme_button = ctk.CTkOptionMenu(self.sidebar,values=["系统默认","暗色","亮色"],command=self.change_theme,anchor="center")
        self.theme_button.grid(row=2,column=0,padx=20,pady=10)
        self.url=ctk.CTkEntry(self.sidebar,placeholder_text="输入b站/抖音/油管url：")
        self.url.grid(row=3,column=0,padx=20,pady=10)
        self.download_button = ctk.CTkButton(self.sidebar,text="爬取音乐",command=self.start_download_thread,anchor="center")
        self.download_button.grid(row=4,column=0,padx=20,pady=10)
        self.current_folder= ""
        self.current_song = None
        self.is_playing = False
        self.is_paused = False
        self.play_button = ctk.CTkButton(self.sidebar,text="播放",command=self.toggle_play,anchor="center")
        self.play_button.grid(row=5,column=0,padx=20,pady=10)
        self.play_button=ctk.CTkButton(self.sidebar,text="播放",command=self.toggle_play,anchor="center")
        self.play_button.grid(row=5,column=0,padx=20,pady=10)
        self.song_length=0
        self.start_offset=0
        self.is_dragging=False
        self.time_label=ctk.CTkLabel(self.sidebar,text="00:00 / 00:00")
        self.time_label.grid(row=6,column=0,padx=20,pady=(10,0))
        self.progress_slider=ctk.CTkSlider(self.sidebar,from_=0,to=100,command=self.on_slider_drag)
        self.progress_slider.grid(row=7,column=0,padx=20,pady=(0,10))
        self.progress_slider.bind("<ButtonPress-1>",self.seek_position)
        self.update_progress_bar()
        self.play_mode = 0 
        self.MUSIC_END_EVENT = pygame.USEREVENT + 1
        pygame.mixer.music.set_endevent(self.MUSIC_END_EVENT)
        self.mode_button = ctk.CTkButton(
            self.sidebar, 
            text="列表循环", 
            command=self.toggle_mode,
            anchor="center"
        )
        self.mode_button.grid(row=8, column=0, padx=20, pady=10)
        self.check_for_end()
    def start_download_thread(self):
        url=self.url.get()
        self.download_button.configure(state="disabled",text="正在爬取...")
        threading.Thread(target=self.download_music,args=(url,),daemon=True).start()
    def download_music(self,url):
        flag=spider.download_music(url,self.current_folder)
        if flag:
            self.url.delete(0,'end')
            self.download_button.configure(state="normal",text="爬取音乐")
        else:
            self.download_button.configure(state="disabled",text="爬取失败")
            time.sleep(2)
            self.download_button.configure(state="normal",text="爬取音乐")
    def change_theme(self,choice):
        if choice == "系统默认":
            ctk.set_appearance_mode("Dark")
        elif choice == "暗色":
            ctk.set_appearance_mode("Dark")
        elif choice == "亮色":
            ctk.set_appearance_mode("Light")
    def load_music_folder(self):
        folder_path = filedialog.askdirectory()
        if not folder_path:
            return
        folder_name = os.path.basename(folder_path)
        if folder_name in self.all_playlists:
            self.all_playlists[folder_name]["header"].destroy()
            self.all_playlists[folder_name]["frame"].destroy()
        header_btn = ctk.CTkButton(
            self.main_playlist_frame, 
            text=f"📁 {folder_name}", 
            anchor="w",
            fg_color="#3B3B3B", 
            hover_color="#4A4A4A",
            command=lambda name=folder_name: self.toggle_playlist(name)
        )
        header_btn.pack(fill="x", padx=5, pady=(10, 0))
        song_container = ctk.CTkFrame(self.main_playlist_frame, fg_color="transparent")
        song_container.pack(fill="x", padx=20, pady=0)
        self.all_playlists[folder_name] = {
            "header": header_btn,
            "frame": song_container,
            "songs": [],
            "is_expanded": True
        }
        for filename in os.listdir(folder_path):
            if filename.lower().endswith((".mp3", ".wav")):
                full_path = os.path.join(folder_path, filename)
                self.all_playlists[folder_name]["songs"].append(full_path)
                s_btn = ctk.CTkButton(
                    song_container,
                    text=f"  🎵 {filename}",
                    anchor="w",
                    fg_color="transparent",
                    height=28,
                    command=lambda p=full_path: self.paly_music(p)
                )
                s_btn.pack(fill="x", padx=10, pady=2)
        
        self.show_message(f"已加载歌单：{folder_name}")
        self.save_history()

    def toggle_play(self):
        if self.current_song is None:
            self.show_message(f'播放出错:没有选择歌曲')
            return
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            self.is_paused = True
            self.play_button.configure(text="继续播放")
        else:
            if self.is_paused:
                pygame.mixer.music.unpause()
                self.is_paused = False
                self.play_button.configure(text="暂停播放")
            else:
                pygame.mixer.music.play()
                self.is_playing = False
                self.play_button.configure(text="暂停播放")
    def show_message(self, message, is_error=False):
        if hasattr(self, "toast_frame") and self.toast_frame.winfo_exists():
            self.toast_frame.destroy()
        bg_color = "#8B0000" if is_error else "#2E8B57" 
        self.toast_frame = ctk.CTkFrame(self, fg_color=bg_color, corner_radius=8)
        self.toast_frame.place(relx=0.5, rely=0.85, anchor="center")
        lbl = ctk.CTkLabel(self.toast_frame, text=message, text_color="white", font=ctk.CTkFont(size=14))
        lbl.pack(side="left", padx=(15, 5), pady=10)
        close_btn = ctk.CTkButton(
            self.toast_frame, 
            text="✖", 
            width=30, 
            fg_color="transparent",       
            hover_color="gray30",         
            command=self.toast_frame.destroy 
            )
        close_btn.pack(side="right", padx=(5, 10), pady=10)
        self.after(3000, lambda:self.toast_frame.destroy() if self.toast_frame.winfo_exists() else None)
    def toggle_playlist(self, name):
        playlist = self.all_playlists[name]
        if playlist["is_expanded"]:
            playlist["frame"].pack_forget()
            playlist["header"].configure(text=f"📁 {name} (点击展开)")
            playlist["is_expanded"] = False
        else:
            playlist["frame"].pack(fill="x", padx=20, after=playlist["header"])
            playlist["header"].configure(text=f"📁 {name}")
            playlist["is_expanded"] = True

    def on_slider_drag(self, value):
        self.is_dragging = True
        current_time_str = time.strftime('%M:%S', time.gmtime(value))
        total_time_str = time.strftime('%M:%S', time.gmtime(self.song_length))
        self.time_label.configure(text=f"{current_time_str} / {total_time_str}")


    def seek_position(self, event):
        if self.current_song is None:
            return
        target_sec = self.progress_slider.get()
        self.start_offset = target_sec
        pygame.mixer.music.play(start=target_sec)
        self.is_paused = False
        self.play_button.configure(text="暂停播放")
        self.is_dragging = False


    def update_progress_bar(self):
        if pygame.mixer.music.get_busy() and not self.is_dragging:
            current_sec = self.start_offset + (pygame.mixer.music.get_pos() / 1000)
            if current_sec > self.song_length:
                current_sec = self.song_length
            self.progress_slider.set(current_sec)
            current_time_str = time.strftime('%M:%S', time.gmtime(current_sec))
            total_time_str = time.strftime('%M:%S', time.gmtime(self.song_length))
            self.time_label.configure(text=f"{current_time_str} / {total_time_str}")
        self.after(1000, self.update_progress_bar)

    def toggle_mode(self):
        if self.play_mode == 0:
            self.play_mode = 1
            self.mode_button.configure(text="单曲循环")
            self.show_message("已切换到单曲循环模式")
        else:
            self.play_mode = 0
            self.mode_button.configure(text="列表循环")
            self.show_message("已切换到列表循环模式")

    def play_next(self):
        if not self.song_list or self.current_song is None:
            return
        try:
            idx = self.song_list.index(self.current_song)
        except ValueError:
            idx = -1
        if self.play_mode == 1:
            next_idx = idx
        else:
            next_idx = (idx + 1) % len(self.song_list)
        self.paly_music(self.song_list[next_idx])

    def check_for_end(self):
        for event in pygame.event.get():
            if event.type == self.MUSIC_END_EVENT:
                self.show_message("检测到歌曲结束/切歌，正在切歌...")
                self.play_next()
                pygame.event.clear()
        self.after(100, self.check_for_end)

    def paly_music(self,file_path):
        pygame.event.clear()
        try:
            audio = MP3(file_path)
            self.song_length = audio.info.length
            self.progress_slider.configure(to=self.song_length)
            self.progress_slider.set(0)
            self.start_offset=0
            pygame.mixer.music.stop()
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            self.current_song = file_path
            self.is_paused = False
            self.play_button.configure(text="暂停播放")
        except Exception as e:
            self.show_message(f"播放音乐时发生错误：{e}",is_error=True)


    # 写到这里保存历史记录累了 直接vibe coding了 稍微改了一下报错显示
    def save_history(self):
        """将当前的歌单数据剥离 UI 控件，保存为纯文本的 JSON"""
        # 我们不能保存 button 这种 UI 控件，只能保存文本路径
        data_to_save = {}
        for folder_name, data_dict in self.all_playlists.items():
            data_to_save[folder_name] = data_dict["songs"]
            
        try:
            with open("playlist_history.json", "w", encoding="utf-8") as f:
                # ensure_ascii=False 保证中文不会变成乱码，indent=4 让 json 文件排版好看
                json.dump(data_to_save, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self.show_message(f"保存历史记录失败: {e}")

    def load_history(self):
        """软件启动时，读取本地 JSON 并还原歌单界面"""
        if not os.path.exists("playlist_history.json"):
            return # 如果没找历史文件（比如第一次打开软件），就算了
            
        try:
            with open("playlist_history.json", "r", encoding="utf-8") as f:
                history_data = json.load(f)
                
            # 遍历读取到的历史数据，自动把它们“画”回界面上
            for folder_name, songs_list in history_data.items():
                
                # 1. 还原标题按钮
                header_btn = ctk.CTkButton(
                    self.main_playlist_frame, 
                    text=f"📁 {folder_name}", 
                    anchor="w",
                    fg_color="#3B3B3B",        
                    hover_color="#4A4A4A",
                    command=lambda name=folder_name: self.toggle_playlist(name)
                )
                header_btn.pack(fill="x", padx=5, pady=(10, 0))

                # 2. 还原歌曲容器
                song_container = ctk.CTkFrame(self.main_playlist_frame, fg_color="transparent")
                song_container.pack(fill="x", padx=20, pady=0)

                # 3. 填入数据字典
                self.all_playlists[folder_name] = {
                    "header": header_btn,
                    "frame": song_container,
                    "songs": songs_list, # 直接用读出来的路径列表
                    "is_expanded": True
                }

                for full_path in songs_list:
                    filename = os.path.basename(full_path)
                    s_btn = ctk.CTkButton(
                        song_container,
                        text=f"  🎵 {filename}",
                        anchor="w",
                        fg_color="transparent",
                        height=28,
                        command=lambda p=full_path: self.paly_music(p)
                    )
                    s_btn.pack(fill="x", padx=10, pady=2)
                    
        except Exception as e:
            self.show_message(f"读取历史记录失败: {e}")


        
if __name__ == "__main__":
    app = Music()
    app.mainloop()