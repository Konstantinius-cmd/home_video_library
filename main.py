import sys
import uuid
import psycopg2
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QDialog, QLabel, QLineEdit, QMessageBox,
    QTabWidget, QComboBox, QDateTimeEdit
)
from PySide6.QtCore import QDateTime

# Конфигурация подключения к базе данных
DB_CONFIG = {
    "dbname": "home_video_library",
    "user": "home_video_library",
    "password": "1234",
    "host": "localhost",
    "port": 5432
}

MIN_YEAR = 1895  # Минимальный год
MIN_DURATION = 1  # Минимальная длительность в минутах

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)

    def fetch_all(self, query, params=None):
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall(), [desc[0] for desc in cur.description]

    def execute(self, query, params):
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            self.conn.commit()

class AddSourceDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Добавить источник")
        layout = QVBoxLayout()

        self.name_input = QLineEdit()
        self.link_input = QLineEdit()

        layout.addWidget(QLabel("Название"))
        layout.addWidget(self.name_input)
        layout.addWidget(QLabel("Ссылка"))
        layout.addWidget(self.link_input)

        btn_save = QPushButton("Сохранить")
        btn_save.clicked.connect(self.validate_and_accept)
        layout.addWidget(btn_save)

        self.setLayout(layout)

    def validate_and_accept(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Поле 'Название' не может быть пустым")
            return
        self.accept()

    def get_data(self):
        return self.name_input.text(), self.link_input.text()

class AddVideoDialog(QDialog):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Добавить видео")
        layout = QVBoxLayout()

        self.title_input = QLineEdit()
        self.author_input = QLineEdit()
        self.year_input = QLineEdit()
        self.duration_input = QLineEdit()
        self.source_combo = QComboBox()
        self.file_path_input = QLineEdit()

        layout.addWidget(QLabel("Название"))
        layout.addWidget(self.title_input)
        layout.addWidget(QLabel("Автор"))
        layout.addWidget(self.author_input)
        layout.addWidget(QLabel("Год"))
        layout.addWidget(self.year_input)
        layout.addWidget(QLabel("Длительность (мин)"))
        layout.addWidget(self.duration_input)
        layout.addWidget(QLabel("Источник"))
        layout.addWidget(self.source_combo)
        layout.addWidget(QLabel("Путь к файлу"))
        layout.addWidget(self.file_path_input)

        self.load_sources()

        btn_save = QPushButton("Сохранить")
        btn_save.clicked.connect(self.validate_and_accept)
        layout.addWidget(btn_save)
        self.setLayout(layout)

    def load_sources(self):
        try:
            sources, _ = self.db.fetch_all('SELECT id_источника, название FROM "Источники" ORDER BY название')
            for source in sources:
                self.source_combo.addItem(source[1], source[0])
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить источники: {str(e)}")

    def validate_and_accept(self):
        # Проверка поля "Название"
        if not self.title_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Поле 'Название' не может быть пустым")
            return

        # Проверка поля "Год"
        try:
            year = int(self.year_input.text())
            if year < MIN_YEAR:
                QMessageBox.warning(self, "Ошибка", f"Год должен быть не меньше {MIN_YEAR}")
                return
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Поле 'Год' должно содержать целое число")
            return

        # Проверка поля "Длительность"
        try:
            duration = int(self.duration_input.text())
            if duration < MIN_DURATION:
                QMessageBox.warning(self, "Ошибка", f"Длительность должна быть не меньше {MIN_DURATION} минут")
                return
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Поле 'Длительность' должно содержать целое число")
            return

        # Если все проверки пройдены, закрываем диалог
        self.accept()

    def get_data(self):
        return (
            self.title_input.text(), self.author_input.text(),
            int(self.year_input.text()), int(self.duration_input.text()),
            self.source_combo.currentData(), self.file_path_input.text()
        )

class AddEventDialog(QDialog):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Добавить событие")
        layout = QVBoxLayout()

        self.event_type = QComboBox()
        self.event_type.addItems(["Добавлено", "Просмотрено", "Пересмотрено", "Удалено", "Архивировано", "Перемещено"])

        self.datetime_input = QDateTimeEdit(QDateTime.currentDateTime())
        self.datetime_input.setCalendarPopup(True)

        self.note_input = QLineEdit()
        self.video_combo = QComboBox()

        layout.addWidget(QLabel("Тип события"))
        layout.addWidget(self.event_type)
        layout.addWidget(QLabel("Дата и время"))
        layout.addWidget(self.datetime_input)
        layout.addWidget(QLabel("Примечание"))
        layout.addWidget(self.note_input)
        layout.addWidget(QLabel("Видео"))
        layout.addWidget(self.video_combo)

        self.load_videos()

        btn_save = QPushButton("Сохранить")
        btn_save.clicked.connect(self.accept)
        layout.addWidget(btn_save)
        self.setLayout(layout)

    def load_videos(self):
        try:
            videos, _ = self.db.fetch_all('SELECT id_видео, название FROM "Видео" ORDER BY название')
            for video in videos:
                self.video_combo.addItem(video[1], video[0])
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить видео: {str(e)}")

    def get_data(self):
        return (
            self.event_type.currentText(),
            self.datetime_input.dateTime().toString("yyyy-MM-dd HH:mm:ss"),
            self.note_input.text(), self.video_combo.currentData()
        )


class AddStatusDialog(QDialog):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Добавить статус")
        layout = QVBoxLayout()

        # Выпадающий список для выбора статуса
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Добавлено", "Просмотрено", "В коллекции", "Удалено", "Архивировано"])
        layout.addWidget(QLabel("Статус"))
        layout.addWidget(self.status_combo)

        # Выбор видео
        self.video_combo = QComboBox()
        layout.addWidget(QLabel("Видео"))
        layout.addWidget(self.video_combo)
        self.load_videos()

        # Кнопка "Сохранить"
        btn_save = QPushButton("Сохранить")
        btn_save.clicked.connect(self.accept)
        layout.addWidget(btn_save)

        self.setLayout(layout)

    def load_videos(self):
        try:
            videos, _ = self.db.fetch_all('SELECT id_видео, название FROM "Видео" ORDER BY название')
            for video in videos:
                self.video_combo.addItem(video[1], video[0])
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить видео: {str(e)}")

    def get_data(self):
        return self.status_combo.currentText(), self.video_combo.currentData()

class TableTab(QWidget):
    def __init__(self, db, table_name, add_dialog_cls, insert_query):
        super().__init__()
        self.db = db
        self.table_name = table_name
        self.add_dialog_cls = add_dialog_cls
        self.insert_query = insert_query
        layout = QVBoxLayout()
        self.table = QTableWidget()
        button_row = QHBoxLayout()

        # Кнопка "Обновить"
        btn_reload = QPushButton(QIcon.fromTheme("view-refresh"), "Обновить")
        btn_reload.clicked.connect(self.load_data)
        button_row.addWidget(btn_reload)

        # Кнопка "Добавить"
        btn_add = QPushButton(QIcon.fromTheme("list-add"), "Добавить")
        btn_add.clicked.connect(self.add_record)
        button_row.addWidget(btn_add)

        # Кнопка "Удалить"
        btn_delete = QPushButton(QIcon.fromTheme("list-remove"), "Удалить")
        btn_delete.clicked.connect(self.delete_record)
        button_row.addWidget(btn_delete)

        layout.addWidget(self.table)
        layout.addLayout(button_row)
        self.setLayout(layout)
        self.load_data()

    def load_data(self):
        rows, columns = self.db.fetch_all(f'SELECT * FROM "{self.table_name}" ORDER BY 1')
        self.table.setRowCount(len(rows))
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(val)))

    def add_record(self):
        # Проверяем, принимает ли конструктор диалогового окна параметр db
        if "db" in self.add_dialog_cls.__init__.__code__.co_varnames:
            dialog = self.add_dialog_cls(self.db)
        else:
            dialog = self.add_dialog_cls()

        if dialog.exec():
            data = dialog.get_data()
            try:
                self.db.execute(self.insert_query, (str(uuid.uuid4()), *data))
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def delete_record(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Предупреждение", "Пожалуйста, выберите запись для удаления")
            return

        id_col = self.table.horizontalHeaderItem(0).text()
        id_value = self.table.item(selected_row, 0).text()

        confirm = QMessageBox.question(self, "Подтверждение", f"Удалить запись с ID {id_value}?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            try:
                self.db.execute(f'DELETE FROM "{self.table_name}" WHERE "{id_col}" = %s', (id_value,))
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка удаления", str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Домашняя видеотека")
        self.resize(1000, 700)
        self.db = Database()

        # Применяем глобальный стиль
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #ccc;
                background: white;
            }
            QTabBar::tab {
                background: #e0e0e0;
                padding: 10px;
                border: 1px solid #ccc;
                border-bottom-color: transparent;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom-color: white;
            }
            QPushButton {
                background-color: #0078d7;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #005bb5;
            }
            QLineEdit, QComboBox, QDateTimeEdit {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QTableWidget {
                gridline-color: #ccc;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 5px;
                border: 1px solid #ccc;
            }
        """)

        self.db = Database()

        tabs = QTabWidget()

        tabs.addTab(
            TableTab(
                self.db,
                "Видео",
                AddVideoDialog,
                'INSERT INTO "Видео" (id_видео, название, автор, год, длительность, источник_id, файл_путь) VALUES (%s, %s, %s, %s, %s, %s, %s)'
            ),
            "Видео"
        )

        tabs.addTab(
            TableTab(
                self.db,
                "Источники",
                AddSourceDialog,
                'INSERT INTO "Источники" (id_источника, название, ссылка) VALUES (%s, %s, %s)'
            ),
            "Источники"
        )

        tabs.addTab(
            TableTab(
                self.db,
                "События",
                AddEventDialog,
                'INSERT INTO "События" (id_события, тип_события, дата, примечание, видео_id) VALUES (%s, %s, %s, %s, %s)'
            ),
            "События"
        )

        tabs.addTab(
            TableTab(
                self.db,
                "Статус",
                AddStatusDialog,
                'INSERT INTO "Статус" (id_статуса, статус, видео_id) VALUES (%s, %s, %s)'
            ),
            "Статус"
        )

        self.setCentralWidget(tabs)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())