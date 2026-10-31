import sys
from PySide6.QtWidgets import (
    QApplication,
    QMessageBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import QCoreApplication, Qt, QTimer, QSettings, QObject
from PySide6.QtGui import QGuiApplication

import PlayerTab, LibraryTab, DownloadTab
import MiniPlayer
import KeyboardControls
import Player, Queue, DownloadQueue, Network
from Controllers.DownloadController import DownloadController
from Controllers.LibraryController import LibraryController
from Controllers.SearchController import SearchController
from Utils import resource_path


class MainWindow(QObject):
    def __init__(self):
        super().__init__()
        self.app = QApplication(sys.argv)
        self.window = QWidget()
        self.window.setWindowTitle("ReproBabb")
        self.window.setMinimumSize(640, 420)

        icon_path = resource_path("Assets/ReproBabb.ico")
        app_icon = QIcon(icon_path)
        self.window.setWindowIcon(app_icon)
        self.app.setWindowIcon(app_icon)

        self.settings = QSettings("Reprobabb", "Reprobabb")
        QCoreApplication.setOrganizationName("Reprobabb")
        QCoreApplication.setApplicationName("Reprobabb")

        with open(resource_path("Styles/styles.qss"), "r") as f:
            self.app.setStyleSheet(f.read())

        try:
            self.player = Player.AudioController()
        except Player.VlcNotAvailableError:
            QMessageBox.critical(
                self.window,
                "Error de VLC",
                "VLC was not found. ReproBabb needs VLC (64-bit) installed. You can download it from videolan.org.",
            )
            sys.exit(1)
        self.queue = Queue.SongQueue(self.player)
        self.download_queue = DownloadQueue.DownloadQueue()
        self.thumbnail = Network.ThumbnailFetcher(self.queue)

        self.song_timer = QTimer()
        self.song_timer.timeout.connect(self.update_timeline)

        self.refresh_download_timer = QTimer()
        self.refresh_download_timer.timeout.connect(self.refresh_download)
        self.refresh_download_timer.start(500)

        self.tab = QTabWidget()
        self.player_tab = PlayerTab.PlayerTab()
        self.library_tab = LibraryTab.LibraryTab()
        self.download_tab = DownloadTab.DownloadTab()
        self.keyboard_controls = KeyboardControls.KeyboardControls(self)
        self.mini_player = MiniPlayer.MiniPlayer(self.queue.model)
        self.mini_player.setWindowFlags(
            Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint
        )
        self.mini_player.setWindowTitle("ReproBabb Mini Player")
        self.mini_player.setWindowIcon(app_icon)
        self.mini_player.hide()

        always_on = self.settings.value("always_on", False, type=bool)
        self.player_tab.visible.setChecked(always_on)
        self.window.setWindowFlag(Qt.WindowStaysOnTopHint, always_on)

        self.player_tab.queue_list.setModel(self.queue.model)

        self.tab.addTab(self.player_tab, "Reproducer")
        self.tab.addTab(self.library_tab, "Library")
        self.tab.addTab(self.download_tab, "Downloads")

        layout = QVBoxLayout(self.window)
        layout.addWidget(self.tab)

        self.download_ctrl = DownloadController(
            self.settings, self.download_queue, self.window
        )
        self.library_ctrl = LibraryController(
            self.settings,
            self.library_tab,
            self.player_tab,
            self.thumbnail,
            self.window,
        )
        self.search_ctrl = SearchController(self.player_tab, self.thumbnail)
        self.download_tab.download_path_requested.connect(
            self.download_ctrl.choose_download_path
        )
        self.download_ctrl.download_path_changed.connect(
            self.download_tab.set_download_path
        )
        self.download_tab.set_download_path(self.settings.value("download_path", ""))

        self._wire_signals()

        self.app.aboutToQuit.connect(
            lambda: self.thumbnail.download_list_thumbnail_executor.shutdown(
                wait=False, cancel_futures=True
            )
        )
        self.app.aboutToQuit.connect(self.keyboard_controls.stop)
        self.library_ctrl.try_auto_login()
        self.window.show()

    def _wire_signals(self):
        self.keyboard_controls.play_pause_requested.connect(
            self.player_tab.toggle_play_pause
        )
        self.keyboard_controls.next_requested.connect(self.player_tab.next_song_play)
        self.player_tab.search_requested.connect(self.search_ctrl.search)
        self.player_tab.mini_player_requested.connect(self.show_mini_player)
        self.mini_player.expanded_requested.connect(self.show_main_window)
        self.search_ctrl.search_completed.connect(
            self.search_ctrl.process_search_results
        )
        self.search_ctrl.similar_songs_fetched.connect(self.queue.add_multiple_to_queue)

        self.player_tab.play_pause_toggled.connect(self.player.toggle_pause_play)
        self.player_tab.next_requested.connect(
            lambda: self.queue.next_or_previous("next")
        )
        self.player_tab.previous_requested.connect(
            lambda: self.queue.next_or_previous("previous")
        )
        self.player_tab.time_changed.connect(self.player.set_actual_time)
        self.player_tab.volume_changed.connect(self.player.set_volume)
        self.player_tab.shuffle_requested.connect(self.toggle_shuffle)
        self.mini_player.previous_requested.connect(
            lambda: self.queue.next_or_previous("previous")
        )
        self.mini_player.play_pause_toggled.connect(self.player.toggle_pause_play)
        self.mini_player.next_requested.connect(
            lambda: self.queue.next_or_previous("next")
        )
        self.mini_player.shuffle_requested.connect(self.toggle_shuffle)

        self.player_tab.play_requested.connect(self.queue.playing_playlist)
        self.player_tab.play_requested.connect(self.search_ctrl.fetch_similar_songs)
        self.player_tab.play_queue_song.connect(self.queue.playing_playlist)
        self.mini_player.queue_song_requested.connect(self.queue.playing_playlist)
        self.library_tab.playlist_play_shuffled_requested.connect(
            self.queue.playing_playlist_shuffled
        )
        self.player_tab.play_next_requested.connect(self.queue.add_to_queue)
        self.player_tab.queue_reordered.connect(self.queue.reorder_queue)
        self.player_tab.remove_queue.connect(self.queue.remove_song_at_index)
        self.player_tab.remove_from_playlist_requested.connect(
            self.library_tab.remove_queue_song_from_current_playlist
        )
        self.player_tab.always_on_toggle.connect(self.always_on_toggle)

        self.player.error_occurred.connect(self.player_tab.show_error)
        self.player.state_changed.connect(self.update_play_icon)
        self.queue.song_data.connect(self.player_tab.update_title_artist)
        self.queue.song_data.connect(self.mini_player.set_song)
        self.queue.change_shuffle.connect(self.reset_shuffle)

        self.library_tab.load_account_requested.connect(self.library_ctrl.load_account)
        self.library_tab.create_browser_requested.connect(
            self.library_ctrl.create_browser_session
        )
        self.library_tab.playlist_content_selected.connect(
            self.library_ctrl.fetch_playlist_songs
        )
        self.library_tab.playlist_play_requested.connect(self.queue.playing_playlist)
        self.library_ctrl.playlist_data_fetched.connect(self.on_playlist_fetched)
        self.player_tab.added_playlist.connect(self.library_ctrl.add_song_to_playlist)
        self.library_tab.song_playlist_delete.connect(
            self.library_ctrl.remove_song_from_playlist
        )

        self.player_tab.download_requested.connect(self.download_ctrl.download_song)
        self.library_tab.playlist_download_requested.connect(
            self.download_ctrl.download_playlist
        )
        self.download_tab.cancel_download_requested.connect(
            self.download_queue.cancel_download
        )

        self.thumbnail.thumbnail_changed.connect(self.player_tab.update_thumbnail)
        self.thumbnail.thumbnail_changed.connect(self.mini_player.set_thumbnail)
        self.thumbnail.list_thumbnail_changed.connect(self.list_thumbnails)
        self.thumbnail.playlist_thumbnail_changed.connect(self.list_thumbnails)

    def always_on_toggle(self, display):
        self.settings.setValue("always_on", display)
        self.window.setWindowFlag(Qt.WindowStaysOnTopHint, display)
        self.window.show()

    def show_mini_player(self):
        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            area = screen.availableGeometry()
            margin = 16
            self.mini_player.move(
                area.right() - self.mini_player.width() - margin,
                area.bottom() - self.mini_player.height() - margin,
            )
        self.window.hide()
        self.mini_player.show()
        self.mini_player.raise_()
        self.mini_player.activateWindow()

    def show_main_window(self):
        self.mini_player.hide()
        self.window.showNormal()
        self.window.raise_()
        self.window.activateWindow()

    def toggle_shuffle(self):
        self.queue.shuffle_queue()
        self.player_tab.shuffle_button.setChecked(self.queue.is_shuffle)
        self.mini_player.set_shuffle_enabled(self.queue.is_shuffle)

    def reset_shuffle(self):
        self.player_tab.shuffle_button.setChecked(self.queue.is_shuffle)
        self.mini_player.set_shuffle_enabled(self.queue.is_shuffle)

    def update_play_icon(self, state):
        if state == "Playing":
            self.song_timer.start(300)
            self.tab.setCurrentIndex(0)
        else:
            self.song_timer.stop()
        self.player_tab.update_play_icon(state)
        self.mini_player.set_playback_state(state)

    def update_timeline(self):
        duration = self.player.get_length()
        if duration > 0:
            current_time = self.player.get_current_time()
            self.player_tab.update_timeline(current_time, duration)

    def refresh_download(self):
        if self.download_queue.downloads:
            self.download_tab.refresh_downloads(self.download_queue.get_data())

    def on_playlist_fetched(self, status, songs):
        if status:
            self.library_tab.display_playlist_songs(status, songs)
            for song in songs:
                self.thumbnail.download_list_thumbnail(song)

    def list_thumbnails(self, image, id_key):
        pixmap = QPixmap()
        pixmap.loadFromData(image)
        icon = QIcon(pixmap)
        self.queue.model.update_thumbnail(id_key, icon)
        self.library_tab.playlist_songs_model.update_thumbnail(id_key, icon)
        self.player_tab.set_list_thumbnail(image, id_key)
        self.mini_player.set_list_thumbnail(image, id_key)
        self.library_tab.set_list_thumbnail(image, id_key)


if __name__ == "__main__":
    start = MainWindow()
    close = start.app.exec()
    sys.exit(close)
