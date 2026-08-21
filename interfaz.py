from PySide6.QtWidgets import QApplication, QLabel, QWidget, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,QSlider,QMenu,QSizePolicy,QListWidget,QListWidgetItem,QTabWidget,QFileDialog
from PySide6.QtGui import QIcon, QPixmap,QAction,QShortcut,QKeySequence,QColor
import sys
import Player
import Motor
import Queue
import Network
import CustomWidgets
from PySide6.QtCore import Qt,QPoint,QTimer,Qt,Signal,QObject,QSize
import threading
import os



                
class MainWindow(QObject):
    search_finished=Signal(object)
    fetched_playlist=Signal(bool,list)
    def __init__(self):
        super().__init__()
        self.app=QApplication([])
        self.player=Player.AudioController()
        self.queue=Queue.SongQueue(self.player)
        self.window=QWidget()
        self.search_version=0
        self.thumbnail=Network.ThumbnailFetcher(self.queue)
        
        self.location=os.path.dirname(__file__)
        self.window.setWindowTitle("ReproBabb")
        self.window.setMaximumSize(300,500)
        self.window.setWindowIcon(QIcon(self.program_location("ReproBabb.png")))
    
        vertical_layout=QVBoxLayout()
        search_settings_layout=QHBoxLayout()
        
        self.search_box=QLineEdit()
        search_settings_layout.addWidget(self.search_box)
        self.search_timer=QTimer()
        self.search_timer.timeout.connect(self.click_search)
        self.search_timer.setSingleShot(True)
        self.search_box.textChanged.connect(lambda text: self.search_timer.start(300))
        self.search_box.returnPressed.connect(self.on_search_enter)
        self.search_finished.connect(self.search_result)
        
        self.search_list=QListWidget(self.window)
        self.search_list.setVisible(False)
        self.search_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.search_list.customContextMenuRequested.connect(self.context_menu)
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
        
        self.thumbnail_label=QLabel()
        self.thumbnail_label.setScaledContents(True)
        self.thumbnail_label.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding)
        self.cover=QPixmap(self.program_location("Vinyl-Cover.png"))
        self.thumbnail_label.setPixmap(self.cover)
        self.thumbnail.thumbnail_changed.connect(self.update_thumbnail)
        self.thumbnail.list_thumbnail_changed.connect(self.list_thumbnals)
        self.cover_color=QColor()
        self.thumbnail_label.setMinimumSize(100,100)
        thumbnail_layout=QHBoxLayout()
        thumbnail_layout.addStretch()
        thumbnail_layout.addWidget(self.thumbnail_label)
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
        


        self.song_timer=QTimer()
        self.song_timer.timeout.connect(self.update_timeline)
        

        self.volume_slider=CustomWidgets.volume_design(self.program_location("Volume.png"))
        vertical_layout.addWidget(self.volume_slider,1)
        self.volume_slider.volume_changed.connect(self.player.set_volume)
        
        
        controllers_layout=QHBoxLayout()
        
        previous_song=QPushButton()
        self.ico_previous=QIcon(self.program_location("Previous.png"))
        previous_song.setIcon(self.ico_previous)
        controllers_layout.addWidget(previous_song)   
        
        self.shortcut_previous_song = QShortcut(QKeySequence("Left"), self.window)
        self.shortcut_previous_song.activated.connect(self.previous_song_play)
        
        previous_song.clicked.connect(self.previous_song_play)

        self.pause=QPushButton()
        self.ico_pause_play=QIcon(self.program_location("Play.png"))
        self.pause.setIcon(self.ico_pause_play)
        controllers_layout.addWidget(self.pause)

        self.pause.clicked.connect(self.toggle_play_pause)       
        self.player.state_changed.connect(self.update_play_icon)
        
        self.shortcut_pause_play = QShortcut(QKeySequence("Space"), self.window)
        self.shortcut_pause_play.activated.connect(self.toggle_play_pause)
        
        next_song=QPushButton()
        self.ico_next=QIcon(self.program_location("Next.png"))
        next_song.setIcon(self.ico_next)        
        controllers_layout.addWidget(next_song)
        
        self.shortcut_next_song = QShortcut(QKeySequence("Right"), self.window)
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
        self.tab=QTabWidget()
        self.reproducer=QWidget()
        self.reproducer.setLayout(vertical_layout)
        self.tab.addTab(self.reproducer,"Reproducer")
        
        self.library_vlayout=QVBoxLayout()
        self.library=QWidget()
        self.library_state_hlayout=QHBoxLayout()
        self.sesion_status=QLabel("State: No account")
        self.library_vlayout.addWidget(self.sesion_status)
        self.browser_route=QLineEdit()
        self.browser_route.setReadOnly(True)
        self.library_state_hlayout.addWidget(self.browser_route)
        self.browser_search=QPushButton("Browse_Account:...")
        self.browser_search.clicked.connect(self.select_load_account)
        self.library_state_hlayout.addWidget(self.browser_search)
        self.library_vlayout.addLayout(self.library_state_hlayout)
        self.user_playlists=QListWidget()
        self.user_playlists.setIconSize(QSize(40,40))

        self.user_playlists.itemClicked.connect(self.select_user_playlist)
        self.library_vlayout.addWidget(self.user_playlists)
        self.library.setLayout(self.library_vlayout)
        self.tab.addTab(self.library,"Library")
        
        self.thumbnail.playlist_thumbnail_changed.connect(self.playlist_thumbnail)

        self.fetched_playlist.connect(self.change_tab)
        
        self.general_vlayout=QVBoxLayout()
        self.general_vlayout.addWidget(self.tab)
        self.library_vlayout.addStretch()
        self.window.setLayout(self.general_vlayout)
        self.window.show()
        
    def program_location(self,asset_name):
        return os.path.join(self.location,"Assets",asset_name)


    def click_search(self):
        search=self.search_box.text()
        self.search_version+=1
        search_thread=threading.Thread(target=self.search_process,daemon=True,args=(search,self.search_version))
        search_thread.start()
        
    def search_process(self,search,search_version):
        res=Motor.search_bar(search)
        if search_version == self.search_version:
                    self.search_finished.emit(res)

    def search_result(self,res):
        self.search_list.clear()
        self.search_list.setGeometry(self.search_box.x(),self.search_box.y()+self.search_box.height(),self.search_box.width(),200)
        if "http" in self.search_box.text():
            if isinstance(res,list):
                if res[0]["status"] !="error":
                    self.queue.playing_playlist(res)
            elif isinstance(res,dict):
                if res["status"] !="error":
                    songs=[res]
                    self.queue.playing_playlist(songs)
            self.search_list.setVisible(False)
        else:
            for song in res:
                if song["status"]=="success":
                    artists = ", ".join(artist['name'] for artist in song['artists']) if isinstance(song['artists'], list) else song['artists']
                    self.thumbnail.download_list_thumbnail(song)
                    search_list_element=QListWidgetItem(f"{song['title']}-{artists}")
                    search_list_element.setData(Qt.UserRole,song)
                    self.search_list.addItem(search_list_element)
            if self.search_list.count() > 0:
                self.search_list.setVisible(True)
            else:
                self.search_list.setVisible(False)
        self.shuffle_button.setChecked(False)
        
    def on_search_enter(self):
        self.search_timer.stop()
        self.click_search()
        self.search_box.clearFocus()
        self.window.setFocus()
        self.search_box.clear()

        
    def select_song(self,item):
        song=item.data(Qt.UserRole)
        self.search_box.clearFocus()
        self.queue.playing_playlist([song])
        self.search_list.setVisible(False)
        self.search_box.clear()
        self.window.setFocus()
        
    def settings_menu(self):
        self.settings.exec(self.window.mapToGlobal(QPoint(self.window.width()//2-self.settings.sizeHint().width()//2,self.window.height()//2-self.settings.sizeHint().height()//2)))


    def always_on_toggle(self,display):
        self.window.setWindowFlag(Qt.WindowStaysOnTopHint, display)
        self.window.show()


    def update_thumbnail(self,data):
        self.cover=QPixmap()
        self.cover.loadFromData(data)
        if self.cover.isNull():
                   self.cover=QPixmap(self.program_location("Vinyl-Cover.png")) 
        self.thumbnail_label.setPixmap(self.cover)
        cover_scaled=self.cover.toImage()
        cover_scaled=cover_scaled.scaled(1,1)
        self.cover_color=cover_scaled.pixelColor(0,0)
        self.visualizer.cover_color=self.cover_color
        h,s,v,a=self.cover_color.getHsv()
        h=(h+180)%360
        self.visualizer.cover_color_contrary=QColor.fromHsv(h,s,v,a)
        self.volume_slider.color_slider(self.visualizer.cover_color_contrary)
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
        self.queue.next_or_previous("next")
    
    def previous_song_play(self):
        self.queue.next_or_previous("previous")

    def toggle_play_pause(self):
        self.player.toggle_pause_play()

    def update_play_icon(self,state):
        if state=="Playing":
            ico_pause_play=QIcon(self.program_location("Pause.png"))
            self.pause.setIcon(ico_pause_play)
            self.song_timer.start(300)
            self.visualizer.bars_height_timer.start(50)
        else:
            ico_pause_play=QIcon(self.program_location("Play.png"))
            self.pause.setIcon(ico_pause_play)
            self.song_timer.stop()
            self.visualizer.bars_height_timer.stop()

    
    def update_timeline(self):
        duration=self.player.get_length();
        if duration >0:
            
            current_time=self.player.get_current_time()
            
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
        self.player.set_actual_time(new_time)
        
    def shuffle(self):
        self.queue.shuffle_queue()
    
    def context_menu(self,pos):
        selected_song=self.search_list.itemAt(pos)
        if selected_song:
            song_data=selected_song.data(Qt.UserRole)
            menu=QMenu()
            play_next_action=menu.addAction("Play Next")
            play_next_action.triggered.connect(lambda :(self.queue.add_to_queue(song_data),self.search_list.hide()))
            menu_pos=self.search_list.mapToGlobal(pos)
            menu.exec(menu_pos)
            
    def select_load_account(self):
        file_path,_=QFileDialog.getOpenFileName(self.window,"Select Json with your account","","JSON Files (*.json)")
        if file_path:
            sesion=Motor.set_account(file_path)
            if sesion:
                self.browser_route.setText(file_path)
                self.sesion_status.setText("State: Account Loaded")
                self.user_playlists.clear()
                playlists=Motor.get_user_playlist()
                for playlist in playlists:
                    playlist_item=QListWidgetItem(playlist["title"])
                    playlist_item.setData(Qt.UserRole,playlist)
                    self.user_playlists.addItem(playlist_item)
                    self.thumbnail.download_playlist_thumbnail(playlist)
            else:
                self.browser_route.clear()
                self.sesion_status.setText("State: Error with account")
    
    def select_user_playlist(self,item):
        playlist=item.data(Qt.UserRole)
        playlist_id=playlist["playlistId"]
        search_playlist_thread=threading.Thread(target=self.get_user_playlist_data,daemon=True,args=(playlist_id,))
        search_playlist_thread.start()
        
    
    def get_user_playlist_data(self,playlist_id):
        playlist_data=Motor.playlist_data(playlist_id)
        if playlist_data and playlist_data[0]["status"]=="success":
                        self.fetched_playlist.emit(True,playlist_data)
        else:
            playlist_data=[]
            self.fetched_playlist.emit(False,playlist_data)
        
    def change_tab(self,playlist_status,playlist_data):
        if playlist_status:
            self.queue.playing_playlist(playlist_data)
            self.tab.setCurrentIndex(0)
            
    def playlist_thumbnail(self,image,playlistId):
        playlist_image=QPixmap()
        playlist_image.loadFromData(image)
        playlist_icon=QIcon(playlist_image)
        
        for i in range(self.user_playlists.count()):
            item = self.user_playlists.item(i)
            playlist_data = item.data(Qt.UserRole)
            if playlist_data and playlist_data.get("playlistId") == playlistId:
                item.setIcon(playlist_icon)
                break

start=MainWindow()
close=start.app.exec()

sys.exit(close)
