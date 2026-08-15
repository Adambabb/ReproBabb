from PySide6.QtWidgets import QApplication, QLabel, QWidget, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,QSlider,QMenu,QSizePolicy
from PySide6.QtGui import QIcon, QPixmap,QAction,QShortcut,QKeySequence,QColor,QPainter
import sys,urllib.request
import Player
import Motor
import Queue
from PySide6.QtCore import Qt,QPoint,QObject,Signal,QTimer,QPointF
import threading
import os
import random

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
            
class time_design(QWidget):
    
    time_changed=Signal(int)
    
    def __init__(self,cover_color,song_duration,song_current_time):
        super().__init__()
        self.bars_number=0
        self.bars_height=[0 for i  in range(140) ]
        self.bars_height_timer=QTimer()
        self.bars_height_timer.timeout.connect(self.update_heights)
        self.bar_gap=0
        self.bars_wave=0.0
        self.song_duration=0
        self.song_current_time=0
        self.cover_color=cover_color
        self.cover_color_contrary=cover_color
        self.is_dragging=False
        self.setMinimumHeight(50)
    
    def update_heights(self):
        self.bars_height=[random.uniform(0.1,0.9) for i  in range(140) ]
        self.update()
    
    
    def paintEvent(self,event):
        visaulizer=QPainter(self)
        visaulizer.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.width() >= 800:
            self.bars_number=140
            self.bar_gap=2
        elif self.width() >= 400:
            self.bars_number=70
            self.bar_gap=2
        elif self.width() >= 200:
            self.bars_number=50
            self.bar_gap=2
        else:
            self.bars_number=20
            self.bar_gap=1
        bar_width=(self.width()/self.bars_number)-self.bar_gap
        self.bars_number_color=0
        if self.song_duration >0:
            percent_song_duration=self.song_current_time/self.song_duration
            self.bars_number_color=self.bars_number*percent_song_duration
        for i in range(self.bars_number):
            position_x=i*(bar_width+self.bar_gap)
            bar_pixel_height=self.height() * self.bars_height[i]
            position_y=self.height()-(bar_pixel_height)
            if self.bars_number_color >= i:
                visaulizer.setPen(Qt.PenStyle.NoPen)
                visaulizer.setBrush(self.cover_color)
            else:
                cover_color_alpha=QColor(self.cover_color)
                cover_color_alpha.setAlpha(75)
                visaulizer.setPen(Qt.PenStyle.NoPen)
                visaulizer.setBrush(cover_color_alpha)
            visaulizer.drawRect(position_x,position_y,bar_width,bar_pixel_height)
        if self.song_duration >0:
            round_slider_x=self.width()*(self.song_current_time/self.song_duration)
        else:
            round_slider_x=0
        round_slider_y=self.height()-6
        visaulizer.setPen(Qt.PenStyle.NoPen)
        
        visaulizer.setBrush(self.cover_color_contrary)
        visaulizer.drawEllipse(QPointF(round_slider_x,round_slider_y),6,6)
    
    def mousePressEvent(self, event):
        self.is_dragging=True
        click_x=event.position().x()
        round_slider_percent=click_x/self.width()
        round_slider_new_time=int(round_slider_percent*self.song_duration)
        self.song_current_time=round_slider_new_time
        self.update()
        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        round_slider_new_time=0
        if self.is_dragging==True:
            if event.position().x() > 0 and event.position().x() < self.width():
                click_x=event.position().x()
            else:
                click_x=max(0,min(event.position().x(),self.width()))
            round_slider_percent=click_x/self.width()
            round_slider_new_time=int(round_slider_percent*self.song_duration)
            self.song_current_time=round_slider_new_time
            self.update()
        return super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        self.is_dragging=False
        
        self.time_changed.emit(self.song_current_time)
        return super().mouseReleaseEvent(event)


                
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
        self._window.resize(500,600)
        self._window.setWindowIcon(QIcon(self.program_location("ReproBabb.png")))
    
        vertical_layout=QVBoxLayout()
        search_settings_layout=QHBoxLayout()
        
        self._search_box=QLineEdit()
        search_settings_layout.addWidget(self._search_box)
        self._search_box.returnPressed.connect(self.click_search)
        
        search_button=QPushButton("search")
        search_settings_layout.addWidget(search_button)
        search_button.clicked.connect(self.click_search)

        settings_button=QPushButton()
        ico_settings=QIcon(self.program_location("Settings.png"))
        settings_button.setIcon(ico_settings)
        search_settings_layout.addWidget(settings_button)
        settings_button.clicked.connect(self.settings_menu)
        
        vertical_layout.addLayout(search_settings_layout,1)
        
        self._thumbnail_label=QLabel()
        self._thumbnail_label.setScaledContents(True)
        self._thumbnail_label.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding)
        self.cover=QPixmap(self.program_location("Vinyl-Cover.png"))
        self._thumbnail_label.setPixmap(self.cover)
        self._thumbnail.thumbnail_changed.connect(self.update_thumbnail)
        self.cover_color=QColor()
        self._thumbnail_label.setMinimumSize(100,100)
        thumbnail_layout=QHBoxLayout()
        thumbnail_layout.addStretch()
        thumbnail_layout.addWidget(self._thumbnail_label)
        thumbnail_layout.addStretch()

        vertical_layout.addLayout(thumbnail_layout,6)
        
        self.current_time_label=QLabel("00:00")
        
        self.visualizer = time_design(self.cover_color, 0, 0)
        
        self.total_time_label=QLabel("00:00")
        self.current_time_label = QLabel("00:00")
        self.total_time_label = QLabel("00:00")

        time_layout=QHBoxLayout()
        
        time_layout.addWidget(self.current_time_label,0)
        time_layout.addWidget(self.visualizer,1)
        time_layout.addWidget(self.total_time_label,0)
        vertical_layout.addLayout(time_layout)
        self.visualizer.time_changed.connect(self.update_current_time_new_slider)
        


        self._song_timer=QTimer()
        self._song_timer.timeout.connect(self.update_timeline)
        
        self.volume_slider=QSlider(Qt.Horizontal)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self._player.set_volume)
        volume_layout=QHBoxLayout()
        volume_layout.addWidget(self.volume_slider,1)
        
        self.shortcut_volume_up = QShortcut(QKeySequence("Up"), self._window)
        self.shortcut_volume_up.activated.connect(self.volume_up)
        
        self.shortcut_volume_down = QShortcut(QKeySequence("Down"), self._window)
        self.shortcut_volume_down.activated.connect(self.volume_down)
        
        vertical_layout.addLayout(volume_layout,1)
        
        controllers_layout=QHBoxLayout()
        
        previous_song=QPushButton()
        self._ico_previous=QIcon(self.program_location("Previous.png"))
        previous_song.setIcon(self._ico_previous)
        controllers_layout.addWidget(previous_song)   
        
        self.shortcut_previous_song = QShortcut(QKeySequence("Left"), self._window)
        self.shortcut_previous_song.activated.connect(self.previous_song_play)
        
        previous_song.clicked.connect(self.previous_song_play)

        self.pause=QPushButton()
        self._ico_pause_play=QIcon(self.program_location("Play.png"))
        self.pause.setIcon(self._ico_pause_play)
        controllers_layout.addWidget(self.pause)

        self.pause.clicked.connect(self.toggle_play_pause)       
        self._player.state_changed.connect(self.update_play_icon)
        
        self.shortcut_pause_play = QShortcut(QKeySequence("Space"), self._window)
        self.shortcut_pause_play.activated.connect(self.toggle_play_pause)
        
        next_song=QPushButton()
        self._ico_next=QIcon(self.program_location("Next.png"))
        next_song.setIcon(self._ico_next)        
        controllers_layout.addWidget(next_song)
        
        self.shortcut_next_song = QShortcut(QKeySequence("Right"), self._window)
        self.shortcut_next_song.activated.connect(self.next_song_play)
        
        next_song.clicked.connect(self.next_song_play)
        
        self.shuffle_button=QPushButton()
        self.shuffle_button.setCheckable(True)
        self.shuffle_icon=QIcon(self.program_location("Shuffle.png"))
        self.shuffle_button.setIcon(self.shuffle_icon)
        self.shuffle_button.clicked.connect(self.shuffle)
        
        controllers_layout.addWidget(self.shuffle_button)
                
        vertical_layout.addLayout(controllers_layout,1)
        
        

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
        self.shuffle_button.setChecked(False)
        
    def settings_menu(self):
        self.settings.exec(self._window.mapToGlobal(QPoint(self._window.width()//2-self.settings.sizeHint().width()//2,self._window.height()//2-self.settings.sizeHint().height()//2)))


    def always_on_toggle(self,display):
        self._window.setWindowFlag(Qt.WindowStaysOnTopHint, display)
        self._window.show()


    def update_thumbnail(self,data):
        self.cover=QPixmap()
        self.cover.loadFromData(data)
        if self.cover.isNull():
                   self.cover=QPixmap(self.program_location("Vinyl-Cover.png")) 
        self._thumbnail_label.setPixmap(self.cover)
        cover_scaled=self.cover.toImage()
        cover_scaled=cover_scaled.scaled(1,1)
        self.cover_color=cover_scaled.pixelColor(0,0)
        self.visualizer.cover_color=self.cover_color
        h,s,v,a=self.cover_color.getHsv()
        h=(h+180)%360
        self.visualizer.cover_color_contrary=QColor.fromHsv(h,s,v,a)
        self.visualizer.update()
   
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
            self.visualizer.bars_height_timer.start(50)
        else:
            ico_pause_play=QIcon(self.program_location("Play.png"))
            self.pause.setIcon(ico_pause_play)
            self._song_timer.stop()
            self.visualizer.bars_height_timer.stop()

    
    def update_timeline(self):
        duration=self._player.get_length();
        if duration >0:
            
            current_time=self._player.get_current_time()
            
            self.visualizer.song_duration = duration
            if not self.visualizer.is_dragging:
                self.visualizer.song_current_time = current_time
                self.visualizer.update()
                
            current_time_mins=(current_time//1000)//60
            current_time_seconds=(current_time//1000)%60
            
            formated_time=f"{current_time_mins:02d}:{current_time_seconds:02d}"
            
            self.current_time_label.setText(formated_time)
            
            total_time_mins=(duration//1000)//60
            total_time_seconds=(duration//1000)%60
            formated_total_time=f"{total_time_mins:02d}:{total_time_seconds:02d}"
            self.total_time_label.setText(formated_total_time)

            
    def update_current_time_new_slider(self,new_time):
        self._player.set_actual_time(new_time)
        
    def shuffle(self):
        self._queue.shuffle_queue()
        
    def volume_up(self):
        self.volume_slider.setValue(self.volume_slider.value()+10)
    
    def volume_down(self):
            self.volume_slider.setValue(self.volume_slider.value()-10)
    
start=MainWindow()
close=start._app.exec()

sys.exit(close)
