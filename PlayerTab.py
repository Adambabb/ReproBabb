from PySide6.QtWidgets import QWidget,QHBoxLayout,QVBoxLayout,QLineEdit,QListWidget,QPushButton,QLabel,QSizePolicy,QMenu,QListWidgetItem,QFrame,QAbstractItemView
from PySide6.QtGui import QIcon,QPixmap,QColor,QShortcut,QKeySequence,QAction
from PySide6.QtCore import QTimer,Qt,QPoint,Signal,QSize,QEvent
import CustomWidgets
import os

class PlayerTab(QWidget):
    search_requested=Signal(str,int)
    play_requested = Signal(list)
    play_pause_toggled = Signal()
    next_requested = Signal()
    play_next_requested=Signal(dict)
    previous_requested = Signal()
    shuffle_requested = Signal() 
    volume_changed = Signal(int)
    time_changed=Signal(int)
    always_on_toggle=Signal(bool)
    added_playlist=Signal(str,dict)
    download_requested=Signal(dict)

    def __init__(self):
        super().__init__()
        self.location=os.path.dirname(__file__)
        self.search_version=0
        vertical_layout=QVBoxLayout()
        search_settings_layout=QHBoxLayout()
        
        
        self.search_box=QLineEdit()
        self.search_box.installEventFilter(self)
        self.download_song=QPushButton("Download Song")
        self.download_song.clicked.connect(lambda: self.download_requested.emit(self.actual_song))
        
        search_settings_layout.addWidget(self.download_song)
        search_settings_layout.addWidget(self.search_box)
        self.search_timer=QTimer()
        self.hide_list_timer=QTimer()
        self.hide_list_timer.setSingleShot(True)
        self.hide_list_timer.timeout.connect(self.hide_list)
        self.search_timer.timeout.connect(self.click_search)
        self.search_timer.setSingleShot(True)
        self.search_box.textChanged.connect(lambda text: self.search_timer.start(300))
        self.search_box.returnPressed.connect(self.on_search_enter)
        
        
        self.search_list=QListWidget(self)
        self.search_list.setIconSize(QSize(50,50))
        self.search_list.setVisible(False)
        self.available_playlists=[]
        self.search_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.search_list.customContextMenuRequested.connect(self.context_menu)
        self.search_list.itemClicked.connect(self.select_song)
        self.search_list.raise_()
        search_button=QPushButton("search")
        search_settings_layout.addWidget(search_button)
        search_button.clicked.connect(self.click_search)

        settings_button=QPushButton()
        ico_settings=QIcon(self.program_location("Settings.png"))
        settings_button.setIcon(ico_settings)
        search_settings_layout.addWidget(settings_button)
        settings_button.clicked.connect(self.settings_menu)
        
        
        self.thumbnail_label=QLabel()
        self.thumbnail_label.setScaledContents(True)
        self.thumbnail_label.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding)
        self.cover=QPixmap(self.program_location("Vinyl-Cover.png"))
        self.thumbnail_label.setPixmap(self.cover)

        self.cover_color=QColor()
        self.thumbnail_label.setMinimumSize(100,100)
        self.thumbnail_label.setMaximumSize(300,300)
        thumbnail_layout=QHBoxLayout()
        thumbnail_layout.addStretch()
        thumbnail_layout.addWidget(self.thumbnail_label)
        
        actual_song=QFrame()
        self.actual_song={}
        self.actual_song_title=QLabel("Nothing Playing")
        self.actual_song_title.setObjectName("title_search_list")
        self.actual_song_title.setWordWrap(True)
        self.actual_song_artist=QLabel("No artist")
        self.actual_song_artist.setObjectName("artist_search_list")
        self.actual_song_artist.setWordWrap(True)
        actual_song_layout=QVBoxLayout()
        actual_song_layout.setAlignment(Qt.AlignVCenter)
        actual_song_layout.setSpacing(4)
        actual_song_layout.addWidget(self.actual_song_title)
        actual_song_layout.addWidget(self.actual_song_artist)
        actual_song.setLayout(actual_song_layout)
        thumbnail_layout.addWidget(actual_song)
        thumbnail_layout.addStretch()

        
        self.thumbnail_frame=QFrame()
        self.thumbnail_frame.setLayout(thumbnail_layout)
        self.thumbnail_frame.setObjectName("thumbnailFrame")
        vertical_layout.addWidget(self.thumbnail_frame,6)
        
        self.current_time_label=QLabel("00:00")
        
        self.visualizer = CustomWidgets.TimeDesign(self.cover_color, 0, 0)
        
        self.total_time_label=QLabel("00:00")

        time_layout=QHBoxLayout()
        
        time_layout.addWidget(self.current_time_label,0)
        time_layout.addWidget(self.visualizer,1)
        time_layout.addWidget(self.total_time_label,0)
        vertical_layout.addLayout(time_layout)
        self.visualizer.time_changed.connect(self.update_current_time_new_slider)
        

        self.volume_slider=CustomWidgets.VolumeDesign(self.program_location("Volume.png"))
        vertical_layout.addWidget(self.volume_slider,1)
        self.volume_slider.volume_changed.connect(self.volume_changed.emit)
        self.status_label = QLabel("")
        vertical_layout.addWidget(self.status_label)

        
        controllers_layout=QHBoxLayout()
        
        previous_song=QPushButton()
        self.ico_previous=QIcon(self.program_location("Previous.png"))
        previous_song.setIcon(self.ico_previous)
        controllers_layout.addWidget(previous_song)   
        
        self.shortcut_previous_song = QShortcut(QKeySequence("Left"), self)
        self.shortcut_previous_song.activated.connect(self.previous_song_play)
        
        previous_song.clicked.connect(self.previous_song_play)

        self.pause=QPushButton()
        self.ico_pause_play=QIcon(self.program_location("Play.png"))
        self.pause.setIcon(self.ico_pause_play)
        controllers_layout.addWidget(self.pause)

        self.pause.clicked.connect(self.toggle_play_pause)       
        
        self.shortcut_pause_play = QShortcut(QKeySequence("Space"), self)
        self.shortcut_pause_play.activated.connect(self.toggle_play_pause)
        
        next_song=QPushButton()
        self.ico_next=QIcon(self.program_location("Next.png"))
        next_song.setIcon(self.ico_next)        
        controllers_layout.addWidget(next_song)
        
        self.shortcut_next_song = QShortcut(QKeySequence("Right"), self)
        self.shortcut_next_song.activated.connect(self.next_song_play)
        
        next_song.clicked.connect(self.next_song_play)
        
        self.shuffle_button=QPushButton()
        self.shuffle_button.setCheckable(True)
        self.shuffle_icon=QIcon(self.program_location("Shuffle.png"))
        self.shuffle_button.setIcon(self.shuffle_icon)
        self.shuffle_button.clicked.connect(self.shuffle)
        
        controllers_layout.addWidget(self.shuffle_button)
                
        vertical_layout.addLayout(controllers_layout,1)
        
        self.is_link_search=False

        self.settings=QMenu()
        self.visible=QAction("Always Visible")
        self.visible.setCheckable(True)
        self.visible.setChecked(True)
        self.settings.addAction(self.visible)
        self.visible.toggled.connect(self.always_on_toggle.emit)
        
        self.general_layout=QHBoxLayout()
        self.general_layout.addLayout(vertical_layout)
        
        self.vertical_queue_layout=QVBoxLayout()
        
        self.vertical_queue_layout.addLayout(search_settings_layout)
        
        self.vertical_queue_place=QLabel("Queue in work")
        self.vertical_queue_layout.addWidget(self.vertical_queue_place)
        
        self.queue_list=QListWidget(self)
        self.queue_list.setIconSize(QSize(60,60))
        self.vertical_queue_layout.addWidget(self.queue_list)
       
        
        self.general_layout.addLayout(self.vertical_queue_layout)
        
        self.setLayout(self.general_layout)
        
        
    def program_location(self,asset_name):
        return os.path.join(self.location,"Assets",asset_name)


    def click_search(self):
        search=self.search_box.text()
        if not search:
            self.search_list.setVisible(False)
            return
        self.search_version+=1
        self.is_link_search = "http" in search
        self.search_requested.emit(search,self.search_version)

    def search_result(self,res):
        self.search_list.clear()
        self.search_list.setGeometry(self.search_box.x(),self.search_box.y()+self.search_box.height(),self.search_box.width(),200)
        self.search_list.raise_()
        if self.is_link_search:
            if isinstance(res, list) and res and res[0]["status"] != "error":
                self.play_requested.emit(res)
            elif isinstance(res, dict) and res.get("status") != "error":
                songs=[res]
                self.play_requested.emit(songs)
            self.search_list.setVisible(False)
        else:
            for song in res:
                if isinstance(song, dict) and song.get("status") == "success":
                    artists = ", ".join(artist['name'] for artist in song['artists']) if isinstance(song['artists'], list) else song['artists']
                    search_list_element=QListWidgetItem()
                    search_list_element.setData(Qt.UserRole,song)
                    self.search_list.addItem(search_list_element)
                    search_row_element=CustomWidgets.search_row(song,artists)
                    search_list_element.setSizeHint(search_row_element.sizeHint())
                    self.search_list.setItemWidget(search_list_element,search_row_element)
            self.search_list.setVisible((self.search_list.count() > 0))
    
    
        
       
    def on_search_enter(self):
        self.search_timer.stop()
        self.click_search()
        self.search_box.clearFocus()
        self.setFocus()
        self.search_box.clear()

        
    def select_song(self,item):
        song=item.data(Qt.UserRole)
        self.search_box.clearFocus()
        self.play_requested.emit([song])
        self.search_list.setVisible(False)
        self.search_box.clear()
        self.setFocus()
        
    def settings_menu(self):
        self.settings.exec(self.mapToGlobal(QPoint(self.width()//2-self.settings.sizeHint().width()//2,self.height()//2-self.settings.sizeHint().height()//2)))



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
        if self.search_list.isVisible():
            self.search_list.raise_()
        self.visualizer.update()
    
    def update_title_artist(self,song):
        self.actual_song=song
        title = song.get("title", "Unknown Title")
        artists = song.get("artists", "")
        if isinstance(artists, list):
            artists = ", ".join(a.get("name", "") if isinstance(a, dict) else str(a) for a in artists)
    
        self.actual_song_title.setText(title)
        self.actual_song_artist.setText(str(artists))
            
    def next_song_play(self):
        self.next_requested.emit()
        
    def previous_song_play(self):
        self.previous_requested.emit()

    def toggle_play_pause(self):
        self.play_pause_toggled.emit()        

    def update_play_icon(self,state):
            if state=="Playing":
                ico_pause_play=QIcon(self.program_location("Pause.png"))
                self.pause.setIcon(ico_pause_play)
                self.visualizer.bars_height_timer.start(50)
            else:
                ico_pause_play=QIcon(self.program_location("Play.png"))
                self.pause.setIcon(ico_pause_play)
                self.visualizer.bars_height_timer.stop()
    
    def update_timeline(self,current_player_time,player_duration):
            duration=player_duration;
            if duration >0:
                
                current_time=current_player_time
                
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
    
    def context_menu(self,pos):
            selected_song=self.search_list.itemAt(pos)
            if selected_song:
                song_data=selected_song.data(Qt.UserRole)
                menu=QMenu()
                play_next_action=menu.addAction("Play Next")
                play_next_action.triggered.connect(lambda: (self.play_next_requested.emit(song_data), self.search_list.hide()))
                add_song_playlist=menu.addMenu("Add to playlist")
                download_selected_song=menu.addAction("Download")
                download_selected_song.triggered.connect(lambda:(self.download_requested.emit(song_data)))
                for playlist in self.available_playlists:
                    playlist_to_select=add_song_playlist.addAction(playlist["title"])
                    playlist_to_select.triggered.connect(lambda checked=False, p=playlist["playlistId"], s=song_data: self.added_playlist.emit(p,s))                
                menu_pos=self.search_list.mapToGlobal(pos)
                menu.exec(menu_pos)
                            
    
    def update_playlist(self,new_playlist):
        self.available_playlists=new_playlist
    
    def update_current_time_new_slider(self,new_time):
           self.time_changed.emit(new_time)
            
    def shuffle(self):
        self.shuffle_requested.emit()
    
    def show_error(self, message):
        self.status_label.setText(message)
        QTimer.singleShot(3000, lambda: self.status_label.setText(""))
        
    def hide_list(self):
        self.search_list.setVisible(False)

    def eventFilter(self, obj, event):
        if obj == self.search_box and event.type() == QEvent.FocusOut:
            self.hide_list_timer.start(100)
        elif obj == self.download_song:
            if event.type() == QEvent.Enter:
                # En lugar de ocultar el botón (que mueve el layout), 
                # quitamos el texto y mostramos la barra.
                self.download_song.setText("") 
                self.download_progress.setVisible(True)
            elif event.type() == QEvent.Leave:
                # Volvemos el texto y ocultamos la barra.
                self.download_song.setText("Download Song")
                self.download_progress.setVisible(False)
            elif event.type() == QEvent.Resize:
                # Ajusta el tamaño de la barra al tamaño del botón
                self.download_progress.setGeometry(0, 0, self.download_song.width(), self.download_song.height())
        return super().eventFilter(obj, event)
    

                    
    def update_queue_list(self, songs):
        self.queue_list.clear()
        target_item = None
        
        # Obtener un ID único de la canción actual para comparar de forma segura
        current_id = self.actual_song.get("videoId") or self.actual_song.get("id") if isinstance(self.actual_song, dict) else None

        for song in songs:
            artists = ", ".join(artist['name'] for artist in song['artists']) if isinstance(song['artists'], list) else song['artists']
            queue_list_element = QListWidgetItem()
            queue_list_element.setData(Qt.UserRole, song)
            self.queue_list.addItem(queue_list_element)
            
            queue_row_element = CustomWidgets.queue(song, artists)
            queue_list_element.setSizeHint(queue_row_element.sizeHint())
            self.queue_list.setItemWidget(queue_list_element, queue_row_element)
            
            # Comparar por ID único o por igualdad directa
            song_id = song.get("videoId") or song.get("id") if isinstance(song, dict) else None
            if (current_id and song_id == current_id) or song == self.actual_song:
                target_item = queue_list_element

        # Hacer el desplazamiento si se encontró la canción
        if target_item:
            # Asegura que el layout de la lista haya calculado los tamaños
            self.queue_list.doItemsLayout() 
            self.queue_list.scrollToItem(target_item, QAbstractItemView.PositionAtTop)


    