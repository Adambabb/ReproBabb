from PySide6.QtWidgets import QApplication, QLabel, QWidget, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,QSlider,QMenu,QSizePolicy,QListWidget,QListWidgetItem
from PySide6.QtGui import QIcon, QPixmap,QAction,QShortcut,QKeySequence,QColor
import sys
import Player
import Motor
import Queue
import Network
import CustomWidgets
from PySide6.QtCore import Qt,QPoint,QTimer,Qt,Signal,QObject
import threading
import os



                
class MainWindow(QObject):
    search_finished=Signal(object)
    def __init__(self):
        super().__init__()
        self._app=QApplication([])
        self._player=Player.AudioController()
        self._queue=Queue.SongQueue(self._player)
        self._window=QWidget()
        self._search_version=0
        self._thumbnail=Network.ThumbnailFetcher(self._queue)
        
        self._location=os.path.dirname(__file__)
        self._window.setWindowTitle("ReproBabb")
        self._window.resize(500,600)
        self._window.setWindowIcon(QIcon(self.program_location("ReproBabb.png")))
    
        vertical_layout=QVBoxLayout()
        search_settings_layout=QHBoxLayout()
        
        self._search_box=QLineEdit()
        search_settings_layout.addWidget(self._search_box)
        self._search_timer=QTimer()
        self._search_timer.timeout.connect(self.click_search)
        self._search_timer.setSingleShot(True)
        self._search_box.textChanged.connect(lambda text: self._search_timer.start(300))
        self._search_box.returnPressed.connect(self.click_search)
        self.search_finished.connect(self.search_result)
        
        self.search_list=QListWidget(self._window)
        self.search_list.setVisible(False)
        self.search_list.itemClicked.connect(self.select_song)
        
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
        self._thumbnail.list_thumbnail_changed.connect(self.list_thumbnals)
        self.cover_color=QColor()
        self._thumbnail_label.setMinimumSize(100,100)
        thumbnail_layout=QHBoxLayout()
        thumbnail_layout.addStretch()
        thumbnail_layout.addWidget(self._thumbnail_label)
        thumbnail_layout.addStretch()
        
        
        vertical_layout.addLayout(thumbnail_layout,6)
        
        self.current_time_label=QLabel("00:00")
        
        self.visualizer = CustomWidgets.time_design(self.cover_color, 0, 0)
        
        self.total_time_label=QLabel("00:00")

        time_layout=QHBoxLayout()
        
        time_layout.addWidget(self.current_time_label,0)
        time_layout.addWidget(self.visualizer,1)
        time_layout.addWidget(self.total_time_label,0)
        vertical_layout.addLayout(time_layout)
        self.visualizer.time_changed.connect(self.update_current_time_new_slider)
        


        self._song_timer=QTimer()
        self._song_timer.timeout.connect(self.update_timeline)
        

        self.volume_slider=CustomWidgets.volume_design(self.program_location("Volume.png"))
        vertical_layout.addWidget(self.volume_slider,1)

        self.volume_slider.volume_changed.connect(self._player.set_volume)
        
        
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
                    self.search_finished.emit(res)

    def search_result(self,res):
        self.search_list.clear()
        self.search_list.setGeometry(self._search_box.x(),self._search_box.y()+self._search_box.height(),self._search_box.width(),200)
        if "http" in self._search_box.text():
            if isinstance(res,list):
                if res[0]["status"] !="error":
                    self._queue.playing_playlist(res)
            elif isinstance(res,dict):
                if res["status"] !="error":
                    songs=[res]
                    self._queue.playing_playlist(songs)
            self.search_list.setVisible(False)
        else:
            for song in res:
                if song["status"]=="success":
                    artists = ", ".join(artist['name'] for artist in song['artists']) if isinstance(song['artists'], list) else song['artists']
                    self._thumbnail.download_list_thumbnail(song)
                    search_list_element=QListWidgetItem(f"{song['title']}-{artists}")
                    search_list_element.setData(Qt.UserRole,song)
                    self.search_list.addItem(search_list_element)
            if self.search_list.count() > 0:
                self.search_list.raise_()
                self.search_list.setVisible(True)
            else:
                self.search_list.setVisible(False)
        self.shuffle_button.setChecked(False)
        
    def select_song(self,item):
        song=item.data(Qt.UserRole)
        
        self._queue.playing_playlist([song])
        self.search_list.setVisible(False)
        self._search_box.clear()
        
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
    
    def list_thumbnals(self,image,id):
        list_image=QPixmap()
        list_image.loadFromData(image)
        list_icon=QIcon(list_image)
        
        for i in range(self.search_list.count()):
            item = self.search_list.item(i)
            song_data = item.data(Qt.UserRole)
            if song_data and song_data.get("id") == id:
                item.setIcon(list_icon)
                break
    
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
        

    
start=MainWindow()
close=start._app.exec()

sys.exit(close)
