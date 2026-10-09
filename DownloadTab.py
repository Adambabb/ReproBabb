from PySide6.QtWidgets import QWidget, QVBoxLayout, QListView, QMenu, QAbstractItemView, QStyledItemDelegate, QStyle
from PySide6.QtCore import Qt, Signal, QAbstractListModel, QModelIndex, QSize, QRect, QEvent
from PySide6.QtGui import QPainter, QFont, QFontMetrics, QColor, QPen

class DownloadModel(QAbstractListModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.downloads_list = []
        self.downloads_index_map = {}

    def rowCount(self, parent=QModelIndex()):
        return len(self.downloads_list)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self.downloads_list)):
            return None
        item = self.downloads_list[index.row()]
        if role == Qt.UserRole:
            return item
        return None

    def refresh_data(self, data_dict):
        """Refresca los datos y devuelve el índice de la canción que se está descargando activamente."""
        new_items = []
        active_download_index = -1

        for d_id, info in data_dict.items():
            current_status = info.get("status", "pending")

            if d_id not in self.downloads_index_map:
                item = {
                    "id": d_id,
                    "title": info.get("title", "Unknown"),
                    "status": current_status,
                    "progress": info.get("progress", 0)
                }
                new_items.append(item)
            else:
                idx = self.downloads_index_map[d_id]
                old_item = self.downloads_list[idx]
                new_progress = info.get("progress", 0)
                if old_item["status"] != current_status or old_item["progress"] != new_progress:
                    old_item["status"] = current_status
                    old_item["progress"] = new_progress
                    model_idx = self.index(idx)
                    self.dataChanged.emit(model_idx, model_idx, [Qt.UserRole])

            # Detectar cuál se está descargando actualmente
            if current_status == "downloading" and d_id in self.downloads_index_map:
                active_download_index = self.downloads_index_map[d_id]

        if new_items:
            start_row = len(self.downloads_list)
            end_row = start_row + len(new_items) - 1
            self.beginInsertRows(QModelIndex(), start_row, end_row)
            for item in new_items:
                self.downloads_list.append(item)
                idx = len(self.downloads_list) - 1
                self.downloads_index_map[item["id"]] = idx
                if item["status"] == "downloading":
                    active_download_index = idx
            self.endInsertRows()

        return active_download_index


