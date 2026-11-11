import os
import json
import threading
from PySide6.QtCore import QObject, Signal, QStandardPaths
from PySide6.QtWidgets import QDialog, QMessageBox
import motor
import login


class LibraryController(QObject):
    playlists_loaded = Signal(list, str, bool, bool)
    playlist_data_fetched = Signal(bool, list)

    def __init__(self, settings, library_tab, player_tab, thumbnail_fetcher, window):
        super().__init__()
        self.settings = settings
        self.library_tab = library_tab
        self.player_tab = player_tab
        self.thumbnail_fetcher = thumbnail_fetcher
        self.window = window
        self.playlists_loaded.connect(self.on_playlists_loaded)

    def try_auto_login(self):
        saved_path = self.settings.value("saved_session_path", "")
        if saved_path and os.path.exists(saved_path):
            self.load_account(saved_path, show_error=False)

    def load_account(self, file_path, show_error=True):
        self.library_tab.sesion_status.setText("State: Loading...")
        get_account_thread = threading.Thread(
            target=self.run_load_account, daemon=True, args=(file_path, show_error)
        )
        get_account_thread.start()

    def run_load_account(self, file_path, show_error):
        playlists = []
        success = False
        try:
            if file_path and motor.set_account(file_path):
                playlists = motor.get_user_playlist()
                success = True
        except Exception as e:
            print(f"Error cargando la cuenta: {e}")
            playlists = []
            success = False
        finally:
            self.playlists_loaded.emit(playlists, file_path, success, show_error)

    def on_playlists_loaded(self, playlists, file_path, success, show_error):
        if file_path and success:
            self.settings.setValue("saved_session_path", file_path)
            self.player_tab.update_playlist(playlists)
            for pl in playlists:
                self.thumbnail_fetcher.download_playlist_thumbnail(pl)
        elif show_error and not success:
            QMessageBox.critical(
                self.window, "Sesion Error", "Couldn't sign up or expired credentials."
            )
        self.library_tab.display_playlists(playlists, file_path, success)

    def create_browser_session(self):
        login_dialog = login.LoginDialog()
        if login_dialog.exec() == QDialog.Accepted:
            app_path = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
            os.makedirs(app_path, exist_ok=True)
            file_path = os.path.join(app_path, "browser.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(login_dialog.headers_dict, f, indent=4)
            self.load_account(file_path, show_error=True)

    def fetch_playlist_songs(self, playlist):
        playlist_id = playlist.get("playlistId", "")
        threading.Thread(
            target=self._run_fetch_playlist, daemon=True, args=(playlist_id,)
        ).start()

    def _run_fetch_playlist(self, playlist_id):
        data = motor.playlist_data(playlist_id)
        status = bool(data and data[0].get("status") == "success")
        self.playlist_data_fetched.emit(status, data if status else [])

    def add_song_to_playlist(self, playlist_id, song_data):
        threading.Thread(
            target=motor.add_song_playlist,
            daemon=True,
            args=(playlist_id, song_data.get("id", "")),
        ).start()

    def remove_song_from_playlist(self, playlist_id, song_data):
        def _run():
            res = motor.remove_song_playlist(playlist_id, song_data)
            if res.get("status") == "success":
                self.fetch_playlist_songs({"playlistId": playlist_id})

        threading.Thread(target=_run, daemon=True).start()
