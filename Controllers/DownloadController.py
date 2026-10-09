import os
import threading
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QFileDialog
import Motor

class DownloadController(QObject):
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

        playlist_folder = os.path.join(destination, playlist_name)
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
        self.download_queue.update_status(download_id, "downloading")
        res = Motor.fetch(
            song_id,
            download=True,
            destination=destination,
            is_cancelled_fn=lambda: self.download_queue.is_cancelled(download_id),
            update_progress_fn=lambda pct: self.download_queue.update_progress(download_id, pct)
        )
        status = "finished" if res["status"] == "success" else ("cancelled" if self.download_queue.is_cancelled(download_id) else "error")
        self.download_queue.update_status(download_id, status)

    def _run_playlist_download(self, playlist_folder, songs_with_ids):
        for song, download_id in songs_with_ids:
            self._run_download(song.get("id", ""), playlist_folder, download_id)

    def _get_download_path(self):
        path = self.settings.value("download_path", None)
        if not path:
            path = QFileDialog.getExistingDirectory(self.window, "Select Download Folder")
            if path and path.strip():
                self.settings.setValue("download_path", path)
            else:
                return None
        return path