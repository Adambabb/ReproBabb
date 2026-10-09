from PySide6.QtCore import QObject, Signal, QTimer, QAbstractListModel, QModelIndex, Qt, QMimeData, QByteArray
from PySide6.QtGui import QIcon, QPixmap
import Motor
import threading
import random
import json


class QueueModel(QAbstractListModel):
    rows_reordered = Signal(list)

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

    def _apply_cached_thumbnails(self, songs):

        for song in songs:
            s_id = song.get("videoId") or song.get("id")
            if s_id and s_id in self._thumbnail_cache:
                song["_icon"] = self._thumbnail_cache[s_id]

    def set_songs(self, songs):
        self.beginResetModel()
        self.songs_list = list(songs)
        self._apply_cached_thumbnails(self.songs_list)
        self.endResetModel()

    def remove_at(self, row):
        if 0 <= row < len(self.songs_list):
            self.beginRemoveRows(QModelIndex(), row, row)
            self.songs_list.pop(row)
            self.endRemoveRows()

    def insert_songs(self, position, songs):
        if not songs:
            return
        self._apply_cached_thumbnails(songs)
        self.beginInsertRows(QModelIndex(), position, position + len(songs) - 1)
        for i, song in enumerate(songs):
            self.songs_list.insert(position + i, song)
        self.endInsertRows()

    def update_thumbnail(self, song_id, icon):
        self._thumbnail_cache[song_id] = icon
        for row, song in enumerate(self.songs_list):
            s_id = song.get("videoId") or song.get("id")
            if s_id == song_id:
                song["_icon"] = icon
                idx = self.index(row)
                self.dataChanged.emit(idx, idx, [Qt.DecorationRole])

    def flags(self, index):
        default_flags = super().flags(index)
        if index.isValid():
            return default_flags | Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsDragEnabled
        return default_flags | Qt.ItemIsDropEnabled

    def supportedDropActions(self):
        return Qt.MoveAction

    def mimeTypes(self):
        return ["application/x-reprobabb-song-row"]

    def mimeData(self, indexes):
        mime_data = QMimeData()
        valid_rows = [idx.row() for idx in indexes if idx.isValid()]
        if valid_rows:
            encoded = json.dumps(valid_rows).encode('utf-8')
            mime_data.setData("application/x-reprobabb-song-row", QByteArray(encoded))
        return mime_data

    def dropMimeData(self, data, action, row, column, parent):
        if not data.hasFormat("application/x-reprobabb-song-row") or action != Qt.MoveAction:
            return False

        encoded = data.data("application/x-reprobabb-song-row")
        source_rows = json.loads(bytes(encoded).decode('utf-8'))
        if not source_rows:
            return False

        from_row = source_rows[0]

        if row != -1:
            target_row = row
        elif parent.isValid():
            target_row = parent.row()
        else:
            target_row = len(self.songs_list)

        if from_row == target_row or from_row == target_row - 1:
            return False

        if self.beginMoveRows(QModelIndex(), from_row, from_row, QModelIndex(), target_row):
            item = self.songs_list.pop(from_row)
            if from_row < target_row:
                target_row -= 1
            self.songs_list.insert(target_row, item)
            self.endMoveRows()
            self.rows_reordered.emit(self.songs_list)
            return True

        return False



