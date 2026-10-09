from PySide6.QtCore import QObject,Signal
import urllib.request
import threading
from concurrent.futures import ThreadPoolExecutor


class ThumbnailFetcher(QObject):
    
    thumbnail_changed=Signal(bytes)
    
    list_thumbnail_changed=Signal(bytes,str)
    
    playlist_thumbnail_changed=Signal(bytes,str)
    
    def __init__(self, queue):
            super().__init__()
            self._queue = queue
            self._queue.song_data.connect(self.download_thumbnail)
            self.download_list_thumbnail_executor=ThreadPoolExecutor(max_workers=5)
            self._list_thumbnail_lock = threading.Lock()
            self._list_thumbnail_loaded = set()
            self._list_thumbnail_pending = set()

    
    def download_thumbnail(self,song):
        if song.get("thumbnails"):
            url=song["thumbnails"][-1]["url"]
            get_thumbnail=threading.Thread(target=self.fetch_thumbnail,daemon=True,args=(url,))
            get_thumbnail.start()

    def fetch_thumbnail(self,url):
        try:
            url = url.replace("=w60-h60", "=w400-h400").replace("=w120-h120", "=w400-h400")
            with urllib.request.urlopen(url, timeout=5) as response:
                data=response.read()
                self.thumbnail_changed.emit(data)
        except Exception as e:
            print("Error fetching thumbnail:", e)
            
    def download_list_thumbnail(self,song):
            song_id = song.get("id")
            if song_id and song.get("thumbnails"):
                with self._list_thumbnail_lock:
                    if song_id in self._list_thumbnail_loaded or song_id in self._list_thumbnail_pending:
                        return
                    self._list_thumbnail_pending.add(song_id)
                self.download_list_thumbnail_executor.submit(self.list_thumbnail,song)
    
    def list_thumbnail(self,song):
        song_id = song.get("id")
        try:
            url=song["thumbnails"][-1]["url"]
            url = url.replace("=w60-h60", "=w60-h60").replace("=w120-h120", "=w60-h60")
            with urllib.request.urlopen(url, timeout=5) as response:
                data=response.read()
            with self._list_thumbnail_lock:
                self._list_thumbnail_loaded.add(song_id)
            self.list_thumbnail_changed.emit(data,song_id)
        except Exception as e:
            print("Error fetching thumbnail:", e)
        finally:
            with self._list_thumbnail_lock:
                self._list_thumbnail_pending.discard(song_id)
            
    def download_playlist_thumbnail(self,playlist):
        if playlist.get("thumbnails"):
            get_thumbnail=threading.Thread(target=self.playlist_thumbnail,daemon=True,args=(playlist,))
            get_thumbnail.start()
    
    def playlist_thumbnail(self,playlist):
            try:
                url=playlist["thumbnails"][-1]["url"]
                url = url.replace("=w60-h60", "=w80-h80").replace("=w120-h120", "=w80-h80")
                with urllib.request.urlopen(url, timeout=5) as response:
                    data=response.read()
                    self.playlist_thumbnail_changed.emit(data,playlist["playlistId"])
            except Exception as e:
                print("Error fetching thumbnail:", e)
    
    