class DownloadItemDelegate(QStyledItemDelegate):
    cancel_requested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

    def sizeHint(self, option, index):
        return QSize(0, 52)

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        item = index.data(Qt.UserRole)
        if not item:
            painter.restore()
            return

        rect = option.rect
        margin = 10

        if option.state & QStyle.State_Selected:
            painter.fillRect(rect, option.palette.highlight())
        elif option.state & QStyle.State_MouseOver:
            hover_color = option.palette.color(option.palette.ColorRole.Highlight)
            hover_color.setAlpha(30)
            painter.fillRect(rect, hover_color)

        title = item.get("title", "")
        status = item.get("status", "pending")
        progress = item.get("progress", 0)

        font_title = QFont()
        font_title.setBold(True)
        painter.setFont(font_title)
        painter.setPen(option.palette.text().color())

        cancel_btn_width = 30
        progress_bar_width = 140
        available_text_width = rect.width() - progress_bar_width - cancel_btn_width - (margin * 4)

        title_rect = QRect(rect.left() + margin, rect.top() + 6, max(50, available_text_width), 18)
        metrics_title = QFontMetrics(font_title)
        elided_title = metrics_title.elidedText(title, Qt.ElideRight, title_rect.width())
        painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignVCenter, elided_title)

        font_status = QFont()
        font_status.setPointSize(8)
        painter.setFont(font_status)
        
        status_colors = {
            "downloading": QColor(59, 130, 246),
            "finished": QColor(34, 197, 94),
            "cancelled": QColor(107, 114, 128),
            "error": QColor(239, 68, 68),
            "pending": QColor(245, 158, 11)
        }
        painter.setPen(status_colors.get(status, QColor(160, 160, 160)))

        status_text = f"Status: {status} ({progress}%)" if status == "downloading" else f"Status: {status}"
        status_rect = QRect(rect.left() + margin, title_rect.bottom() + 2, max(50, available_text_width), 16)
        painter.drawText(status_rect, Qt.AlignLeft | Qt.AlignVCenter, status_text)

        bar_x = rect.right() - cancel_btn_width - progress_bar_width - (margin * 2)
        bar_y = rect.top() + (rect.height() - 10) // 2
        bar_rect = QRect(bar_x, bar_y, progress_bar_width, 10)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(50, 50, 50))
        painter.drawRoundedRect(bar_rect, 5, 5)

        if progress > 0:
            fill_width = int((progress / 100.0) * progress_bar_width)
            fill_rect = QRect(bar_x, bar_y, fill_width, 10)
            painter.setBrush(status_colors.get(status, QColor(59, 130, 246)))
            painter.drawRoundedRect(fill_rect, 5, 5)

        if status in ["downloading", "pending"]:
            x_btn_x = rect.right() - cancel_btn_width - margin
            x_btn_y = rect.top() + (rect.height() - 24) // 2
            x_btn_rect = QRect(x_btn_x, x_btn_y, 24, 24)

            painter.setBrush(QColor(220, 38, 38, 180))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(x_btn_rect, 12, 12)

            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawLine(x_btn_rect.left() + 7, x_btn_rect.top() + 7, x_btn_rect.right() - 7, x_btn_rect.bottom() - 7)
            painter.drawLine(x_btn_rect.left() + 7, x_btn_rect.bottom() - 7, x_btn_rect.right() - 7, x_btn_rect.top() + 7)

        painter.restore()

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
            item = index.data(Qt.UserRole)
            if item and item.get("status") in ["downloading", "pending"]:
                rect = option.rect
                cancel_btn_width = 30
                margin = 10
                x_btn_x = rect.right() - cancel_btn_width - margin
                x_btn_y = rect.top() + (rect.height() - 24) // 2
                x_btn_rect = QRect(x_btn_x, x_btn_y, 24, 24)

                if x_btn_rect.contains(event.pos()):
                    self.cancel_requested.emit(item["id"])
                    return True
        return super().editorEvent(event, model, option, index)


class DownloadTab(QWidget):
    cancel_download_requested = Signal(int)

    def __init__(self):
        super().__init__()
        self.download_vlayout = QVBoxLayout()
        self.setLayout(self.download_vlayout)

        self.download_list = QListView(self)
        self.delegate = DownloadItemDelegate(self.download_list)
        self.delegate.cancel_requested.connect(self.cancel_download_requested.emit)
        self.download_list.setItemDelegate(self.delegate)
        self.download_list.setSelectionMode(QAbstractItemView.SingleSelection)

        self.model = DownloadModel()
        self.download_list.setModel(self.model)

        self.download_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.download_list.customContextMenuRequested.connect(self.context_menu_downloads)

        self.download_vlayout.addWidget(self.download_list)

    def refresh_downloads(self, data):
        active_row = self.model.refresh_data(data)
        # Si hay una descarga en progreso y no está completamente visible, desliza la lista suavemente
        if active_row >= 0:
            idx = self.model.index(active_row)
            self.download_list.scrollTo(idx, QAbstractItemView.EnsureVisible)

    def context_menu_downloads(self, pos):
        index = self.download_list.indexAt(pos)
        if index.isValid():
            item = index.data(Qt.UserRole)
            if item and item.get("status") in ["downloading", "pending"]:
                menu = QMenu()
                cancel_action = menu.addAction("Cancel Download")
                cancel_action.triggered.connect(lambda: self.cancel_download_requested.emit(item["id"]))
                menu.exec(self.download_list.mapToGlobal(pos))