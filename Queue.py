from PySide6.QtCore import QObject,Signal,QTimer
import Motor
import threading
import random

class SongQueue(QObject):
    
    song_data = Signal(dict)         

    def __init__(self, player):
        super().__init__()
        self.player = player
        self._current_index=0
        self._songs_list=[]
        self._direction=""
        self._click_count=0
        self._timer_click=QTimer()
        self._lock=threading.Lock()
        self._timer_click.setSingleShot(True)
        self._timer_click.timeout.connect(self.process_click)
        self.player.state_changed.connect(self.next_song_queue)
        self._is_shuffle=False
        self._shuffle_song_list=[]
        self._shuffle_current_index=0
        self.fetch_version=0

    def playing_playlist(self, playlist):
        song_to_play=None
        with self._lock:
            self._is_shuffle=False
            self._current_index=0
            self._songs_list=playlist
            if len(self._songs_list)>0:
                song=self._songs_list[self._current_index]
                song_to_play=song
        if song_to_play != None:
            fetch_thread=threading.Thread(target=self._fetch_song,daemon=True,args=(song_to_play,))
            fetch_thread.start()
    
    def next_or_previous(self,direction):
        with self._lock:
            self._direction=direction
            self._click_count+=1
        self._timer_click.start(200)
    
    def process_click(self):
        with self._lock:
            if not self._songs_list:
                self._click_count=0
                
                self._direction=""
                return
            if self._is_shuffle:
                if self._direction=="previous":
                    if self._shuffle_current_index > 0 and self._shuffle_current_index - self._click_count >= 0:
                        self._shuffle_current_index-=self._click_count
                        self._current_index=self._shuffle_song_list[self._shuffle_current_index]  
                    else:
                        self._shuffle_current_index=0
                        self._current_index=self._shuffle_song_list[self._shuffle_current_index]  
                else:
                    if self._shuffle_current_index + self._click_count < len(self._shuffle_song_list):
                        self._shuffle_current_index+=self._click_count
                        self._current_index=self._shuffle_song_list[self._shuffle_current_index]  
                    else:
                        self._shuffle_current_index=len(self._shuffle_song_list)-1
                        self._current_index=self._shuffle_song_list[self._shuffle_current_index]
            else:
                if self._direction=="previous":
                    if self._current_index > 0 and self._current_index - self._click_count >= 0:
                        self._current_index-=self._click_count  
                    else:
                        self._current_index=0
                else:
                    if self._current_index + self._click_count < len(self._songs_list):
                        self._current_index+=self._click_count
                    else:
                        self._current_index=len(self._songs_list)-1
            self._click_count=0
            self._direction=""
            song=self._songs_list[self._current_index]
        fetch_thread=threading.Thread(target=self._fetch_song,daemon=True,args=(song,))
        fetch_thread.start()
        

    def next_song_queue(self,state):
        song_to_play=None
        if state=="Ended Media" and not self._timer_click.isActive():
            with self._lock:
                if self._is_shuffle:
                    if self._shuffle_current_index+1 < len(self._shuffle_song_list) :
                        self._shuffle_current_index+=1
                        self._current_index= self._shuffle_song_list[self._shuffle_current_index]
                    else:
                        song_to_play=None
                        self._shuffle_current_index=len(self._shuffle_song_list)
                        self._current_index=self._shuffle_current_index
                else:
                    self._current_index+=1
                if self._current_index < len(self._songs_list):
                    song= self._songs_list[self._current_index]
                    song_to_play=song
        if song_to_play != None:
                fetch_thread=threading.Thread(target=self._fetch_song,daemon=True,args=(song_to_play ,))
                fetch_thread.start()
    
    def _fetch_song(self, song):
        self.fetch_version+=1
        current_fetch_version=self.fetch_version
        while song is not None:
            status_fetch=Motor.fetch(song["id"])
            if current_fetch_version != self.fetch_version:
                break
            if status_fetch["status"]=="success":
                url=status_fetch["url"]
                self.song_data.emit(song)
                self.player.play(url)
                song=None
            else:
                error=status_fetch["error"]
                print("Error:", error)
                song=None
                with self._lock:
                    if self._is_shuffle:
                        self._shuffle_current_index+=1
                        if self._shuffle_current_index < len(self._shuffle_song_list):
                            self._current_index= self._shuffle_song_list[self._shuffle_current_index]
                            song=self._songs_list[self._current_index]
                        else:
                            self._shuffle_current_index=len(self._shuffle_song_list)
                            self._current_index=self._shuffle_current_index
                    else:
                        self._current_index+=1
                        if self._current_index < len(self._songs_list):
                            song= self._songs_list[self._current_index]
                        
    
    def shuffle_queue(self):
        with self._lock:
            self._is_shuffle=not self._is_shuffle
            if self._is_shuffle:
                if not self._songs_list:
                    self._shuffle_song_list = []
                    self._shuffle_current_index = 0
                    return
                self._shuffle_song_list=[]
                self._shuffle_song_list=list(range(len(self._songs_list)))
                random.shuffle(self._shuffle_song_list)
                if self._current_index < len(self._songs_list):
                    self._shuffle_current_index=self._shuffle_song_list.index(self._current_index)
                else:
                    self._shuffle_current_index=0
