from PySide6.QtWidgets import QDialog, QLineEdit, QPushButton, QVBoxLayout, QLabel, QMessageBox
from database import authenticate

class LoginWindow(QDialog):
    def __init__(self):  # <-- Вот здесь мы убрали 'db'
        super().__init__()
        self.setWindowTitle("Авторизация")
        self.main_window = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Логин:"))
        
        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Введите логин")
        layout.addWidget(self.login_input)
        
        self.login_button = QPushButton("Войти")
        self.login_button.clicked.connect(self.check_login)
        layout.addWidget(self.login_button)
        
        self.setLayout(layout)

    def check_login(self):
        login = self.login_input.text().strip()
        if not login:
            QMessageBox.warning(self, "Ошибка", "Введите логин")
            return
        
        user_data = authenticate(login)
        if user_data:
            self.accept()
            from main import MainWindow
            self.main_window = MainWindow(user_id=user_data['user_id'], role_id=1)
            self.main_window.show()
        else:
            QMessageBox.warning(self, "Ошибка", "Пользователь не найден")