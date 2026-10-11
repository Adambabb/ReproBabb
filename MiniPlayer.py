import os

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QCloseEvent
from PySide6.QtGui import QFont, QFontMetrics, QIcon, QPixmap
from PySide6.QtWidgets import QAbstractItemView,QFrame,QHBoxLayout,QLabel,QListView,QPushButton,QStyledItemDelegate,QSizePolicy,QStyle,QVBoxLayout,QWidget

from Utils import resource_path


class MiniQueueDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        painter.save()
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        song = index.data(Qt.UserRole)
        if song:
            margin = 8
            icon = index.data(Qt.DecorationRole)
            text_left = option.rect.left() + margin
            if icon and not icon.isNull():
                icon_size = 32
                icon_rect = option.rect.adjusted(
                    margin,
                    (option.rect.height() - icon_size) // 2,
                    0,
                    0,
                )
                icon.paint(
                    painter,
                    icon_rect.left(),
                    icon_rect.top(),
                    icon_size,
                    icon_size,
                )
                text_left = icon_rect.left() + icon_size + margin

            if option.state & QStyle.State_Selected:
                painter.setPen(option.palette.highlightedText().color())
            else:
                painter.setPen(option.palette.text().color())
            font_metrics = QFontMetrics(option.font)
            title = font_metrics.elidedText(
                song.get("title", ""),
                Qt.TextElideMode.ElideRight,
                option.rect.right() - text_left - margin,
            )
            painter.drawText(
                text_left,
                option.rect.top(),
                option.rect.right() - text_left - margin,
                option.rect.height(),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                title,
            )

        painter.restore()

    def sizeHint(self, option, index):
        if not index.isValid():
            return QSize()
        return QSize(option.rect.width(), 40)


