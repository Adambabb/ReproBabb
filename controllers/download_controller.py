import os
import re
import threading
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QFileDialog
import motor


class DownloadController(QObject):
    download_path_changed = Signal(str)
    error_download = Signal(str)

    def __init__(self, settings, download_queue, window):
        super().__init__()
        self.settings = settings
        self.download_queue = download_queue
        self.window = window

    def download_song(self, song_data):
        destination = self._get_download_path()
        if not destination:
            return

        song_id = song_data.get("id", "")
        download_id = self.download_queue.register_download(song_data.get("title", ""))

        thread = threading.Thread(
            target=self._run_download,
            daemon=True,
            args=(song_id, destination, download_id),
        )
        thread.start()

    def download_playlist(self, songs, playlist_name):
        destination = self._get_download_path()
        if not destination:
            return

        songs_with_ids = [
            (song, self.download_queue.register_download(song.get("title", "")))
            for song in songs
        ]

        thread = threading.Thread(
            target=self._run_playlist_download,
            daemon=True,
            args=(destination, playlist_name, songs_with_ids),
        )
        thread.start()

    def _run_playlist_download(self, destination, playlist_name, songs_with_ids):
        try:
            playlist_folder = os.path.join(
                destination, self._safe_playlist_folder_name(playlist_name)
            )
            os.makedirs(playlist_folder, exist_ok=True)
            for song, download_id in songs_with_ids:
                self._run_download(song.get("id", ""), playlist_folder, download_id)
        except Exception as e:
            self.error_download.emit(str(e))

    @staticmethod
    def _safe_playlist_folder_name(playlist_name):
        safe_name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", str(playlist_name))
        safe_name = safe_name.rstrip(" .")
        if not safe_name:
            return "Playlist"
        if re.match(
            r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?$",
            safe_name,
            re.IGNORECASE,
        ):
            safe_name = f"_{safe_name}"
        return safe_name

    def _get_download_path(self):
        path = self.settings.value("download_path", "")
        if not path:
            return self.choose_download_path()
        return str(path)

    def choose_download_path(self):
        current_path = str(self.settings.value("download_path", "") or "")
        path = QFileDialog.getExistingDirectory(
            self.window,
            "Choose Download Folder",
            current_path,
        )
        if not path or not path.strip():
            return None
        self.settings.setValue("download_path", path)
        self.download_path_changed.emit(path)
        return path
