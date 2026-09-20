import json
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout,QTabWidget,QMessageBox,QDialog,QFileDialog
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt,QTimer,Qt,Signal,QObject,QSettings
import PlayerTab,LibraryTab,Network,Motor,Queue,Player,sys,Login,DownloadTab,DownloadQueue
import threading
import os
from yt_dlp.utils import DownloadCancelled

                
class MainWindow(QObject):
    fetched_playlist=Signal(bool,list)
    search_completed=Signal(object)
    progress_signal=Signal(dict)
    # En __init__ de MainWindow, añade una señal nueva:
    similar_songs_fetched = Signal(list)
    def __init__(self):
        super().__init__()
        self.app=QApplication([])
        self.window=QWidget()
        self.window.setWindowTitle("ReproBabb")
        #self.window.setMaximumSize(300,400)
        self.window.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__),"Assets","Reprobabb.png")))
        styles_file=open(os.path.join(os.path.dirname(__file__),"Styles","styles.Qss"),"r")
        with styles_file  as styles:
            self.app.setStyleSheet(styles.read())
        self.settings=QSettings("Reprobabb","Reprobabb")
        
        self.tab=QTabWidget()
        self.song_timer=QTimer()
        self.song_timer.timeout.connect(self.update_timeline)

        self.download_queue=DownloadQueue.DownloadQueue()
        self.refresh_download_timer=QTimer()
        self.refresh_download_timer.timeout.connect(self.refresh_download)
        self.refresh_download_timer.start(500)
        
        self.search_completed.connect(self.on_search_completed)
        self.fetched_playlist.connect(self.on_playlist_fetched)
        # En __init__, conéctala (fuera del constructor, junto a las demás conexiones):
        
        self.always_on_toggle(False)
        
        self.player_tab=PlayerTab.PlayerTab()
        self.visualizer=self.player_tab.visualizer
        self.volume_slider=self.player_tab.volume_slider
        self.library_tab=LibraryTab.LibraryTab()
        self.player=Player.AudioController()
        self.queue=Queue.SongQueue(self.player)        
        self.thumbnail=Network.ThumbnailFetcher(self.queue)
        self.download_tab=DownloadTab.DownloadTab()
        
        #===============================Connections========================================#
        self.player_tab.play_pause_toggled.connect(self.toggle_play_pause)
        self.player_tab.next_requested.connect(self.next_song_play)
        self.player_tab.previous_requested.connect(self.previous_song_play)
        self.player_tab.time_changed.connect(self.update_current_time_new_slider)
        self.player_tab.volume_changed.connect(self.player.set_volume)
        self.player_tab.shuffle_requested.connect(self.queue.shuffle_queue)
        self.player_tab.play_requested.connect(self.queue.playing_playlist)
        self.player_tab.play_requested.connect(self.get_similar_song_thread)
        self.player_tab.play_next_requested.connect(self.queue.add_to_queue)
        self.player_tab.search_requested.connect(self.search)
        self.player_tab.added_playlist.connect(self.add_song_playlist)
        self.player_tab.download_requested.connect(self.download)
        
        self.player_tab.always_on_toggle.connect(self.always_on_toggle)
        self.tab.addTab(self.player_tab,"Reproducer")
        
        self.library_tab.load_account_requested.connect(self.select_load_account)
        self.library_tab.playlist_content_selected.connect(self.select_user_playlist)
        self.library_tab.playlist_play_requested.connect(self.queue.playing_playlist)
        self.library_tab.song_playlist_delete.connect(self.handle_remove_song)
        self.library_tab.create_browser_requested.connect(self.create_browser)
        self.library_tab.playlist_download_requested.connect(self.download_playlist)
        self.tab.addTab(self.library_tab,"Library")
        
        self.download_tab.cancel_download_requested.connect(self.download_queue.cancel_download)
        self.tab.addTab(self.download_tab,"Downloads")
        
        self.player.error_occurred.connect(self.player_tab.show_error)
        self.player.state_changed.connect(self.update_play_icon)

        
        self.thumbnail.thumbnail_changed.connect(self.player_tab.update_thumbnail)
        self.thumbnail.list_thumbnail_changed.connect(self.list_thumbnails)
        self.thumbnail.playlist_thumbnail_changed.connect(self.list_thumbnails)

        self.queue.song_data.connect(self.player_tab.update_title_artist)
        self.queue.change_shuffle.connect(self.change_shuffle)
        self.queue.update_queue.connect(self.update_queue_in_ui)
        self.similar_songs_fetched.connect(self.queue.add_multiple_to_queue)

        
        
        self.general_vlayout=QVBoxLayout()
        self.general_vlayout.addWidget(self.tab)
        self.window.setLayout(self.general_vlayout)
        self.try_auto_login()
        self.app.aboutToQuit.connect(lambda: self.thumbnail.download_list_thumbnail_executor.shutdown(wait=False, cancel_futures=True))
        self.window.show()

    def search(self,search,search_ver):
        
        search_playlist_thread=threading.Thread(target=self.search_process,daemon=True,args=(search,search_ver))
        search_playlist_thread.start()
     
    #before emit the res we check tahta there isn't any new search comparing if the search version is diferent       
    def search_process(self,search,search_version):
        res=Motor.search_bar(search)
        if search_version == self.player_tab.search_version:
            self.search_completed.emit(res)

    def always_on_toggle(self,display):
        self.window.setWindowFlag(Qt.WindowStaysOnTopHint, display)
        self.window.show()

    def change_shuffle(self):
        self.player_tab.shuffle_button.setChecked(False)   
    
    def list_thumbnails(self,image,id):
        lists=(self.player_tab.search_list,self.library_tab.user_playlists_songs,self.library_tab.user_playlists,self.player_tab.queue_list)
        list_image=QPixmap()
        list_image.loadFromData(image)
        list_icon=QIcon(list_image)
        
        for widget_list in lists :
            for i in range (widget_list.count()):
                item = widget_list.item(i)
                song_data = item.data(Qt.UserRole)
                if song_data and (song_data.get("id") == id or song_data.get("playlistId")==id):
                    item.setIcon(list_icon)
                    break
            
    
    def next_song_play(self):
        self.queue.next_or_previous("next")
    
    def previous_song_play(self):
        self.queue.next_or_previous("previous")

    def toggle_play_pause(self):
        self.player.toggle_pause_play()

    def update_play_icon(self,state):
        if state=="Playing":
            self.song_timer.start(300)
            self.tab.setCurrentIndex(0)
        else:
            self.song_timer.stop()
        self.player_tab.update_play_icon(state)

    
    def update_timeline(self):
        duration=self.player.get_length();
        current_time=0
        if duration >0:
            
            current_time=self.player.get_current_time()

            self.player_tab.update_timeline(current_time,duration)

            
    def update_current_time_new_slider(self,new_time):
        self.player.set_actual_time(new_time)
        
    def shuffle(self):
        self.queue.shuffle_queue()

            
    def select_load_account(self,file_path,show_error):
        playlists=[]
        succes=False
        if file_path:
            sesion=Motor.set_account(file_path)
            if sesion:
                self.settings.setValue("saved_session_path",file_path)
                succes=True           
                playlists=Motor.get_user_playlist()
                self.player_tab.update_playlist(playlists)
                for playlist in playlists:
                    self.thumbnail.download_playlist_thumbnail(playlist)
            else:
                if show_error:
                    QMessageBox.critical(
                    self.window,
                    "Sesion Error",
                    "Couldn't sign up, wrong file or expired credentials in the file "
                )
        self.library_tab.display_playlists(playlists,file_path,succes)
    
    def try_auto_login(self):
        saved_path=self.settings.value("saved_session_path","")
        if saved_path and os.path.exists(saved_path):
            self.select_load_account(saved_path,False)
        
    def select_user_playlist(self,playlist):
        playlist_id=playlist.get("playlistId","")
        search_playlist_thread=threading.Thread(target=self.get_user_playlist_data,daemon=True,args=(playlist_id,))
        search_playlist_thread.start()
        
    
    def get_user_playlist_data(self,playlist_id):
        playlist_data=Motor.playlist_data(playlist_id)
        if playlist_data and playlist_data[0]["status"]=="success":
                        self.fetched_playlist.emit(True,playlist_data)
        else:
            playlist_data=[]
            self.fetched_playlist.emit(False,playlist_data)
        
    def on_playlist_fetched(self,playlist_status,playlist_data):
        if playlist_status:
            self.library_tab.display_playlist_songs(playlist_status,playlist_data)
            for song in playlist_data:
                self.thumbnail.download_list_thumbnail(song)

    def on_search_completed(self, res):
        self.player_tab.search_result(res)
        songs = res if isinstance(res, list) else [res]
        for song in songs:
            if isinstance(song, dict) and song.get("status") == "success":
                self.thumbnail.download_list_thumbnail(song)
    
    def add_song_playlist(self,playlist_id,song_data):
        add_song_thread=threading.Thread(target=Motor.add_song_playlist, daemon=True, args=(playlist_id,song_data.get("id","")))
        add_song_thread.start()
    
    def handle_remove_song(self,playlist_id,song_data):
        remove_thread=threading.Thread(target=self.remove_song,daemon=True,args=(playlist_id,song_data))
        remove_thread.start()
    
    def remove_song(self,playlist_id,song_data):
        remove_response=Motor.remove_song_playlist(playlist_id,song_data)
        if remove_response["status"]=="success":
            self.get_user_playlist_data(playlist_id)

    def create_browser(self):
        login_dialog=Login.LoginDialog()
        if login_dialog.exec() == QDialog.Accepted:
            file_path = os.path.abspath("browser.json")
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(login_dialog.headers_dict, f, indent=4)
                self.select_load_account(file_path, True)
            except Exception as e:
                print(f"Error saving session file: {e}")
        
    def download(self,song_data):
        song_id=song_data.get("id","")
        if self.settings.value("download_path", None) is None:
            file_path=QFileDialog.getExistingDirectory(self.window,"Select Download Folder")
            if file_path is None or file_path.strip() == "":
                return
            self.settings.setValue("download_path", file_path)
        else:
            file_path=self.settings.value("download_path", None)

        download_id=self.download_queue.register_download(song_data.get("title",""))

        downlaod_song_thread=threading.Thread(target=self.download_song,daemon=True,args=(song_id,True,file_path,download_id))
        downlaod_song_thread.start()
    
    def download_song(self,song_id,download,destination,download_id):
        self.download_queue.update_status(download_id,"downloading")

        def progress_hook(progress_data):
            if self.download_queue.is_cancelled(download_id):
                raise DownloadCancelled()
            self.download_queue.update_progress(download_id, self.update_progress(progress_data))

        download_response= Motor.fetch(song_id, download, destination, progress_hook=progress_hook)

        if download_response["status"]=="success":
            self.download_queue.update_status(download_id,"finished")
            print(f"Song downloaded successfully to {destination}")
        else:
            if self.download_queue.is_cancelled(download_id):
                self.download_queue.update_status(download_id,"cancelled")
            else:
                self.download_queue.update_status(download_id,"error")
                print(f"Error downloading song: {download_response.get('error', 'Unknown error')}")
            
            
    def update_progress(self,progress_data):
        if progress_data.get('status') == 'downloading':
            try:
                downloaded = progress_data.get('downloaded_bytes', 0)
                total = progress_data.get('total_bytes', 1)
                percentage = int((downloaded / total) * 100)
                self.progress_signal.emit({"percentage": percentage})
                return percentage
            except Exception as e:
                print(f"Error procesando progreso: {e}")
                return 0
        elif progress_data.get('status') == 'finished':
            self.progress_signal.emit({"percentage": 100})
            return 100
        return 0
    
    
    def download_playlist(self,songs,playlist_name):
        if self.settings.value("download_path", None) is None:
            file_path=QFileDialog.getExistingDirectory(self.window,"Select Download Folder")
            if file_path is None or file_path.strip() == "":
                return
            self.settings.setValue("download_path", file_path)
        else:
            file_path=self.settings.value("download_path", None)
        
        playlist_folder=os.path.join(file_path,playlist_name)
        os.makedirs(playlist_folder,exist_ok=True)

        songs_with_ids = []
        for song in songs:
            download_id = self.download_queue.register_download(song.get("title", ""))
            songs_with_ids.append((song, download_id))

        downlaod_song_thread=threading.Thread(target=self.download_playlist_songs,daemon=True,args=(playlist_folder,songs_with_ids))
        downlaod_song_thread.start()
    
    def download_playlist_songs(self,playlist_folder,songs_with_ids):
        for song, download_id in songs_with_ids:
            song_id=song.get("id","")
            self.download_song(song_id,True,playlist_folder,download_id)

    def refresh_download(self):
        if self.download_queue.downloads:
            self.download_tab.refresh_downloads(self.download_queue.get_data())
            
    def update_queue_in_ui(self,songs):
        self.player_tab.update_queue_list(songs)
        for song in songs:
            if isinstance(song, dict) and song.get("status") == "success":
                self.thumbnail.download_list_thumbnail(song)
    
    
    def get_similar_song_thread(self,song_data):
        if len(song_data)==1:
            only_song = song_data[0]
            videoId=only_song.get("id")
            search_similar_song=threading.Thread(target=self.get_similar_song,daemon=True,args=(videoId,))
            search_similar_song.start()
        
    def get_similar_song(self,videoId):
        returned_songs=Motor.get_similar_songs(videoId)
        self.similar_songs_fetched.emit(returned_songs)

start=MainWindow()
close=start.app.exec()

sys.exit(close)