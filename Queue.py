from PySide6.QtCore import QObject,Signal,QTimer
import Motor
import threading
import random

class SongQueue(QObject):
    
    song_data = Signal(dict)         
    change_shuffle=Signal()
    
    def __init__(self, player):
        super().__init__()
        self.player = player
        self.current_index=0
        self.songs_list=[]
        self.click_count=0
        self.retry_count=0
        self.timer_click=QTimer()
        self.lock=threading.Lock()
        self.timer_click.setSingleShot(True)
        self.timer_click.timeout.connect(self.process_click)
        self.player.state_changed.connect(self.next_song_queue)
        self.is_shuffle=False
        self.shuffle_song_list=[]
        self.shuffle_current_index=0
        self.fetch_version=0

    def playing_playlist(self, playlist,start_index=0):
        song_to_play=None
        with self.lock:
            self.retry_count=0
            self.is_shuffle=False
            self.current_index = start_index if 0 <= start_index < len(playlist) else 0
            self.songs_list=playlist
            if len(self.songs_list)>0:
                song=self.songs_list[self.current_index]
                song_to_play=song
        if song_to_play is not None:
            fetch_thread=threading.Thread(target=self.fetch_song,daemon=True,args=(song_to_play,))
            fetch_thread.start()
        self.change_shuffle.emit()
    
    def next_or_previous(self,direction):
        with self.lock:
            if direction == "next":
                self.click_count+=1
            elif direction=="previous":
                self.click_count-=1
        self.timer_click.start(200)
    
    def process_click(self):
        with self.lock:
            if not self.songs_list or self.click_count==0:
                self.click_count=0
                return
            if self.is_shuffle:
                self.shuffle_current_index=(max(0,min(len(self.shuffle_song_list)-1,self.shuffle_current_index+self.click_count)))
                self.current_index=self.shuffle_song_list[self.shuffle_current_index]
            else:
               self.current_index= max(0,min(len(self.songs_list)-1,self.current_index+self.click_count))
            self.click_count=0
            self.retry_count=0
            song=self.get_song_index()
        fetch_thread=threading.Thread(target=self.fetch_song,daemon=True,args=(song,))
        fetch_thread.start()
        

    def next_song_queue(self,state):
        song_to_play=None
        if state=="Ended Media" and not self.timer_click.isActive():
            with self.lock:
                self.increment_index()
                song_to_play=self.get_song_index()
                self.retry_count=0
        elif state=="Cannot Reproduce":
            if self.retry_count < 7:
                with self.lock:
                    song_to_play=self.get_song_index()
                    self.retry_count+=1
            else:
                with self.lock:
                    self.increment_index()
                    song_to_play=self.get_song_index()
                    self.retry_count=0

        if song_to_play != None:
                fetch_thread=threading.Thread(target=self.fetch_song,daemon=True,args=(song_to_play ,))
                fetch_thread.start()
    
    def fetch_song(self, song):
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
                with self.lock:
                    self.increment_index()
                    song=self.get_song_index()
    
    def shuffle_queue(self):
        with self.lock:
            self.is_shuffle=not self.is_shuffle
            if self.is_shuffle:
                if not self.songs_list:
                    self.shuffle_song_list = []
                    self.shuffle_current_index = 0
                    return
                self.shuffle_song_list=[]
                self.shuffle_song_list=list(range(len(self.songs_list)))
                random.shuffle(self.shuffle_song_list)
                if self.current_index < len(self.songs_list):
                    self.shuffle_current_index=self.shuffle_song_list.index(self.current_index)
                else:
                    self.shuffle_current_index=0
        
    def get_song_index(self):
        if self.is_shuffle:
            if self.shuffle_current_index < len(self.shuffle_song_list):
                index=self.shuffle_song_list[self.shuffle_current_index]
                song=self.songs_list[index]
            else:
                song=None
        else:
            if self.current_index < len(self.songs_list):
                song=self.songs_list[self.current_index]
            else:
                song=None
        return song

    def increment_index(self):
        if self.is_shuffle:
            if self.shuffle_current_index+1 < len(self.shuffle_song_list):
                self.shuffle_current_index+=1
                self.current_index=self.shuffle_song_list[self.shuffle_current_index]
            else:
                self.shuffle_current_index=len(self.shuffle_song_list)
                self.current_index=len(self.songs_list)
        else:
            self.current_index+=1
     
    def add_to_queue(self,song):
        with self.lock:
            insert_index=0
            if self.is_shuffle:
                insert_index=self.shuffle_current_index+1
                self.songs_list.append(song)
                new_song_index=len(self.songs_list)-1
                self.shuffle_song_list.insert(insert_index,new_song_index)
            else:
                insert_index=self.current_index+1
                self.songs_list.insert(insert_index,song)

                
        
