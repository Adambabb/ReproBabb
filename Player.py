from PySide6.QtCore import QObject, Signal

try:
    import vlc
except Exception as error:
    vlc = None
    VLC_IMPORT_ERROR = error


class VlcNotAvailableError(Exception):
    pass


class AudioController(QObject):

    state_changed = Signal(str)
    error_occurred = Signal(str)
    volume_changed = Signal(int)

    def __init__(self):
        if vlc is None:
            raise VlcNotAvailableError(
                f"VLC module is not available: {VLC_IMPORT_ERROR}"
            )
        events = [
            vlc.EventType.MediaPlayerNothingSpecial,
            vlc.EventType.MediaPlayerOpening,
            vlc.EventType.MediaPlayerBuffering,
            vlc.EventType.MediaPlayerPlaying,
            vlc.EventType.MediaPlayerPaused,
            vlc.EventType.MediaPlayerStopped,
            vlc.EventType.MediaPlayerEndReached,
            vlc.EventType.MediaPlayerEncounteredError,
        ]

        super().__init__()
        self.status = "idle"
        self.has_played = False
        self.volume = 100
        try:
            self.instance = vlc.Instance("--no-video", "--quiet")
        except Exception as e:
            raise VlcNotAvailableError(f"Failed to initialize VLC instance: {e}") from e

        if self.instance is None:
            raise VlcNotAvailableError("Failed to create VLC instance.")

        self.player = self.instance.media_player_new()
        self.event_manager = self.player.event_manager()
        for event in events:
            self.event_manager.event_attach(event, self.on_vlc_event)

    def on_vlc_event(self, event):
        vlc_state = self.player.get_state()
        self.process_vlc_state(vlc_state)

    def process_vlc_state(self, state):
        match state:
            case vlc.State.Opening:
                state = "Loading Url"
            case vlc.State.Buffering:
                state = "Loading Song"
            case vlc.State.NothingSpecial:
                state = "No content"
            case vlc.State.Playing:
                self.has_played = True
                state = "Playing"
            case vlc.State.Paused:
                state = "Paused"
            case vlc.State.Stopped:
                state = "Stopped"
            case vlc.State.Ended:
                if self.has_played == True:
                    state = "Ended Media"
                else:
                    state = "Cannot Reproduce"
            case vlc.State.Error:
                state = "Cannot Reproduce"
                self.error_occurred.emit(vlc.libvlc_errmsg() or "Unknown error")
            case _:
                print("Error")
                state = ""
                return
        if self.status != state:
            self.status = state
            self.state_changed.emit(self.status)

    def play(self, url: str):
        self.has_played = False
        media = self.instance.media_new(url)
        self.player.set_media(media)
        self.player.play()

    def pause(self):
        self.player.pause()

    def stop(self):
        self.player.stop()

    def set_volume(self, value: int):
        self.player.audio_set_volume(value)
        self.volume = value
        self.volume_changed.emit(self.volume)

    def get_state(self) -> str:
        return self.status

    def get_volume(self) -> int:
        return self.volume

    def toggle_pause_play(self):
        if self.status == "Playing":
            self.player.pause()
        else:
            self.player.play()

    def get_current_time(self):
        return self.player.get_time()

    def get_length(self):
        return self.player.get_length()

    def set_actual_time(self, new_time):
        self.player.set_time(new_time)
