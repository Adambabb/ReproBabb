from PySide6.QtCore import QObject,Signal
import Motor;
import threading;

class SongQueue(QObject):
    
    song_data = Signal(dict)         

    def __init__(self, player):
        super().__init__()
        self.player = player
        self.currentIndex=0
        self.songsList=[]
        self.direction=""
        self.player.state_changed.connect(self.nextPlaylistSong)
        
    def addSong(self, song):
        self.currentIndex=0
        for songs in song:
            self.songsList.append(songs)
            
    def NowPlaylist(self, song):
            self.currentIndex=0
            self.songsList=song
    
    def nextBefore(self,direction):
        self.direction=direction
        self.player.stop()
        
    
    def nextPlaylistSong(self,state):
        if state=="Ended Song" or state=="Song Stopped":
            if self.direction=="before":
                if self.currentIndex > 0:
                    self.currentIndex-=1
            else:
                self.currentIndex+=1
            self.direction=""
            if self.currentIndex < len(self.songsList):
                song= self.songsList[self.currentIndex]
                FetchThread=threading.Thread(target=self.fetchSong,daemon=True,args=(song,))
                FetchThread.start()
    
    def fetchSong(self, song):
        url=Motor.fetch(song["id"])
        self.player.play(url)
        
