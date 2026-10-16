from Player import AudioController
from unittest.mock import MagicMock, patch


@patch("Player.vlc")
def test_audio_controller_states(mock_vlc):
    mock_vlc.State.Playing = "FAKE_VLC_STATE_PLAYING"

    player_AudioController = AudioController()

    emitted_signals = []
    player_AudioController.state_changed.connect(emitted_signals.append)

    player_AudioController._process_vlc_state(mock_vlc.State.Playing)

    assert player_AudioController.has_played is True
    assert player_AudioController.get_state() == "Playing"
    assert emitted_signals == ["Playing"]


@patch("Player.vlc")
def test_transition_finished(mock_vlc):
    mock_vlc.State.Ended = "FAKE_VLC_STATE_ENDED"

    player_AudioController = AudioController()

    player_AudioController.has_played = True
    emitted_signals = []
    player_AudioController.state_changed.connect(emitted_signals.append)

    player_AudioController._process_vlc_state(mock_vlc.State.Ended)

    assert player_AudioController.get_state() == "Ended Media"
    assert emitted_signals == ["Ended Media"]


@patch("Player.vlc")
def test_transition_finished_without_play(mock_vlc):
    mock_vlc.State.Ended = "FAKE_VLC_STATE_ENDED"

    player_AudioController = AudioController()

    emitted_signals = []
    player_AudioController.state_changed.connect(emitted_signals.append)

    player_AudioController._process_vlc_state(mock_vlc.State.Ended)

    assert player_AudioController.get_state() == "Cannot Reproduce"
    assert emitted_signals == ["Cannot Reproduce"]


@patch("Player.vlc")
def test_play_song(mock_vlc):
    player_AudioController = AudioController()
    fake_url = "http://fake-stream.com/audio.mp3"
    player_AudioController.play(fake_url)

    assert player_AudioController.has_played is False
    player_AudioController.player.play.assert_called_once()
    player_AudioController.instance.media_new.assert_called_once_with(fake_url)


@patch("Player.vlc")
def test_pause_song(mock_vlc):
    player_AudioController = AudioController()
    player_AudioController.pause()

    player_AudioController.player.pause.assert_called_once()


@patch("Player.vlc")
def test_stop_song(mock_vlc):
    player_AudioController = AudioController()
    player_AudioController.stop()

    player_AudioController.player.stop.assert_called_once()


@patch("Player.vlc")
def test_set_volume(mock_vlc):
    player_AudioController = AudioController()
    new_volume = 75
    volume_emitted = []
    player_AudioController.volume_changed.connect(volume_emitted.append)

    player_AudioController.set_volume(new_volume)

    assert player_AudioController.get_volume() == new_volume
    assert volume_emitted == [new_volume]
    player_AudioController.player.audio_set_volume.assert_called_once_with(new_volume)


@patch("Player.vlc")
def test_toggle_pause_play(mock_vlc):
    player_AudioController = AudioController()

    player_AudioController.status = "Playing"
    player_AudioController.toggle_pause_play()
    player_AudioController.player.pause.assert_called_once()

    player_AudioController.player.pause.reset_mock()
    player_AudioController.player.play.reset_mock()

    player_AudioController.status = "Paused"
    player_AudioController.toggle_pause_play()
    player_AudioController.player.play.assert_called_once()


@patch("Player.vlc")
def test_set_actual_time(mock_vlc):
    player_AudioController = AudioController()
    new_time = 5000
    player_AudioController.set_actual_time(new_time)

    player_AudioController.player.set_time.assert_called_once_with(new_time)
