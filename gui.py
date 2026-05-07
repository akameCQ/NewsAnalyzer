from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTextEdit, QSplitter, QLabel
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from news import NewsData
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class NewsText(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.text_edit = QTextEdit("Loading news...")
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("background-color: black; color: white;")
        layout.addWidget(self.text_edit)

    def update_news(self, text):
        self.text_edit.setPlainText(text)

class PieChartWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.canvas = FigureCanvas(Figure(facecolor="black"))
        layout.addWidget(self.canvas)
        
        self.status_label = QLabel("Genel: Nötr")
        self.status_label.setStyleSheet("color: #00FF00;")
        layout.addWidget(self.status_label)
        
        self.ax = self.canvas.figure.add_subplot(111)
        self.canvas.figure.set_facecolor("black")
        
    
    def update_pie(self, pos, neg, neu):
        self.ax.clear()
        data = [pos, neg, neu]
        colors = ["#00FF00", "#FF0000", "#808080"]
        labels = ["Pozitif", "Negatif", "Nötr"]
        
        self.ax.set_facecolor("black")
        self.ax.pie(data, labels=None, colors=colors, startangle=90)
        self.ax.legend(labels, loc="upper right", facecolor="black", labelcolor="white")
        self.ax.set_title("Duygu Analizi", color="white")
        self.canvas.draw()

        if pos > neg:
            genel = "Pozitif"
        elif neg > pos:
            genel = "Negatif"
        else:
            genel = "Nötr"
        self.status_label.setText(f"Genel: {genel}")

class GridChartWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.canvas = FigureCanvas(Figure(facecolor="black"))
        layout.addWidget(self.canvas)
        self.ax = self.canvas.figure.add_subplot(111)
        self.canvas.figure.set_facecolor("black")
        self.history = []
        

    def add_point(self, pos, neg):
        self.history.append((pos, neg))
        if len(self.history) > 20:
            self.history.pop(0)

        self.ax.clear()
        self.ax.set_facecolor("black")
        self.ax.set_xlim(-1, 1)
        self.ax.set_ylim(0, 20)
        self.ax.axvline(0, color="white", linewidth=1)

        self.ax.tick_params(colors="white")
        self.ax.xaxis.label.set_color("white")
        self.ax.yaxis.label.set_color("white")
        self.ax.title.set_color("white")

        for i, (p, n) in enumerate(self.history):
            y = i + 1
            self.ax.scatter(p, y, color="#00FF00", s=100, label="Pozitif" if i==0 else "")
            self.ax.scatter(-n, y, color="#FF0000", s=100, label="Negatif" if i==0 else "")

        self.ax.set_xlabel("Negatif ←        → Pozitif")
        self.ax.set_ylabel("Son 20 Haber")
        self.ax.set_yticks(range(1, len(self.history)+1))
        self.ax.set_title("Skorlar")
        self.ax.legend(facecolor="black", labelcolor="white")
        self.ax.grid(True, linestyle="--", alpha=0.3, color="white")

        self.canvas.draw()

class DataLoader(QThread):
    pie_signal = pyqtSignal(int, int, int)
    news_signal = pyqtSignal(str)
    grid_signal = pyqtSignal(float, float)

    def run(self):
        news_data = NewsData()
        data, pos, neu, neg, news = news_data.run()
        self.pie_signal.emit(int(pos*100), int(neg*100), int(neu*100))
        self.news_signal.emit(str(news))
        self.grid_signal.emit(pos, neg)

class HomePage(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Üst-Haber / Alt-Pasta+Grafik")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: black; color: #00FF00;")

        self.news_panel = NewsText()
        self.pie_panel = PieChartWidget()
        self.grid_panel = GridChartWidget()

        bottom_splitter = QSplitter(Qt.Horizontal)
        bottom_splitter.setStyleSheet("background-color: black;")
        bottom_splitter.addWidget(self.pie_panel)
        bottom_splitter.addWidget(self.grid_panel)
        bottom_splitter.setSizes([600, 600])

        main_splitter = QSplitter(Qt.Vertical)
        main_splitter.setStyleSheet("background-color: black;")
        main_splitter.addWidget(self.news_panel)
        main_splitter.addWidget(bottom_splitter)
        main_splitter.setSizes([400, 400])

        self.setCentralWidget(main_splitter)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.start_data_loader)
        self.timer.start(30000)

        self.start_data_loader()
        
    def start_data_loader(self):
        self.data_loader = DataLoader()
        self.data_loader.pie_signal.connect(self.pie_panel.update_pie)
        self.data_loader.news_signal.connect(self.news_panel.update_news)
        self.data_loader.grid_signal.connect(self.grid_panel.add_point)
        self.data_loader.start()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = HomePage()
    window.show()
    sys.exit(app.exec_())
