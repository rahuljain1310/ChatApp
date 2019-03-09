from PyQt5.QtWebEngineWidgets import QWebEngineView
import sys
from PyQt5.QtWidgets import QWidget, QPushButton, QApplication
from PyQt5.QtCore import QThread, QUrl

PORT = 5000
ROOT_URL = 'http://localhost:{}'.format(PORT)
        
if __name__ == '__main__':    
    qtapp = QApplication(sys.argv)
    webview = QWebEngineView()
    webview.load(QUrl(ROOT_URL))
    webview.show()
    sys.exit(qtapp.exec_())
