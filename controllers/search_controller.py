import threading
from PySide6.QtCore import QObject, Signal
import motor


class SearchController(QObject):
    search_completed = Signal(object, int)
    similar_songs_fetched = Signal(list)
    error_search = Signal(str)

    def __init__(self, player_tab, thumbnail_fetcher):
        super().__init__()
        self.player_tab = player_tab
        self.thumbnail_fetcher = thumbnail_fetcher

    def search(self, query, search_version):
        threading.Thread(
            target=self._run_search, daemon=True, args=(query, search_version)
        ).start()

    def _run_search(self, query, search_version):
        try:
            res = motor.search_bar(query)
            self.search_completed.emit(res, search_version)
        except Exception as e:
            print(f"Error searching: {e}")
            self.error_search.emit(str(e))

    def process_search_results(self, res, search_version):
        if search_version != self.player_tab.search_version:
            return
        self.player_tab.search_result(res)
        songs = res if isinstance(res, list) else [res]
        for song in songs:
            if isinstance(song, dict) and song.get("status") == "success":
                self.thumbnail_fetcher.download_list_thumbnail(song)

    def fetch_similar_songs(self, song_data):
        if len(song_data) == 1:
            video_id = song_data[0].get("id")
            threading.Thread(
                target=self._run_similar_songs, daemon=True, args=(video_id,)
            ).start()

    def _run_similar_songs(self, video_id):
        songs = []
        try:
            songs = motor.get_similar_songs(video_id)
            for song in songs:
                if isinstance(song, dict):
                    self.thumbnail_fetcher.download_list_thumbnail(song)
        except Exception as e:
            print(f"Error fetching similar songs: {e}")
            self.error_search.emit(str(e))
        finally:
            self.similar_songs_fetched.emit(songs)
