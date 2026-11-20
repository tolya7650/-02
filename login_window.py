from PySide6.QtWidgets import QDialog, QLineEdit, QPushButton, QVBoxLayout, QLabel, QMessageBox
import psycopg

# --- Функция валидации (Задание 1) ---
def validate_login(raw):
    login = raw.strip()
    if not login:
        return None, "Введите логин (пробелы не считаются)"
    if len(login) < 3:
        return None, "Логин должен содержать минимум 3 символа"
    return login, None

class LoginWindow(QDialog):
    def __init__(self):
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
        # --- ЗАДАНИЕ 1: Используем validate_login ---
        login, error = validate_login(self.login_input.text())
        if error:
            QMessageBox.critical(self, "Ошибка", error)
            return
        
        try:
            conn = psycopg.connect("host=localhost port=5432 dbname=formadessert user=postgres password=123")
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, role_id, last_name, first_name, middle_name FROM users WHERE login = %s", (login,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                user_id, role_id, last_name, first_name, middle_name = result
                parts = [last_name, first_name]
                if middle_name:
                    parts.append(middle_name)
                full_name = " ".join(parts)
                
                # Information при успешном входе (из прошлой пары)
                QMessageBox.information(self, "Информация", f"Добро пожаловать, {full_name}!")
                
                self.accept()
                from main import MainWindow
                self.main_window = MainWindow(user_id=user_id, role_id=role_id, full_name=full_name)
                self.main_window.show()
            else:
                QMessageBox.critical(self, "Ошибка", "Пользователь не найден")
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка БД: {e}")