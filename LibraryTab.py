from PySide6.QtWidgets import QWidget,QHBoxLayout,QVBoxLayout,QLineEdit,QListWidget,QListWidgetItem,QPushButton,QLabel,QFileDialog,QMenu
from PySide6.QtCore import Signal,QSize,Qt
import CustomWidgets



class LibraryTab(QWidget):
    load_account_requested=Signal(str,bool)
    playlist_content_selected=Signal(dict)
    playlist_play_requested=Signal(list,int)
    song_playlist_delete=Signal(str,dict)
    def __init__(self):
        super().__init__()
        self.playlists_songs=QHBoxLayout()
        self.library_vlayout=QVBoxLayout()
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
        
        self.library_vlayout.addStretch()

        self.user_playlists=QListWidget()
        self.user_playlists.setObjectName("library_list")
        self.user_playlists.setIconSize(QSize(50,50))
        self.user_playlists_songs=QListWidget()
        self.user_playlists_songs.setIconSize(QSize(50,50))
        self.user_playlists_songs.itemClicked.connect(self.play_playlist_song_at)
        self.user_playlists_songs.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.user_playlists_songs.customContextMenuRequested.connect(self.playlist_context_menu)
        self.user_playlists.itemClicked.connect(self.select_user_playlist)
        self.playlists_songs.addWidget(self.user_playlists)
        self.playlists_songs.addWidget(self.user_playlists_songs)
        self.library_vlayout.addLayout(self.playlists_songs,1)
        self.setLayout(self.library_vlayout)
        
        self.current_playlist=None
    
    
    def select_load_account(self):
        file_path,_=QFileDialog.getOpenFileName(self,"Select Json with your account","","JSON Files (*.json)")
        if file_path:
            self.load_account_requested.emit(file_path,True)
            
                    
    def select_user_playlist(self,item):
            playlist=item.data(Qt.UserRole)
            self.current_playlist=playlist
            self.playlist_content_selected.emit(playlist)
    
    def play_playlist_song_at(self,item):
        songs = [self.user_playlists_songs.item(i).data(Qt.UserRole)
             for i in range(self.user_playlists_songs.count())]
        start_index = self.user_playlists_songs.row(item)

        self.playlist_play_requested.emit(songs,start_index)
    
    def display_playlists(self,playlist,file_path,succes):
            if succes:
                self.browser_route.setText(file_path)
                self.sesion_status.setText("State: Account Loaded")
                self.user_playlists.clear()
                playlists=playlist
                for one_playlist in playlists:
                    playlist_item=QListWidgetItem(one_playlist["title"])
                    playlist_item.setData(Qt.UserRole,one_playlist)
                    self.user_playlists.addItem(playlist_item)
            else:
                self.browser_route.clear()
                self.sesion_status.setText("State: Error with account")
    
    def display_playlist_songs(self,playlist_status,playlist_data):
            if playlist_status:
                self.user_playlists_songs.clear()
                for song in playlist_data:
                    artists = ", ".join(artist['name'] for artist in song['artists']) if isinstance(song['artists'], list) else song['artists']
                    playlist_item=QListWidgetItem()
                    playlist_item.setData(Qt.UserRole,song)
                    self.user_playlists_songs.addItem(playlist_item)
                    playlist_song_row_element=CustomWidgets.search_row(song,artists)
                    playlist_item.setSizeHint(playlist_song_row_element.sizeHint())
                    self.user_playlists_songs.setItemWidget(playlist_item,playlist_song_row_element)
    
    def playlist_context_menu(self,pos):
        selected_song=self.user_playlists_songs.itemAt(pos)
        if selected_song and self.current_playlist:
            song_data=selected_song.data(Qt.UserRole)
            menu=QMenu()
            delete_action=menu.addAction("Remove from playlist")
            delete_action.triggered.connect(lambda: self.song_playlist_delete.emit(self.current_playlist.get("playlistId",""),song_data))
            menu.exec(self.user_playlists_songs.mapToGlobal(pos))