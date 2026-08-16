from PySide6.QtCore import QObject,Signal
import urllib.request
import threading


class ThumbnailFetcher(QObject):
    
    thumbnail_changed=Signal(bytes)
    
    list_thumbnail_changed=Signal(bytes,str)
    
    def __init__(self, queue):
            super().__init__()
            self._queue = queue
            self._queue.song_data.connect(self.download_thumbnail)

    
    def download_thumbnail(self,song):
        if song.get("thumbnails"):
            url=song["thumbnails"][-1]["url"]
            get_thumbnail=threading.Thread(target=self.fetch_thumbnail,daemon=True,args=(url,))
            get_thumbnail.start()

    def fetch_thumbnail(self,url):
        try:
            url = url.replace("=w60-h60", "=w400-h400").replace("=w120-h120", "=w400-h400")
            with urllib.request.urlopen(url) as response:
                data=response.read()
                self.thumbnail_changed.emit(data)
        except Exception as e:
            print("Error fetching thumbnail:", e)
    
    def download_list_thumbnail(self,song):
            if song.get("thumbnails"):
                get_thumbnail=threading.Thread(target=self.list_thumbnail,daemon=True,args=(song,))
                get_thumbnail.start()
    
    def list_thumbnail(self,song):
        try:
            url=song["thumbnails"][-1]["url"]
            url = url.replace("=w60-h60", "=w40-h40").replace("=w120-h120", "=w40-h40")
            with urllib.request.urlopen(url) as response:
                data=response.read()
                self.list_thumbnail_changed.emit(data,song["id"])
        except Exception as e:
            print("Error fetching thumbnail:", e)