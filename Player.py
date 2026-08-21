from PySide6.QtCore import QObject,Signal
import vlc

class AudioController(QObject):

    state_changed = Signal(str)
    error_occurred = Signal(str)
    volume_changed = Signal(int)  
       
    
    
    def __init__(self):
        events=[vlc.EventType.MediaPlayerNothingSpecial,
                    vlc.EventType.MediaPlayerOpening,
                    vlc.EventType.MediaPlayerBuffering, 
                   vlc.EventType.MediaPlayerPlaying, 
                    vlc.EventType.MediaPlayerPaused,
                    vlc.EventType.MediaPlayerStopped, 
                    vlc.EventType.MediaPlayerEndReached, 
                    vlc.EventType.MediaPlayerEncounteredError]
        
        super().__init__()
        self._status = "idle"
        self._has_played=False
        self._volume=50
        self._instance = vlc.Instance('--no-video', '--quiet')  
        self.player = self._instance.media_player_new()      
        self._event_manager = self.player.event_manager()
        for event in events:
            self._event_manager.event_attach(event,self._on_vlc_event)

    def _on_vlc_event(self,event):
        vlc_state=self.player.get_state()
        self._process_vlc_state(vlc_state)
        
    def _process_vlc_state(self,state):
        match state:
            case vlc.State.Opening:
                state="Loading Url"
            case vlc.State.Buffering:
                state="Loading Song"
            case vlc.State.NothingSpecial:
                state="No content"
            case  vlc.State.Playing:
                self._has_played=True
                state="Playing"
            case vlc.State.Paused:
                state="Paused"
            case vlc.State.Stopped:
                state="Stopped"
            case vlc.State.Ended:
                if  self._has_played==True:
                    state="Ended Media"
                else:
                    state="Cannot Reproduce"
            case vlc.State.Error:
                state="Cannot Reproduce"
                self.error_occurred.emit(vlc.libvlc_errmsg() or "Unknown error")            
            case _:
                print("Error")
                state=""
                return
        if self._status != state:
            self._status=state   
            self.state_changed.emit(self._status)                          

            
    def play(self, url: str):
        self._has_played=False
        media = self._instance.media_new(url)
        self.player.set_media(media)
        self.player.play()
            


    def pause(self):
            self.player.pause()
  
    def stop(self):
            self.player.stop()

    def set_volume(self, value: int):
            self.player.audio_set_volume(value)
            self._volume=value
            self.volume_changed.emit(self._volume)



    def get_state(self) -> str: return self._status
    def get_volume(self)-> int: return self._volume
    
    
    
    def toggle_pause_play(self):
        if self._status=="Playing":
            self.player.pause()
        else:
            self.player.play()        

    def get_current_time(self):
        return self.player.get_time()
    
    def get_length(self):
            return self.player.get_length()

    def set_actual_time(self,new_time):
        self.player.set_time(new_time)