class MiniPlayer(QWidget):

    previous_requested = Signal()
    play_pause_toggled = Signal()
    next_requested = Signal()
    shuffle_requested = Signal()
    expanded_requested = Signal()
    queue_song_requested = Signal(list, int)

    def __init__(self, queue_model):
        super().__init__()
        self._cover = QPixmap(resource_path(os.path.join("Assets", "Vinyl-Cover.png")))
        self.current_song_id = None
        self._song_thumbnail_cache = {}
        self.setObjectName("miniPlayer")
        self.setWindowTitle("ReproBabb Mini Player")
        self.setFixedSize(210, 104)
        self.setStyleSheet(
            "#miniPlayer { background-color: #171725; "
            "border: 1px solid #555575; border-radius: 8px; }"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)

        song_layout = QHBoxLayout()
        song_layout.setSpacing(8)
        self.cover_label = QLabel()
        self.cover_label.setFixedSize(34, 34)
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        song_layout.addWidget(self.cover_label)

        self.title_label = QLabel("Nothing Playing")
        self.title_label.setObjectName("title_search_list")
        self.title_label.setWordWrap(True)
        self.title_label.setMaximumHeight(38)
        self.title_label.setToolTip("Nothing Playing")
        title_font = QFont(self.title_label.font())
        title_font.setPointSize(9)
        self.title_label.setFont(title_font)
        song_layout.addWidget(self.title_label, 1)

        self.expand_button = QPushButton("Full")
        self.expand_button.setToolTip("Return to full player")
        self.expand_button.setAccessibleName("Return to full player")
        self.expand_button.clicked.connect(self.expanded_requested.emit)
        song_layout.addWidget(self.expand_button)
        layout.addLayout(song_layout)
        self._update_cover()

        controls_layout = QHBoxLayout()
        controls_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        controls_layout.setSpacing(4)
        self.previous_button = self._icon_button("Previous.png", "Previous")
        self.play_button = self._icon_button("Play.png", "Play or pause")
        self.next_button = self._icon_button("Next.png", "Next")
        self.shuffle_button = self._icon_button("Shuffle.png", "Shuffle")
        self.shuffle_button.setCheckable(True)
        self.previous_button.setFixedSize(27, 23)
        self.play_button.setFixedSize(27, 23)
        self.next_button.setFixedSize(27, 23)
        self.shuffle_button.setFixedSize(27, 23)
        controls_layout.addWidget(self.previous_button)
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.next_button)
        controls_layout.addWidget(self.shuffle_button)
        layout.addLayout(controls_layout)

        self.previous_button.clicked.connect(self.previous_requested.emit)
        self.play_button.clicked.connect(self.play_pause_toggled.emit)
        self.next_button.clicked.connect(self.next_requested.emit)
        self.shuffle_button.clicked.connect(self.shuffle_requested.emit)

        self.queue_toggle = QPushButton("Show queue")
        self.queue_toggle.setFixedHeight(18)
        self.queue_toggle.setCheckable(True)
        self.queue_toggle.toggled.connect(self._toggle_queue)
        layout.addWidget(self.queue_toggle)

        self.queue_panel = QFrame()
        queue_layout = QVBoxLayout(self.queue_panel)
        self.queue_list = QListView()
        self.queue_list.setModel(queue_model)
        self.queue_list.setItemDelegate(MiniQueueDelegate(self.queue_list))
        self.queue_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.queue_list.setMinimumHeight(60)
        self.queue_list.setMaximumHeight(65)
        self.queue_list.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.queue_list.clicked.connect(self._play_queue_item)
        queue_layout.addWidget(self.queue_list)
        self.queue_panel.setVisible(False)
        layout.addWidget(self.queue_panel)
        self.set_playback_state("Stopped")

    def _icon_button(self, icon_name, accessible_name):
        button = QPushButton()
        button.setIcon(QIcon(resource_path(os.path.join("Assets", icon_name))))
        button.setIconSize(QSize(18, 18))
        button.setAccessibleName(accessible_name)
        return button

    def _toggle_queue(self, expanded):
        previous_height = self.height()
        self.queue_panel.setVisible(expanded)
        self.queue_toggle.setText("Hide queue" if expanded else "Show queue")
        self.setFixedHeight(190 if expanded else 104)
        self.move(self.x(), self.y() - (self.height() - previous_height))

    def _play_queue_item(self, index):
        if index.isValid():
            self.queue_song_requested.emit(
                self.queue_list.model().songs_list, index.row()
            )

    def set_song(self, song):
        self.current_song_id = song.get("id") or song.get("videoId")
        if self.current_song_id is not None:
            self.current_song_id = str(self.current_song_id)
        title = song.get("title", "Unknown Title")
        self.title_label.setText(title)
        self.title_label.setToolTip(title)
        if self.current_song_id in self._song_thumbnail_cache:
            self.set_thumbnail(
                self._song_thumbnail_cache[self.current_song_id],
                self.current_song_id,
            )
        else:
            self._cover = QPixmap(
                resource_path(os.path.join("Assets", "Vinyl-Cover.png"))
            )
            self._update_cover()

    def set_thumbnail(self, image, song_id=None):
        if song_id:
            song_id = str(song_id)
            self._song_thumbnail_cache[song_id] = image
        current_song_id = (
            str(self.current_song_id) if self.current_song_id is not None else None
        )
        if song_id and song_id != current_song_id:
            return

        cover = QPixmap()
        if cover.loadFromData(image):
            self._cover = cover
            self._update_cover()

    def set_list_thumbnail(self, image, song_id):
        song_id = str(song_id)
        has_song_cover = song_id in self._song_thumbnail_cache
        self._song_thumbnail_cache.setdefault(song_id, image)
        current_song_id = (
            str(self.current_song_id) if self.current_song_id is not None else None
        )
        if has_song_cover or song_id != current_song_id:
            return
        cover = QPixmap()
        if cover.loadFromData(image):
            self._cover = cover
            self._update_cover()

    def set_playback_state(self, state):
        icon_name = "Pause.png" if state == "Playing" else "Play.png"
        self.play_button.setIcon(
            QIcon(resource_path(os.path.join("Assets", icon_name)))
        )

    def set_shuffle_enabled(self, enabled):
        self.shuffle_button.setChecked(enabled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_cover()

    def closeEvent(self, event: QCloseEvent):
        self.expanded_requested.emit()
        event.ignore()

    def _update_cover(self):
        if not self._cover.isNull():
            scaled = self._cover.scaled(
                self.cover_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.cover_label.setPixmap(scaled)