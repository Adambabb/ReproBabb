from PySide6.QtWidgets import QDialog, QVBoxLayout
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtCore import QUrl
import time
import hashlib

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout(self)
        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"        
        self.web_view.page().profile().setHttpUserAgent(self.user_agent)
        self.web_view.page().profile().cookieStore().cookieAdded.connect(self.on_cookie_added)
        self.web_view.urlChanged.connect(self.on_url_changed)
        self.web_view.load(QUrl("https://accounts.google.com/ServiceLogin?service=youtube&continue=https://music.youtube.com"))        
        self.collected_cookies={}
        
        self.web_view.settings().setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
        self.web_view.settings().setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        
    def on_cookie_added(self, cookie):
        self.collected_cookies[cookie.name().data().decode()] = cookie.value().data().decode()
    
    def on_url_changed(self, url):
        
        url_str = url.toString()
        required = {"SAPISID", "SID", "HSID", "SSID"}
        
        if "accounts.google.com" not in url_str and "music.youtube.com" in url_str and all(cookie in self.collected_cookies for cookie in required):
            cookie_list = [f"{cookie_name}={cookie_value}" for cookie_name, cookie_value in self.collected_cookies.items()]
            cookie_final_list = "; ".join(cookie_list)
            
            sapisid = self.collected_cookies["SAPISID"]
            timestamp = int(time.time())
            hash_str = f"{timestamp} {sapisid} https://music.youtube.com"
            sapisidhash = hashlib.sha1(hash_str.encode("utf-8")).hexdigest()
            auth_header = f"SAPISIDHASH {timestamp}_{sapisidhash}"

            self.headers_dict = {
                "user-agent": self.user_agent,
                "accept": "*/*",
                "content-type": "application/json",
                "origin": "https://music.youtube.com",
                "cookie": cookie_final_list,
                "x-goog-authuser": "0",
                "authorization": auth_header
            }
            self.accept()