class SongQueue(QObject):
    song_data = Signal(dict)         
    change_shuffle = Signal()
    
    def __init__(self, player):
        super().__init__()
        self.player = player
        self.current_index = 0
        self.songs_list = []
        self.click_count = 0
        self.retry_count = 0
        self.timer_click = QTimer()
        self.lock = threading.Lock()
        self.timer_click.setSingleShot(True)
        self.timer_click.timeout.connect(self.process_click)
        self.player.state_changed.connect(self.next_song_queue)
        self.is_shuffle = False
        self.shuffle_song_list = []
        self.shuffle_current_index = 0
        self.fetch_version = 0
        
        self.model = QueueModel()
        self.model.rows_reordered.connect(self.reorder_queue)

    def playing_playlist(self, playlist, start_index=0):
        song_to_play = None
        with self.lock:
            self.retry_count = 0
            self.is_shuffle = False
            self.current_index = start_index if 0 <= start_index < len(playlist) else 0
            self.songs_list = playlist
            self.model.set_songs(self.songs_list)
            if len(self.songs_list) > 0:
                song = self.songs_list[self.current_index]
                song_to_play = song
        if song_to_play is not None:
            fetch_thread = threading.Thread(target=self.fetch_song, daemon=True, args=(song_to_play,))
            fetch_thread.start()
        self.change_shuffle.emit()
    
    def next_or_previous(self, direction):
        with self.lock:
            if direction == "next":
                self.click_count += 1
            elif direction == "previous":
                self.click_count -= 1
        self.timer_click.start(200)
    
    def process_click(self):
        with self.lock:
            if not self.songs_list or self.click_count == 0:
                self.click_count = 0
                return
            if self.is_shuffle:
                self.shuffle_current_index = max(0, min(len(self.shuffle_song_list) - 1, self.shuffle_current_index + self.click_count))
                self.current_index = self.shuffle_song_list[self.shuffle_current_index]
            else:
                self.current_index = max(0, min(len(self.songs_list) - 1, self.current_index + self.click_count))
            self.click_count = 0
            self.retry_count = 0
            song = self.get_song_index()
        fetch_thread = threading.Thread(target=self.fetch_song, daemon=True, args=(song,))
        fetch_thread.start()

    def next_song_queue(self, state):
        song_to_play = None
        if state == "Ended Media" and not self.timer_click.isActive():
            with self.lock:
                self.increment_index()
                song_to_play = self.get_song_index()
                self.retry_count = 0
        elif state == "Cannot Reproduce":
            if self.retry_count < 7:
                with self.lock:
                    song_to_play = self.get_song_index()
                    self.retry_count += 1
            else:
                with self.lock:
                    self.increment_index()
                    song_to_play = self.get_song_index()
                    self.retry_count = 0

        if song_to_play is not None:
            fetch_thread = threading.Thread(target=self.fetch_song, daemon=True, args=(song_to_play,))
            fetch_thread.start()
    
    def fetch_song(self, song):
        self.fetch_version += 1
        current_fetch_version = self.fetch_version
        while song is not None:
            status_fetch = Motor.fetch(song["id"])
            if current_fetch_version != self.fetch_version:
                break
            if status_fetch["status"] == "success":
                url = status_fetch["url"]
                self.song_data.emit(song)
                self.player.play(url)
                song = None
            else:
                error = status_fetch["error"]
                print("Error:", error)
                song = None
                with self.lock:
                    self.increment_index()
                    song = self.get_song_index()
    
    def shuffle_queue(self):
        with self.lock:
            self.is_shuffle = not self.is_shuffle
            if self.is_shuffle:
                if not self.songs_list:
                    self.shuffle_song_list = []
                    self.shuffle_current_index = 0
                    return
                
                # Si hay una canción sonando válidamente, se fija en la posición 0
                if 0 <= self.current_index < len(self.songs_list):
                    other_indices = [i for i in range(len(self.songs_list)) if i != self.current_index]
                    random.shuffle(other_indices)
                    self.shuffle_song_list = [self.current_index] + other_indices
                else:
                    self.shuffle_song_list = list(range(len(self.songs_list)))
                    random.shuffle(self.shuffle_song_list)
                
                self.shuffle_current_index = 0
                new_list = [self.songs_list[i] for i in self.shuffle_song_list]
                self.model.set_songs(new_list)
            else:
                self.model.set_songs(self.songs_list)

    def get_song_index(self):
        if self.is_shuffle:
            if self.shuffle_current_index < len(self.shuffle_song_list):
                index = self.shuffle_song_list[self.shuffle_current_index]
                song = self.songs_list[index]
            else:
                song = None
        else:
            if self.current_index < len(self.songs_list):
                song = self.songs_list[self.current_index]
            else:
                song = None
        return song

    def increment_index(self):
        if self.is_shuffle:
            if self.shuffle_current_index + 1 < len(self.shuffle_song_list):
                self.shuffle_current_index += 1
                self.current_index = self.shuffle_song_list[self.shuffle_current_index]
            else:
                self.shuffle_current_index = len(self.shuffle_song_list)
                self.current_index = len(self.songs_list)
        else:
            self.current_index += 1
     
    def add_to_queue(self, song):
        with self.lock:
            if self.is_shuffle:
                insert_index = self.shuffle_current_index + 1
                self.songs_list.append(song)
                new_song_index = len(self.songs_list) - 1
                self.shuffle_song_list.insert(insert_index, new_song_index)
            else:
                insert_index = self.current_index + 1
                self.songs_list.insert(insert_index, song)
            
            self.model.insert_songs(insert_index, [song])
                
    def add_multiple_to_queue(self, songs):
        with self.lock:
            if self.is_shuffle:
                insert_index = self.shuffle_current_index + 1
                for song in songs:
                    self.songs_list.append(song)
                    new_song_index = len(self.songs_list) - 1
                    self.shuffle_song_list.insert(insert_index, new_song_index)
                    insert_index += 1
            else:
                insert_index = self.current_index + 1
                for song in songs:
                    self.songs_list.insert(insert_index, song)
                    insert_index += 1
            
            self.model.insert_songs(insert_index, songs)

    def reorder_queue(self, new_order):
        with self.lock:
            actual_song_playing = self.get_song_index()
            self.songs_list = new_order
            if actual_song_playing:
                for position, song in enumerate(new_order):
                    if song.get("id") == actual_song_playing.get("id"):
                        self.current_index = position
                        break
    
    def remove_song_at_index(self, index):
        with self.lock:
            if not (0 <= index < len(self.songs_list)):
                return

            if self.is_shuffle:
                if index < len(self.shuffle_song_list):
                    real_index = self.shuffle_song_list.pop(index)
                    if real_index < len(self.songs_list):
                        self.songs_list.pop(real_index)

                    self.shuffle_song_list = [
                        i - 1 if i > real_index else i for i in self.shuffle_song_list
                    ]

                    if index < self.shuffle_current_index:
                        self.shuffle_current_index -= 1

                    self.model.remove_at(index)
            else:
                self.songs_list.pop(index)

                if index < self.current_index:
                    self.current_index -= 1

                self.model.remove_at(index)