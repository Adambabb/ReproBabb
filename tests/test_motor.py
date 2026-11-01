import pytest
from unittest.mock import MagicMock, patch
import motor


@patch("motor.searcher")
@patch("motor.ytmusicapi.YTMusic")
def test_set_account_success(mock_ytmusic_class, mock_searcher):
    success = motor.set_account("fake_credentials.json")
    assert success is True
    mock_ytmusic_class.assert_called_once_with("fake_credentials.json")


@patch("motor.searcher")
@patch("motor.ytmusicapi.YTMusic")
def test_set_account_failure(mock_ytmusic_class, mock_searcher):
    mock_ytmusic_class.side_effect = [Exception("Invalid file"), MagicMock()]

    success = motor.set_account("invalid.json")

    assert success is False


@patch("motor.searcher")
def test_get_user_playlist(mock_searcher):
    mock_searcher.get_library_playlists.return_value = [
        {"title": "Mi Playlist", "playlistId": "PL123", "thumbnails": []}
    ]
    resultado = motor.get_user_playlist()
    assert len(resultado) == 1
    assert resultado[0]["title"] == "Mi Playlist"
    mock_searcher.get_library_playlists.assert_called_once()


def test_music_data_with_video_details():
    raw = {
        "videoDetails": {
            "title": "Song Title",
            "videoId": "v123",
            "lengthSeconds": "180",
            "thumbnail": {"thumbnails": [{"url": "http://thumb.jpg"}]},
            "author": "Artist Name",
        }
    }
    song = motor.music_data(raw)
    assert song["status"] == "success"
    assert song["title"] == "Song Title"
    assert song["id"] == "v123"
    assert song["duration"] == 180
    assert song["artists"] == "Artist Name"


def test_music_data_with_standard_dict():
    raw = {
        "title": "Song Title",
        "videoId": "v123",
        "duration_seconds": 200,
        "thumbnails": [{"url": "http://thumb.jpg"}],
        "artists": [{"name": "Artist 1"}],
    }
    song = motor.music_data(raw)
    assert song["status"] == "success"
    assert song["title"] == "Song Title"
    assert song["id"] == "v123"
    assert song["duration"] == 200
    assert song["artists"] == [{"name": "Artist 1"}]


def test_music_data_none():
    song = motor.music_data(None)
    assert song["status"] == "error"
    assert song["title"] == "Not found"


@patch("motor.searcher")
def test_playlist_data_success(mock_searcher):
    mock_searcher.get_playlist.return_value = {
        "tracks": [
            {
                "title": "Song 1",
                "videoId": "v1",
                "duration_seconds": 120,
                "setVideoId": "sv1",
            }
        ]
    }
    songs = motor.playlist_data("PL123")
    assert len(songs) == 1
    assert songs[0]["id"] == "v1"
    assert songs[0]["setVideoId"] == "sv1"


@patch("motor.searcher")
def test_playlist_data_empty(mock_searcher):
    mock_searcher.get_playlist.return_value = {"tracks": []}
    songs = motor.playlist_data("PL123")
    assert len(songs) == 1
    assert songs[0]["status"] == "error"


@patch("motor.searcher")
def test_song_data_empty_query(mock_searcher):
    assert motor.song_data("") == []
    assert motor.song_data("   ") == []


@patch("motor.searcher")
def test_song_data_success(mock_searcher):
    mock_searcher.search.return_value = [
        {"title": "Result 1", "videoId": "v1"},
        {"title": "Result 2", "videoId": "v2"},
    ]
    results = motor.song_data("query")
    assert len(results) == 2
    assert results[0]["id"] == "v1"


@patch("motor.searcher")
def test_song_link_data_success(mock_searcher):
    mock_searcher.get_song.return_value = {"title": "Link Song", "videoId": "v10"}
    song = motor.song_link_data("v10")
    assert song["title"] == "Link Song"
    assert song["id"] == "v10"


@patch("motor.searcher")
def test_song_link_data_not_found(mock_searcher):
    mock_searcher.get_song.return_value = None

    song = motor.song_link_data("invalid_id")

    assert song["status"] == "error"
    assert song["title"] == "Not found"


@patch("motor.searcher")
def test_add_song_playlist_success(mock_searcher):
    res = motor.add_song_playlist("PL123", "v1")
    assert res == {"status": "success"}
    mock_searcher.add_playlist_items.assert_called_once_with(
        "PL123", ["v1"], duplicates=True
    )


@patch("motor.searcher")
def test_add_song_playlist_error(mock_searcher):
    mock_searcher.add_playlist_items.side_effect = Exception("API Error")
    res = motor.add_song_playlist("PL123", "v1")
    assert res["status"] == "error"


