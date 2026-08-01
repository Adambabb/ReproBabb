from PySide6.QtCore import QObject,Signal
import vlc
class AudioController(QObject):

    state_changed = Signal(str)           #
    metadata_ready = Signal(dict)         
    error_occurred = Signal(str)
    vol_changed = Signal(int)  
       
    
    
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
        self._player_State=""
        self._vol=50
        self.player = vlc.MediaPlayer()
        self._event_manager = self.player.event_manager()
        for event in events:
            self._event_manager.event_attach(event,self.getVlcState)
            
    def displayStatus(self):
        new_Status=""
        if self._player_State=="Playing":
            new_Status="Playing"
        elif self._player_State=="Cannot Reproduce":
            new_Status="Cannot Reproduce error"
        elif self._player_State=="Paused":
            new_Status="Paused"
        elif  self._player_State=="Stopped":
            new_Status="Song Stopped"
        elif  self._player_State=="Ended Media":
            new_Status="Ended Song"
        elif self._player_State=="No content":
            new_Status="No content"
        elif self._player_State=="Loading Url" or self._player_State=="Loading Song":
            new_Status="Loading"
        else:
            new_Status="Error"
        if new_Status != self._status:
            self._status=new_Status
            self.state_changed.emit(self._status)
  

    def getVlcState(self,state):
        vlcState=self.player.get_state()
        self.vlcStatus(vlcState)
        
    def vlcStatus(self,state):
        match state:
            case vlc.State.Opening:
                state="Loading Url"
            case vlc.State.Buffering:
                state="Loading Song"
            case vlc.State.NothingSpecial:
                state="No content"
            case  vlc.State.Playing:
                state="Playing"
            case vlc.State.Paused:
                state="Paused"
            case vlc.State.Stopped:
                state="Stopped"
            case vlc.State.Ended:
                state="Ended Media"
            case vlc.State.Error:
                state="Cannot Reproduce"
                self.error_occurred.emit(vlc.libvlc_errmsg() or "Unknown error")            
            case _:
                print("Error")
                state=""
                return
        if self._player_State != state:
            self._player_State=state   
            self.displayStatus()                               

            
    def play(self, url: str):
        media=vlc.Media(url)
        self.player.set_media(media)
        self.player.play()
            


    def pause(self):
            self.player.pause()
  
    def stop(self):
            self.player.stop()

    def set_volume(self, value: int):
        if value >=0 and value <= 100:
            vol3=value*3
            self.player.audio_set_volume(vol3)
            self._vol=value
            self.vol_changed.emit(self._vol)
        else:
            self.player.audio_set_volume(50)
            self._vol=50
            self.vol_changed.emit(self._vol)


    def get_state(self) -> str: return self._status
    def get_Vol(self)-> int: return self._vol
    
    
    
    def pausePlay(self):
        if self._player_State=="Playing":
            self.player.pause()
        else:
            self.player.play()        
