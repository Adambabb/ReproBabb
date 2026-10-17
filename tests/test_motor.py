import pytest
from unittest.mock import MagicMock, patch
import Motor


@patch("Motor.ytmusicapi.YTMusic")
def test_set_account_success(mock_ytmusic_class):
    success = Motor.set_account("fake_credentials.json")
    assert success is True
    mock_ytmusic_class.assert_called_once_with("fake_credentials.json")


@patch("Motor.ytmusicapi.YTMusic")
def test_set_account_failure(mock_ytmusic_class):
    mock_ytmusic_class.side_effect = [Exception("Invalid file"), MagicMock()]

    success = Motor.set_account("invalid.json")

    assert success is False


@patch("Motor.searcher")
def test_get_user_playlist(mock_searcher):
    mock_searcher.get_library_playlists.return_value = [
        {"title": "Mi Playlist", "playlistId": "PL123", "thumbnails": []}
    ]
    resultado = Motor.get_user_playlist()
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
    song = Motor.music_data(raw)
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
    song = Motor.music_data(raw)
    assert song["status"] == "success"
    assert song["title"] == "Song Title"
    assert song["id"] == "v123"
    assert song["duration"] == 200
    assert song["artists"] == [{"name": "Artist 1"}]


def test_music_data_none():
    song = Motor.music_data(None)
    assert song["status"] == "error"
    assert song["title"] == "Not found"


@patch("Motor.searcher")
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
    songs = Motor.playlist_data("PL123")
    assert len(songs) == 1
    assert songs[0]["id"] == "v1"
    assert songs[0]["setVideoId"] == "sv1"


@patch("Motor.searcher")
def test_playlist_data_empty(mock_searcher):
    mock_searcher.get_playlist.return_value = {"tracks": []}
    songs = Motor.playlist_data("PL123")
    assert len(songs) == 1
    assert songs[0]["status"] == "error"


@patch("Motor.searcher")
def test_song_data_empty_query(mock_searcher):
    assert Motor.song_data("") == []
    assert Motor.song_data("   ") == []


@patch("Motor.searcher")
def test_song_data_success(mock_searcher):
    mock_searcher.search.return_value = [
        {"title": "Result 1", "videoId": "v1"},
        {"title": "Result 2", "videoId": "v2"},
    ]
    results = Motor.song_data("query")
    assert len(results) == 2
    assert results[0]["id"] == "v1"


@patch("Motor.searcher")
def test_song_link_data_success(mock_searcher):
    mock_searcher.get_song.return_value = {"title": "Link Song", "videoId": "v10"}
    song = Motor.song_link_data("v10")
    assert song["title"] == "Link Song"
    assert song["id"] == "v10"


@patch("Motor.searcher")
def test_song_link_data_not_found(mock_searcher):
    mock_searcher.get_song.return_value = None

    song = Motor.song_link_data("invalid_id")

    assert song["status"] == "error"
    assert song["title"] == "Not found"


@patch("Motor.searcher")
def test_add_song_playlist_success(mock_searcher):
    res = Motor.add_song_playlist("PL123", "v1")
    assert res == {"status": "success"}
    mock_searcher.add_playlist_items.assert_called_once_with(
        "PL123", ["v1"], duplicates=True
    )


@patch("Motor.searcher")
def test_add_song_playlist_error(mock_searcher):
    mock_searcher.add_playlist_items.side_effect = Exception("API Error")
    res = Motor.add_song_playlist("PL123", "v1")
    assert res["status"] == "error"


@patch("Motor.searcher")
def test_remove_song_playlist_success(mock_searcher):
    formatted_song = {"id": "v1", "setVideoId": "sv1"}
    res = Motor.remove_song_playlist("PL123", formatted_song)
    assert res == {"status": "success"}
    mock_searcher.remove_playlist_items.assert_called_once_with(
        "PL123", [{"videoId": "v1", "setVideoId": "sv1"}]
    )


@patch("Motor.searcher")
def test_remove_song_playlist_error(mock_searcher):
    mock_searcher.remove_playlist_items.side_effect = Exception(
        "Error al borrar de la playlist"
    )

    formatted_song = {"id": "v1", "setVideoId": "sv1"}
    res = Motor.remove_song_playlist("PL123", formatted_song)

    assert res["status"] == "error"
    assert res["error"] == "Error al borrar de la playlist"


@patch("Motor.song_data")
def test_search_bar_text(mock_song_data):
    Motor.search_bar("rock song")
    mock_song_data.assert_called_once_with("rock song")


@patch("Motor.song_link_data")
def test_search_bar_video_url(mock_song_link_data):
    Motor.search_bar("https://music.youtube.com/watch?v=abc123")
    mock_song_link_data.assert_called_once_with("abc123")


@patch("Motor.playlist_data")
def test_search_bar_playlist_url(mock_playlist_data):
    Motor.search_bar("https://music.youtube.com/playlist?list=PL999")
    mock_playlist_data.assert_called_once_with("PL999")


@patch("Motor.yt_dlp.YoutubeDL")
def test_fetch_stream_success(mock_ydl_class):
    mock_ydl_instance = MagicMock()
    mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
    mock_ydl_instance.extract_info.return_value = {"url": "http://stream.mp3"}

    res = Motor.fetch("v123", download=False)
    assert res == {"url": "http://stream.mp3", "status": "success"}


@patch("Motor.yt_dlp.YoutubeDL")
def test_fetch_error(mock_ydl_class):
    mock_ydl_instance = MagicMock()
    mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
    mock_ydl_instance.extract_info.side_effect = Exception("Download failed")

    res = Motor.fetch("v123")
    assert res["status"] == "error"


@patch("Motor.searcher")
def test_get_similar_songs(mock_searcher):
    mock_searcher.get_watch_playlist.return_value = {
        "tracks": [
            {"title": "Current Song", "videoId": "v1"},
            {"title": "Similar Song 1", "videoId": "v2"},
        ]
    }
    similar = Motor.get_similar_songs("v1")
    assert len(similar) == 1
    assert similar[0]["id"] == "v2"