@patch("motor.searcher")
def test_remove_song_playlist_success(mock_searcher):
    formatted_song = {"id": "v1", "setVideoId": "sv1"}
    res = motor.remove_song_playlist("PL123", formatted_song)
    assert res == {"status": "success"}
    mock_searcher.remove_playlist_items.assert_called_once_with(
        "PL123", [{"videoId": "v1", "setVideoId": "sv1"}]
    )


@patch("motor.searcher")
def test_remove_song_playlist_error(mock_searcher):
    mock_searcher.remove_playlist_items.side_effect = Exception(
        "Error al borrar de la playlist"
    )

    formatted_song = {"id": "v1", "setVideoId": "sv1"}
    res = motor.remove_song_playlist("PL123", formatted_song)

    assert res["status"] == "error"
    assert res["error"] == "Error al borrar de la playlist"


@patch("motor.song_data")
def test_search_bar_text(mock_song_data):
    motor.search_bar("rock song")
    mock_song_data.assert_called_once_with("rock song")


@patch("motor.song_link_data")
def test_search_bar_video_url(mock_song_link_data):
    motor.search_bar("https://music.youtube.com/watch?v=abc123")
    mock_song_link_data.assert_called_once_with("abc123")


@patch("motor.playlist_data")
def test_search_bar_playlist_url(mock_playlist_data):
    motor.search_bar("https://music.youtube.com/playlist?list=PL999")
    mock_playlist_data.assert_called_once_with("PL999")


@patch("motor.yt_dlp.YoutubeDL")
def test_fetch_stream_success(mock_ydl_class):
    mock_ydl_instance = MagicMock()
    mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
    mock_ydl_instance.extract_info.return_value = {"url": "http://stream.mp3"}

    res = motor.fetch("v123", download=False)
    assert res == {"url": "http://stream.mp3", "status": "success"}


@patch("motor.yt_dlp.YoutubeDL")
def test_fetch_error(mock_ydl_class):
    mock_ydl_instance = MagicMock()
    mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
    mock_ydl_instance.extract_info.side_effect = Exception("Download failed")

    res = motor.fetch("v123")
    assert res["status"] == "error"


@patch("motor.searcher")
def test_get_similar_songs(mock_searcher):
    mock_searcher.get_watch_playlist.return_value = {
        "tracks": [
            {"title": "Current Song", "videoId": "v1"},
            {"title": "Similar Song 1", "videoId": "v2"},
        ]
    }
    similar = motor.get_similar_songs("v1")
    assert len(similar) == 1
    assert similar[0]["id"] == "v2"


@patch("motor.yt_dlp.YoutubeDL")
def test_total_bytes(mock_ytDL):
    mock_progress = MagicMock()
    motor.fetch("v1", update_progress_fn=mock_progress)
    hook = mock_ytDL.call_args[0][0]["progress_hooks"][0]
    progress_data = {
        "status": "downloading",
        "downloaded_bytes": 50,
        "total_bytes": 100,
    }
    hook(progress_data)
    mock_progress.assert_called_once_with(50)


@patch("motor.yt_dlp.YoutubeDL")
def test_total_bytes_estimate(mock_ytDL):
    mock_progress = MagicMock()
    motor.fetch("v1", update_progress_fn=mock_progress)
    hook = mock_ytDL.call_args[0][0]["progress_hooks"][0]
    progress_data = {
        "status": "downloading",
        "downloaded_bytes": 50,
        "total_bytes": None,
        "total_bytes_estimate": 100,
    }
    hook(progress_data)
    mock_progress.assert_called_once_with(50)


@patch("motor.yt_dlp.YoutubeDL")
def test_no_total_bytes(mock_ytDL):
    mock_progress = MagicMock()
    motor.fetch("v1", update_progress_fn=mock_progress)
    hook = mock_ytDL.call_args[0][0]["progress_hooks"][0]
    progress_data = {
        "status": "downloading",
        "downloaded_bytes": 50,
        "total_bytes": None,
        "total_bytes_estimate": None,
    }
    assert hook(progress_data) is None
    mock_progress.assert_not_called()


@patch("motor.yt_dlp.YoutubeDL")
def test_total_bytes_estimate_exceeded(mock_ytDL):
    mock_progress = MagicMock()
    motor.fetch("v1", update_progress_fn=mock_progress)
    hook = mock_ytDL.call_args[0][0]["progress_hooks"][0]
    progress_data = {
        "status": "downloading",
        "downloaded_bytes": 1001,
        "total_bytes": None,
        "total_bytes_estimate": 100,
    }
    hook(progress_data)
    mock_progress.assert_called_once_with(100)
