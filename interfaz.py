from PySide6.QtWidgets import QApplication, QLabel, QWidget, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,QSlider,QMenu
from PySide6.QtGui import QIcon, QPixmap,QAction;
import sys,urllib.request
import Player;
import Motor;
from PySide6.QtCore import Qt,QTimer,QPoint,QUrl;
import threading;
import yt_dlp;

lock=threading.Lock();

class Start():
    def __init__(self,config: dict):
        self._app=QApplication([])
        self._player=Player.AudioController();
        self._config=config
        self._window=QWidget()
        self._searchVer=0



fetcherOpt={
        "format":"bestaudio",
        "noplaylist":True,
        "quiet":False,
    }
start=Start(fetcherOpt);


def fetch(res):
    with yt_dlp.YoutubeDL(fetcherOpt) as fetcher:
        info=fetcher.extract_info(res,download=False)
        url=info["url"]
        start._player.play(url)

def clickSearch():
    search=searchBox.text()
    start._searchVer+=1
    SearchThread=threading.Thread(target=searchMotor,daemon=True,args=(search,start._searchVer))
    SearchThread.start()
    
def searchMotor(search,searchVer):
    res=Motor.searchBar(search)
    if searchVer == start._searchVer:
        if isinstance(res,list):
            if res[0]["status"] !="error":
                fetching=threading.Thread(target=fetch,daemon=True,args=(res[0]["id"],))
                fetching.start()
        elif isinstance(res,dict):
            if res["status"] !="error":
                fetching=threading.Thread(target=fetch,daemon=True,args=(res["id"],))
                fetching.start()

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

beforeSong=QPushButton()
icoBefore=QIcon("./Assets/Before.png")
beforeSong.setIcon(icoBefore)



    
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
