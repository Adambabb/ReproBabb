from PySide6.QtWidgets import QApplication, QLabel, QWidget, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,QSlider,QMenu
from PySide6.QtGui import QIcon, QPixmap,QAction
import sys,urllib.request
import Player
import Motor
import Queue
from PySide6.QtCore import Qt,QPoint,QObject,Signal,QTimer
import threading
import os

class ThumbnailFetcher(QObject):
    
    thumbnail_changed=Signal(bytes)
    
    def __init__(self, queue):
            super().__init__()
            self._queue = queue
            self._queue.song_data.connect(self.download_thumbnail)

    
    def download_thumbnail(self,song):
        if song["thumbnails"]:
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
    
class MainWindow():
    def __init__(self):
        
        self._app=QApplication([])
        self._player=Player.AudioController()
        self._queue=Queue.SongQueue(self._player)
        self._window=QWidget()
        self._search_version=0
        self._thumbnail=ThumbnailFetcher(self._queue)
        
        self._location=os.path.dirname(__file__)
        self._window.setWindowTitle("ReproBabb")
        self._window.setFixedSize(500,600)
        self._window.setWindowIcon(QIcon(self.program_location("ReproBabb.png")))
    
        vertical_layout=QVBoxLayout()
        search_settings_layout=QHBoxLayout()
        
        self._search_box=QLineEdit()
        search_settings_layout.addWidget(self._search_box)

        search_button=QPushButton("search")
        search_settings_layout.addWidget(search_button)
        search_button.clicked.connect(self.click_search)


        settings_button=QPushButton()
        ico_settings=QIcon(self.program_location("Settings.png"))
        settings_button.setIcon(ico_settings)
        search_settings_layout.addWidget(settings_button)
        settings_button.clicked.connect(self.settings_menu)
        
        vertical_layout.addLayout(search_settings_layout)
        
        self._thumbnail_label=QLabel()
        self._thumbnails=QPixmap(self.program_location("Vinyl-Cover.png"))
        self._thumbnail_label.setPixmap(self._thumbnails)
        self._thumbnail.thumbnail_changed.connect(self.update_thumbnail)
        thumbnail_layout=QHBoxLayout()
        thumbnail_layout.addStretch()
        thumbnail_layout.addWidget(self._thumbnail_label)
        thumbnail_layout.addStretch()
        
        vertical_layout.addLayout(thumbnail_layout)
         
        self.time_layout=QHBoxLayout()
        
        self.time_slider=QSlider(Qt.Horizontal)
        self.current_time_label=QLabel()
        self.current_time_label.setText("00:00")
        self.total_time_label=QLabel()
        self.total_time_label.setText("00:00")
        self.time_layout.addWidget(self.current_time_label)
        self.time_layout.addWidget(self.time_slider)
        self.time_layout.addWidget(self.total_time_label)
        
        vertical_layout.addLayout(self.time_layout)
        
        self._song_timer=QTimer()
        self._song_timer.timeout.connect(self.update_timeline)
        self.time_slider.sliderReleased.connect(self.update_current_time)
        
        volume_slider=QSlider(Qt.Horizontal)
        volume_slider.setMaximum(100)
        volume_slider.setMinimum(0)
        volume_slider.setValue(50)
        volume_slider.valueChanged.connect(self._player.set_volume)
        volume_layout=QHBoxLayout()
        volume_layout.addWidget(volume_slider)
        
        vertical_layout.addLayout(volume_layout)
        
        controllers_layout=QHBoxLayout()
        
        previous_song=QPushButton()
        self._ico_previous=QIcon(self.program_location("Previous.png"))
        previous_song.setIcon(self._ico_previous)
        controllers_layout.addWidget(previous_song)   
        
        previous_song.clicked.connect(self.previous_song_play)

        self.pause=QPushButton()
        self._ico_pause_play=QIcon(self.program_location("Play.png"))
        self.pause.setIcon(self._ico_pause_play)
        controllers_layout.addWidget(self.pause)

        self.pause.clicked.connect(self.toggle_play_pause)       
        self._player.state_changed.connect(self.update_play_icon)


        next_song=QPushButton()
        self._ico_next=QIcon(self.program_location("Next.png"))
        next_song.setIcon(self._ico_next)        
        controllers_layout.addWidget(next_song)
        
        next_song.clicked.connect(self.next_song_play)
        
        vertical_layout.addLayout(controllers_layout)
        
        

        self.settings=QMenu()
        self.visible=QAction("Always Visible")
        self.visible.setCheckable(True)
        self.visible.setChecked(True)
        self.settings.addAction(self.visible)
        self.visible.toggled.connect(self.always_on_toggle)
        
        self.always_on_toggle(True)
        self._window.setLayout(vertical_layout)
        self._window.show()
        
    def program_location(self,asset_name):
        return os.path.join(self._location,"Assets",asset_name)


    def click_search(self):
        search=self._search_box.text()
        self._search_version+=1
        search_thread=threading.Thread(target=self.search_process,daemon=True,args=(search,self._search_version))
        search_thread.start()
        
    def search_process(self,search,search_version):
        res=Motor.search_bar(search)
        if search_version == self._search_version:
                    self.search_result(res)

    def search_result(self,res):
        if isinstance(res,list):
            if res[0]["status"] !="error":
                self._queue.playing_playlist(res)
        elif isinstance(res,dict):
            if res["status"] !="error":
                songs=[res]
                self._queue.playing_playlist(songs)

    def settings_menu(self):
        self.settings.exec(self._window.mapToGlobal(QPoint(self._window.width()//2-self.settings.sizeHint().width()//2,self._window.height()//2-self.settings.sizeHint().height()//2)))


    def always_on_toggle(self,display):
        self._window.setWindowFlag(Qt.WindowStaysOnTopHint, display)
        self._window.show()


    def update_thumbnail(self,data):
        cover=QPixmap()
        cover.loadFromData(data)
        if cover.isNull():
            cover=QPixmap(self.program_location("Vinyl-Cover.png"))
        self._thumbnail_label.setPixmap(cover)

   
    def next_song_play(self):
        self._queue.next_or_previous("next")
    
    def previous_song_play(self):
        self._queue.next_or_previous("previous")

    def toggle_play_pause(self):
        self._player.toggle_pause_play()

    def update_play_icon(self,state):
        if state=="Playing":
            ico_pause_play=QIcon(self.program_location("Pause.png"))
            self.pause.setIcon(ico_pause_play)
            self._song_timer.start(300)
        else:
            ico_pause_play=QIcon(self.program_location("Play.png"))
            self.pause.setIcon(ico_pause_play)
            self._song_timer.stop()

    
    def update_timeline(self):
        duration=self._player.get_length();
        if duration >0:
            
            self.time_slider.setMaximum(duration)
            current_time=self._player.get_current_time()
            if not self.time_slider.isSliderDown():
                self.time_slider.setValue(current_time)
            current_time_mins=(current_time//1000)//60
            current_time_seconds=(current_time//1000)%60
            
            formated_time=f"{current_time_mins:02d}:{current_time_seconds:02d}"
            self.current_time_label.setText(formated_time)
            
            total_time_mins=(duration//1000)//60
            total_time_seconds=(duration//1000)%60
            formated_total_time=f"{total_time_mins:02d}:{total_time_seconds:02d}"
            self.total_time_label.setText(formated_total_time)
        else:
            self.time_slider.setMaximum(0)

    def update_current_time(self):
        self._player.set_actual_time(self.time_slider.value())
    
start=MainWindow()
close=start._app.exec()

sys.exit(close)
