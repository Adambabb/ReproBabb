from PySide6.QtWidgets import QPushButton, QWidget,QVBoxLayout,QListWidget,QListWidgetItem,QLabel,QProgressBar,QFrame,QHBoxLayout
from PySide6.QtCore import Qt, Signal
from numpy import info

class DownloadTab(QWidget):
    cancel_download_requested=Signal(int)
    
    def __init__(self):
        super().__init__()
        self.download_vlayout=QVBoxLayout()
        self.setLayout(self.download_vlayout)
        
        self.download_list=QListWidget()
        self.download_vlayout.addWidget(self.download_list)
        
        self.activeDownloads={}
    
    
    def refresh_downloads(self, data):
        for download_id, info in data.items():
            if download_id not in self.activeDownloads:
                download_item = QListWidgetItem()
                download_row_item = self.download_row(download_id, info)
                download_item.setSizeHint(download_row_item.sizeHint())
                download_item.setData(Qt.UserRole, download_id)
                
                self.download_list.addItem(download_item)
                self.download_list.setItemWidget(download_item, download_row_item)
                
                self.activeDownloads[download_id] = download_row_item
                
                self.download_list.scrollToItem(download_item)
            else:
                row_item = self.activeDownloads[download_id]
                row_item.status_label.setText(info.get("status", ""))
                row_item.progress_bar.setValue(info.get("progress", 0))

   
    def download_row(self,download_id,download_info):
        download_row_frame=QFrame()
        download_song_title=QLabel(download_info.get("title",""))
        download_row_frame.status_label = QLabel(download_info.get("status", ""))
        download_row_frame.progress_bar=QProgressBar()
        download_row_frame.progress_bar.setValue(download_info.get("progress",0))
        cancel_download_button=QPushButton("X")
        cancel_download_button.clicked.connect(lambda: self.cancel_download_requested.emit(download_id))
        download_layout=QHBoxLayout()
        download_layout.addWidget(download_song_title)
        download_layout.addWidget(download_row_frame.status_label)
        download_layout.addWidget(download_row_frame.progress_bar)
        download_layout.addWidget(cancel_download_button)
        download_row_frame.setLayout(download_layout)
        return download_row_frame
