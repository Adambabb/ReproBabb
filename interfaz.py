from PySide6.QtWidgets import QApplication, QLabel, QWidget, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,QSlider,QMenu
from PySide6.QtGui import QIcon, QPixmap,QAction;
import sys,urllib.request
import Player;
import Motor;
import Queue;
from PySide6.QtCore import Qt,QTimer,QPoint,QUrl;
import threading;

lock=threading.Lock();

class Start():
    def __init__(self,):
        self._app=QApplication([])
        self._player=Player.AudioController();
        self._queue=Queue.SongQueue(self._player)
        self._window=QWidget()
        self._searchVer=0




start=Start();


def clickSearch():
    search=searchBox.text()
    start._searchVer+=1
    SearchThread=threading.Thread(target=searchMotor,daemon=True,args=(search,start._searchVer))
    SearchThread.start()
    
def searchMotor(search,searchVer):
    res=Motor.searchBar(search)
    if searchVer == start._searchVer:
                fetching=threading.Thread(target=fetchSong,daemon=True,args=(res,))
                fetching.start()

def fetchSong(res):
    if isinstance(res,list):
        if res[0]["status"] !="error":
            start._queue.NowPlaylist(res)
            url=Motor.fetch(res[0]["id"])
            start._player.play(url)
    elif isinstance(res,dict):
        if res["status"] !="error":
            songs=[res]
            start._queue.NowPlaylist(songs)
            url=Motor.fetch(res["id"])
            start._player.play(url)


start._window.setWindowTitle("ReproBabb")
start._window.setFixedSize(500,600)

Horizontal=QHBoxLayout();
PrinVertical=QVBoxLayout();

HorizontalButton=QHBoxLayout();


searchBox=QLineEdit();
searchButton=QPushButton("search");
searchButton.clicked.connect(clickSearch);


def Sett():
    settings.exec(start._window.mapToGlobal(QPoint(250-settings.sizeHint().width()//2,300-settings.sizeHint().height()//2)));


settingsButt=QPushButton();
icoSettings=QIcon("./Assets/Settings.png")
settingsButt.setIcon(icoSettings)
settingsButt.clicked.connect(Sett)



def AlwaysOn(display):
    if display==True:
        start._window.setWindowFlags(start._window.windowFlags()|Qt.WindowStaysOnTopHint)
    else:
        start._window.setWindowFlags(start._window.windowFlags()& ~Qt.WindowStaysOnTopHint)
    start._window.show()

settings=QMenu()
visible=QAction("Always Visible");
visible.setCheckable(True)
visible.setChecked(True)
settings.addAction(visible)
visible.toggled.connect(AlwaysOn);

Horizontal.addWidget(searchBox)
Horizontal.addWidget(searchButton)
Horizontal.addWidget(settingsButt)

thumbnailLabel=QLabel();
thumbnail=QPixmap("./Assets/Next.png")
thumbnailLabel.setPixmap(thumbnail)
HorizontalThumbnail=QHBoxLayout();
HorizontalThumbnail.addStretch();
HorizontalThumbnail.addWidget(thumbnailLabel)


nextSong=QPushButton()
icoNext=QIcon("./Assets/Next.png")
nextSong.setIcon(icoNext)

def nextSongPlay():
    start._queue.nextBefore("next")

   
nextSong.clicked.connect(nextSongPlay)

beforeSong=QPushButton()
icoBefore=QIcon("./Assets/Before.png")
beforeSong.setIcon(icoBefore)

def beforeSongPlay():
    start._queue.nextBefore("before")

beforeSong.clicked.connect(beforeSongPlay)

    
pause=QPushButton()

def playPause():
    start._player.pausePlay()

def icoPlayPause(state):
    if state=="Playing":
        icoPause=QIcon("./Assets/Pause.png")
        pause.setIcon(icoPause)
    else:
        icoPause=QIcon("./Assets/Play.png")
        pause.setIcon(icoPause)

        
start._player.state_changed.connect(icoPlayPause)
        
pause.clicked.connect(playPause)
icoPause=QIcon("./Assets/Pause.png")
pause.setIcon(icoPause)

vol=QSlider(Qt.Horizontal)
vol.setMaximum(100)
vol.setMinimum(0)
vol.setValue(50)
vol.valueChanged.connect(start._player.set_volume)


HorizontalButton.addWidget(beforeSong)
HorizontalButton.addWidget(pause)
HorizontalButton.addWidget(nextSong)

HorizontalThumbnail.addStretch();

HorizontalVol=QHBoxLayout()
HorizontalVol.addWidget(vol)

PrinVertical.addLayout(Horizontal)
PrinVertical.addLayout(HorizontalThumbnail)
PrinVertical.addLayout(HorizontalVol)
PrinVertical.addLayout(HorizontalButton)


start._window.setLayout(PrinVertical)
start._window.show()
AlwaysOn(True)
close=start._app.exec()

sys.exit(close)
