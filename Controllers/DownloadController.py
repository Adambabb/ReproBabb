import os
import re
import threading
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QFileDialog
import Motor

class DownloadController(QObject):
    download_path_changed = Signal(str)

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
            args=(song_id, destination, download_id)
        )
        thread.start()

    def download_playlist(self, songs, playlist_name):
        destination = self._get_download_path()
        if not destination:
            return

        playlist_folder = os.path.join(
            destination, self._safe_playlist_folder_name(playlist_name)
        )
        os.makedirs(playlist_folder, exist_ok=True)

        songs_with_ids = [
            (song, self.download_queue.register_download(song.get("title", "")))
            for song in songs
        ]

        thread = threading.Thread(
            target=self._run_playlist_download,
            daemon=True,
            args=(playlist_folder, songs_with_ids)
        )
        thread.start()

    def _run_download(self, song_id, destination, download_id):
        if not self.download_queue.start_download(download_id):
            return
        res = Motor.fetch(
            song_id,
            download=True,
            destination=destination,
            is_cancelled_fn=lambda: self.download_queue.is_cancelled(download_id),
            update_progress_fn=lambda pct: self.download_queue.update_progress(download_id, pct)
        )
        status = "finished" if res["status"] == "success" else ("cancelled" if self.download_queue.is_cancelled(download_id) else "error")
        self.download_queue.update_status(download_id, status)

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

    def _run_playlist_download(self, playlist_folder, songs_with_ids):
        for song, download_id in songs_with_ids:
            self._run_download(song.get("id", ""), playlist_folder, download_id)

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