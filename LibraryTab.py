from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QListWidget, 
                             QListWidgetItem, QPushButton, QLabel, QFileDialog, QMenu, 
                             QListView, QAbstractItemView)
from PySide6.QtCore import Signal, QSize, Qt, QAbstractListModel, QModelIndex
from PySide6.QtGui import QIcon, QPixmap
import CustomWidgets

# ==============================================================================
# MODELO VIRTUAL LIGERO PARA LAS CANCIONES DE LA PLAYLIST
# ==============================================================================
class PlaylistSongsModel(QAbstractListModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.songs_list = []
        self._thumbnail_cache = {}

    def rowCount(self, parent=QModelIndex()):
        return len(self.songs_list)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self.songs_list)):
            return None
        
        song = self.songs_list[index.row()]
        if role == Qt.UserRole:
            return song
        elif role == Qt.DecorationRole:
            return song.get("_icon", None)
            
        return None

    def set_songs(self, songs):
        self.beginResetModel()
        self.songs_list = list(songs)
        # Aplicar carátulas guardadas en caché
        for song in self.songs_list:
            s_id = song.get("videoId") or song.get("id")
            if s_id and s_id in self._thumbnail_cache:
                song["_icon"] = self._thumbnail_cache[s_id]
        self.endResetModel()

    def update_thumbnail(self, song_id, icon):
        self._thumbnail_cache[song_id] = icon
        for row, song in enumerate(self.songs_list):
            s_id = song.get("videoId") or song.get("id")
            if s_id == song_id:
                song["_icon"] = icon
                idx = self.index(row)
                self.dataChanged.emit(idx, idx, [Qt.DecorationRole])


# ==============================================================================
# PESTAÑA BIBLIOTECA CON QLISTVIEW OPTIMIZADO
# ==============================================================================
class LibraryTab(QWidget):
    load_account_requested = Signal(str, bool)
    create_browser_requested = Signal()
    playlist_content_selected = Signal(dict)
    playlist_play_requested = Signal(list, int)
    song_playlist_delete = Signal(str, dict)
    playlist_download_requested = Signal(list, str)

    def __init__(self):
        super().__init__()
        self.playlists_songs = QHBoxLayout()
        self.library_vlayout = QVBoxLayout()
        self.library_state_hlayout = QHBoxLayout()
        
        self.sesion_status = QLabel("State: No account")
        self.library_vlayout.addWidget(self.sesion_status)
        
        self.browser_route = QLineEdit()
        self.browser_route.setReadOnly(True)
        self.library_state_hlayout.addWidget(self.browser_route)
        
        self.create_browser_button = QPushButton("Create Browser: To load account")
        self.create_browser_button.clicked.connect(self.create_browser)
        self.library_vlayout.addWidget(self.create_browser_button)
        
        self.browser_search = QPushButton("Browse_Account:...")
        self.browser_search.clicked.connect(self.select_load_account)
        self.library_state_hlayout.addWidget(self.browser_search)
        self.library_vlayout.addLayout(self.library_state_hlayout)
        
        self.download_playlist_button = QPushButton("Download Playlist")
        self.download_playlist_button.clicked.connect(self.download_playlist)
        self.library_vlayout.addWidget(self.download_playlist_button)
        self.library_vlayout.addStretch()

        # Lista de Playlists del usuario (se mantiene QListWidget)
        self.user_playlists = QListWidget()
        self.user_playlists.setObjectName("library_list")
        self.user_playlists.setIconSize(QSize(50, 50))
        self.user_playlists.itemClicked.connect(self.select_user_playlist)

        # Vista Virtualizada QListView para las Canciones de la Playlist
        self.user_playlists_songs = QListView(self)
        self.user_playlists_songs.setItemDelegate(CustomWidgets.SongItemDelegate(self.user_playlists_songs))
        self.user_playlists_songs.setSelectionMode(QAbstractItemView.SingleSelection)
        
        self.playlist_songs_model = PlaylistSongsModel()
        self.user_playlists_songs.setModel(self.playlist_songs_model)
        
        self.user_playlists_songs.clicked.connect(self.play_playlist_song_at)
        self.user_playlists_songs.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.user_playlists_songs.customContextMenuRequested.connect(self.playlist_context_menu)

        self.playlists_songs.addWidget(self.user_playlists)
        self.playlists_songs.addWidget(self.user_playlists_songs)
        self.library_vlayout.addLayout(self.playlists_songs, 1)
        self.setLayout(self.library_vlayout)
        
        self.current_playlist = None
        self._thumbnail_cache = {}
        self._thumbnail_items = {"playlists": {}}

    def select_load_account(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Json with your account", "", "JSON Files (*.json)")
        if file_path:
            self.load_account_requested.emit(file_path, True)
            
    def select_user_playlist(self, item):
        playlist = item.data(Qt.UserRole)
        self.current_playlist = playlist
        self.playlist_content_selected.emit(playlist)
    
    def play_playlist_song_at(self, index):
        if not index.isValid():
            return
        songs = self.playlist_songs_model.songs_list
        start_index = index.row()
        self.playlist_play_requested.emit(songs, start_index)
    
    def display_playlists(self, playlist, file_path, succes):
        if succes:
            self.browser_route.setText(file_path)
            self.sesion_status.setText("State: Account Loaded")
            self.user_playlists.clear()
            self._thumbnail_items["playlists"].clear()
            for one_playlist in playlist:
                playlist_item = QListWidgetItem(one_playlist["title"])
                playlist_item.setData(Qt.UserRole, one_playlist)
                self.user_playlists.addItem(playlist_item)
                self._index_thumbnail_item(playlist_item, one_playlist, "playlistId", "playlists")
        else:
            self.browser_route.clear()
            self.sesion_status.setText("State: Error with account")
    
    def display_playlist_songs(self, playlist_status, playlist_data):
        if playlist_status:
            # Carga instantánea de todas las canciones en el modelo
            self.playlist_songs_model.set_songs(playlist_data)

    def _index_thumbnail_item(self, item, data, id_key, list_name):
        thumbnail_id = data.get(id_key)
        if not thumbnail_id:
            return
        self._thumbnail_items[list_name].setdefault(thumbnail_id, []).append(item)
        icon = self._thumbnail_cache.get(thumbnail_id)
        if icon:
            item.setIcon(icon)

    def set_list_thumbnail(self, image, thumbnail_id):
        pixmap = QPixmap()
        pixmap.loadFromData(image)
        icon = QIcon(pixmap)
        self._thumbnail_cache[thumbnail_id] = icon
        for item_group in self._thumbnail_items.values():
            for item in item_group.get(thumbnail_id, []):
                item.setIcon(icon)
        # Actualizar también el modelo de la playlist
        self.playlist_songs_model.update_thumbnail(thumbnail_id, icon)
    
    def playlist_context_menu(self, pos):
        index = self.user_playlists_songs.indexAt(pos)
        if index.isValid() and self.current_playlist:
            song_data = index.data(Qt.UserRole)
            menu = QMenu()
            delete_action = menu.addAction("Remove from playlist")
            delete_action.triggered.connect(lambda: self.song_playlist_delete.emit(self.current_playlist.get("playlistId", ""), song_data))
            menu.exec(self.user_playlists_songs.mapToGlobal(pos))
    
    def create_browser(self):
        self.create_browser_requested.emit()
    
    def download_playlist(self):
        if self.current_playlist:
            songs = self.playlist_songs_model.songs_list
            self.playlist_download_requested.emit(songs, self.current_playlist.get("title", ""))