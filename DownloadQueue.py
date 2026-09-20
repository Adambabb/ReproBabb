import threading

class DownloadQueue:
    def __init__(self):
        self.next_id = 0
        self.downloads = {}
        self.cancelled_downloads = set()
        self.cancelled_lock = threading.Lock()
        self.update_lock = threading.Lock()

        
    def register_download(self, title):
        self.next_id += 1
        new_id = self.next_id
        self.downloads[new_id] = {"title": title, "status": "pending", "progress": 0}
        return new_id
    
    def update_progress(self, download_id, progress):
        with self.update_lock:
            if download_id in self.downloads:
                self.downloads[download_id]["progress"] = progress
    
    def update_status(self, download_id, status):
        with self.update_lock:
            if download_id in self.downloads:
                self.downloads[download_id]["status"] = status
    
    def cancel_download(self, download_id):
        with self.cancelled_lock:
            self.cancelled_downloads.add(download_id)
            self.update_status(download_id, "cancelled")
    
    def is_cancelled(self, download_id):
        with self.cancelled_lock:
            return download_id in self.cancelled_downloads
        
    def get_data(self):
        with self.update_lock:
            return self.downloads.copy()