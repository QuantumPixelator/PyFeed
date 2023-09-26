import sys
import json
import feedparser
import re
from html import unescape
import urllib.request
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QComboBox, QLineEdit, QLabel, QHBoxLayout, QMessageBox, QMenu, QFileDialog
from PySide6.QtWebEngineWidgets import QWebEngineView

DARK_STYLE = """
    QWidget {
        background-color: #2E2E2E;
        border-radius: 5px;
        color: #FFFFFF;
    }
    QPushButton {
        background-color: #454545;
        border-radius: 5px;
        border: none;
        color: white;
        padding: 5px;
    }
    QPushButton:hover {
        background-color: #5A5A5A;
    }
    QLineEdit {
        background-color: #454545;
        border-radius: 5px;
        border: none;
        color: white;
    }
    QComboBox {
        background-color: #454545;
        border-radius: 5px;
        border: none;
        color: white;
    }
    QComboBox QAbstractItemView {
        background-color: #454545;
        border-radius: 5px;
        color: white;
    }
"""


class CustomWebView(QWebEngineView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_custom_context_menu)

    def show_custom_context_menu(self, pos):
        context_menu = QMenu(self)
        save_image_action = context_menu.addAction("Save Image")
        save_image_action.triggered.connect(lambda: self.save_image(pos))
        context_menu.exec_(self.mapToGlobal(pos))

    def save_image(self, pos):
        js_code = f"document.elementFromPoint({pos.x()}, {pos.y()}).src;"
        self.page().runJavaScript(js_code, 0, lambda url: self.download_image(url))


    def download_image(self, image_url: str):
        if image_url:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*)")
            if file_path:
                urllib.request.urlretrieve(image_url, file_path)
                QMessageBox.information(self, "Image Saved", f"Image has been saved to {file_path}")


class RSSReader(QMainWindow):
    def __init__(self):
        super().__init__()

        self.feeds = {}
        self.current_feed_html = ''
        self.initUI()
        self.load_feeds()

    def initUI(self):
        self.setStyleSheet(DARK_STYLE)
        self.setWindowTitle('PyFeed, RSS Reader')
        self.setWindowIcon(QIcon('icon.png'))
        self.resize(800, 600)
        
        self.dropdown = QComboBox()
        self.fetch_button = QPushButton('Fetch RSS Feed', self)
        self.fetch_button.clicked.connect(self.fetch_rss)
        self.back_button = QPushButton('Back', self)
        self.back_button.clicked.connect(self.go_back)
        
        # Create a horizontal layout for the combobox and buttons
        top_row_layout = QHBoxLayout()
        top_row_layout.addWidget(self.dropdown)
        top_row_layout.addWidget(self.fetch_button)
        top_row_layout.addWidget(self.back_button)
        
        self.feed_name_input = QLineEdit()
        self.feed_url_input = QLineEdit()
        self.add_button = QPushButton('Add Feed', self)
        self.add_button.clicked.connect(self.add_feed)
        self.remove_button = QPushButton('Remove Selected Feed', self)
        self.remove_button.clicked.connect(self.remove_feed)

        self.web_view = CustomWebView()

        add_feed_layout = QHBoxLayout()
        add_feed_layout.addWidget(QLabel('Name:'))
        add_feed_layout.addWidget(self.feed_name_input)
        add_feed_layout.addWidget(QLabel('URL:'))
        add_feed_layout.addWidget(self.feed_url_input)
        add_feed_layout.addWidget(self.add_button)
        add_feed_layout.addWidget(self.remove_button)

        layout = QVBoxLayout()
        layout.addLayout(top_row_layout)  # Add the top row layout here
        layout.addLayout(add_feed_layout)
        layout.addWidget(self.web_view)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.show()

    def load_feeds(self):
        try:
            with open('feeds.json', 'r') as file:
                self.feeds = json.load(file)
                self.dropdown.addItems(self.feeds.keys())
        except FileNotFoundError:
            QMessageBox.warning(self, 'File Not Found', 'The feeds.json file was not found.')
        except json.JSONDecodeError:
            QMessageBox.warning(self, 'Error', 'The feeds.json file contains invalid JSON data.')

    def save_feeds(self):
        try:
            with open('feeds.json', 'w') as file:
                json.dump(self.feeds, file)
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'An error occurred while saving the feeds: {str(e)}')

    def fetch_rss(self):
        selected_feed_name = self.dropdown.currentText()
        url = self.feeds[selected_feed_name]
        feed = feedparser.parse(url)
        result = ''
        for post in feed.entries:
            title = post.title
            link = post.link
            content_dict = post.get('content', [{}])[0]
            content = unescape(content_dict.get('value', ''))
            images = re.findall('<img [^>]*src="([^"]*)', content)
            images_html = ''.join([f'<img src="{img}" />' for img in images])
            result += f"<h3><a href='{link}' onclick=\"window.open('{link}', '_self')\">{title}</a></h3>{images_html}<hr>"
        self.current_feed_html = result
        self.web_view.setHtml(result)

    def add_feed(self):
        name = self.feed_name_input.text()
        url = self.feed_url_input.text()
        if name and url:
            self.feeds[name] = url
            self.dropdown.addItem(name)
            self.save_feeds()
            self.feed_name_input.clear()
            self.feed_url_input.clear()

    def remove_feed(self):
        name = self.dropdown.currentText()
        if name in self.feeds:
            del self.feeds[name]
            self.dropdown.removeItem(self.dropdown.currentIndex())
            self.save_feeds()

    def go_back(self):
        if self.current_feed_html:
            self.web_view.setHtml(self.current_feed_html)

app = QApplication(sys.argv)
window = RSSReader()
sys.exit(app.exec())
