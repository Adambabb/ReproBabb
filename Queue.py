from PySide6.QtCore import QObject,Signal,QTimer
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
        self.clickCount=0
        self.timerClick=QTimer()
        self.timerClick.setSingleShot(True)
        self.timerClick.timeout.connect(self.processClick)
        self.player.state_changed.connect(self.nextPlaylistSong)
        
    def addSong(self, song):
        self.currentIndex=0
        for songs in song:
            self.songsList.append(songs)
            
    def NowPlaylist(self, song):
            self.currentIndex=0
            self.songsList=song
            if len(self.songsList)>0:
                song=self.songsList[self.currentIndex]
                FetchThread=threading.Thread(target=self.fetchSong,daemon=True,args=(song,))
                FetchThread.start()
    
    def nextBefore(self,direction):
        self.direction=direction
        self.clickCount+=1
        self.timerClick.start(200)
    
    def processClick(self):
        if self.direction=="before":
            if self.currentIndex > 0 and self.currentIndex - self.clickCount >= 0:
                self.currentIndex-=self.clickCount
            else:
                self.currentIndex=0
        else:
            if self.currentIndex + self.clickCount < len(self.songsList):
                self.currentIndex+=self.clickCount
            else:
                self.currentIndex=len(self.songsList)-1
        self.clickCount=0
        self.direction=""
        song=self.songsList[self.currentIndex]
        FetchThread=threading.Thread(target=self.fetchSong,daemon=True,args=(song,))
        FetchThread.start()
        

    def nextPlaylistSong(self,state):
        if state=="Ended Song" and not self.timerClick.isActive():
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
        self.song_data.emit(song)
        self.player.play(url)
        
