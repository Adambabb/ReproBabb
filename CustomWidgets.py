from PySide6.QtCore import Signal,QPointF,QTimer,Qt
from PySide6.QtWidgets import QWidget,QLabel,QHBoxLayout,QSlider
from PySide6.QtGui import QPainter,QColor,QShortcut,QKeySequence,QPixmap

import random

            
class time_design(QWidget):
    
    time_changed=Signal(int)
    
    def __init__(self,cover_color,song_duration,song_current_time):
        super().__init__()
        self.bars_number=0
        self.bars_height=[0 for i  in range(140) ]
        self.bars_height_timer=QTimer()
        self.bars_height_timer.timeout.connect(self.update_heights)
        self.bar_gap=0
        self.bars_wave=0.0
        self.song_duration=0
        self.song_current_time=0
        self.cover_color=cover_color
        self.cover_color_contrary=cover_color
        self.is_dragging=False
        self.setMinimumHeight(50)
    
    def update_heights(self):
        self.bars_height=[random.uniform(0.1,0.9) for i  in range(140) ]
        self.update()
    
    
    def paintEvent(self,event):
        visaulizer=QPainter(self)
        visaulizer.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.width() >= 800:
            self.bars_number=140
            self.bar_gap=2
        elif self.width() >= 400:
            self.bars_number=70
            self.bar_gap=2
        elif self.width() >= 200:
            self.bars_number=50
            self.bar_gap=2
        else:
            self.bars_number=20
            self.bar_gap=1
        bar_width=(self.width()/self.bars_number)-self.bar_gap
        self.bars_number_color=0
        if self.song_duration >0:
            percent_song_duration=self.song_current_time/self.song_duration
            self.bars_number_color=self.bars_number*percent_song_duration
        for i in range(self.bars_number):
            position_x=i*(bar_width+self.bar_gap)
            bar_pixel_height=self.height() * self.bars_height[i]
            position_y=self.height()-(bar_pixel_height)
            if self.bars_number_color >= i:
                visaulizer.setPen(Qt.PenStyle.NoPen)
                visaulizer.setBrush(self.cover_color)
            else:
                cover_color_alpha=QColor(self.cover_color)
                cover_color_alpha.setAlpha(75)
                visaulizer.setPen(Qt.PenStyle.NoPen)
                visaulizer.setBrush(cover_color_alpha)
            visaulizer.drawRect(position_x,position_y,bar_width,bar_pixel_height)
        if self.song_duration >0:
            round_slider_x=self.width()*(self.song_current_time/self.song_duration)
        else:
            round_slider_x=0
        round_slider_y=self.height()-6
        visaulizer.setPen(Qt.PenStyle.NoPen)
        
        visaulizer.setBrush(self.cover_color_contrary)
        visaulizer.drawEllipse(QPointF(round_slider_x,round_slider_y),6,6)
    
    def mousePressEvent(self, event):
        self.is_dragging=True
        click_x=event.position().x()
        round_slider_percent=click_x/self.width()
        round_slider_new_time=int(round_slider_percent*self.song_duration)
        self.song_current_time=round_slider_new_time
        self.update()
        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        round_slider_new_time=0
        if self.is_dragging==True:
            if event.position().x() > 0 and event.position().x() < self.width():
                click_x=event.position().x()
            else:
                click_x=max(0,min(event.position().x(),self.width()))
            round_slider_percent=click_x/self.width()
            round_slider_new_time=int(round_slider_percent*self.song_duration)
            self.song_current_time=round_slider_new_time
            self.update()
        return super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        self.is_dragging=False
        
        self.time_changed.emit(self.song_current_time)
        return super().mouseReleaseEvent(event)

class volume_design(QWidget):
    
    volume_changed=Signal(int)
    
    def __init__(self,vol_png):
        super().__init__()
        self.volume_slider=QSlider(Qt.Horizontal)
        self.volume_label=QLabel("Vol")
        self.vol_png=QPixmap(vol_png)
        self.volume_label.setPixmap(self.vol_png)
        self.volume_label.setFixedSize(24,24)
        self.volume_layout=QHBoxLayout(self)
        self.volume_layout.addWidget(self.volume_slider,1)
        self.volume_layout.addStretch()
        self.volume_layout.addWidget(self.volume_label)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setValue(50)
        self.volume_slider.setVisible(False)
        self.volume_slider.valueChanged.connect(self.volume_changed.emit)
        self.color=0
        self.shortcut_volume_up = QShortcut(QKeySequence("Up"), self)
        self.shortcut_volume_up.activated.connect(self.volume_up)
        
        self.shortcut_volume_down = QShortcut(QKeySequence("Down"), self)
        self.shortcut_volume_down.activated.connect(self.volume_down)
    
    def enterEvent(self, event):
        self.volume_slider.setVisible(True)
        return super().enterEvent(event)
    
    def leaveEvent(self, event):
        self.volume_slider.setVisible(False)
        return super().leaveEvent(event)
    

    def volume_up(self):
        self.volume_slider.setValue(self.volume_slider.value()+10)

    def volume_down(self):
            self.volume_slider.setValue(self.volume_slider.value()-10)
    
    def color_slider(self,color):
        self.color=color
        hex_color=self.color.name()
        
        self.volume_slider.setStyleSheet(f"""
        QSlider::groove:horizontal {{
            height: 6px;
            background: #444444;
            border-radius: 3px;
        }}
        QSlider::sub-page:horizontal {{
            background: {hex_color};
            border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: {hex_color};
            width: 12px;
            margin-top: -3px;
            margin-bottom: -3px;
            border-radius: 6px;
        }}
    """)