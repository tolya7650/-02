import sys
import psycopg
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtCore import Qt

# --- ФУНКЦИЯ ДЛЯ ЗАДАНИЯ 3.1 ---
def calculate_price(product_id, base_price, cursor):
    try:
        # Ищем заказы за предыдущий месяц
        cursor.execute("""
            SELECT COUNT(*) FROM order_items oi
            JOIN orders o ON oi.order_id = o.order_id
            WHERE oi.product_id = %s
            AND o.order_date >= CURRENT_DATE - INTERVAL '1 month'
        """, (product_id,))
        orders_count = cursor.fetchone()[0]
        if orders_count == 0:
            return round(base_price * 0.75, 2) # Скидка 25% с округлением
    except Exception as e:
        print(f"Ошибка в calculate_price: {e}")
    return base_price

class CatalogWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ФормаДесерт - Каталог")
        self.resize(800, 600)
        
        # Стиль: Шрифт Calibri (Задание 3.4)
        self.setStyleSheet("background-color: #f9f9f9; font-family: 'Calibri';")
        
        layout = QVBoxLayout()
        
        title = QLabel("Каталог товаров")
        title.setFont(QFont("Calibri", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        scroll.setWidget(self.scroll_content)
        layout.addWidget(scroll)
        
        self.setLayout(layout)
        self.load_data()

    def load_data(self):
        try:
            # Подключение к вашей БД
            conn = psycopg.connect("host=localhost port=5432 dbname=formadessert user=postgres password=123")
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT p.product_id, p.name, p.price, COALESCE(SUM(si.quantity), 0) AS total_quantity
                FROM products p
                LEFT JOIN stock_items si ON p.product_id = si.product_id
                GROUP BY p.product_id
                LIMIT 5;
            """)
            products = cursor.fetchall()
            
            for prod in products:
                p_id, name, price, quantity = prod
                final_price = calculate_price(p_id, price, cursor)
                self.create_card(name, final_price, quantity)
                
            conn.close()
        except Exception as e:
            print(f"Ошибка БД: {e}")
            # Если БД не подключилась, показываем заглушки
            self.create_card("Тестовый торт", 1000.0, 2)

    def create_card(self, name, price, quantity):
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet("background-color: white; border: 1px solid #ddd; border-radius: 8px; margin: 5px;")
        
        # Подсветка #ff8080 при остатке <= 3 (Задание 3.4)
        if quantity <= 3:
            card.setStyleSheet("background-color: #ff8080; border: 1px solid #ddd; border-radius: 8px; margin: 5px;")
            
        card_layout = QHBoxLayout()
        
        # Изображение слева (Задание 3.3)
        img_label = QLabel()
        pixmap = QPixmap("picture.png")
        if pixmap.isNull():
            img_label.setText("Нет\nфото")
            img_label.setFixedSize(100, 100)
            img_label.setStyleSheet("background-color: #eee; text-align: center;")
            img_label.setAlignment(Qt.AlignCenter)
        else:
            img_label.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio))
        card_layout.addWidget(img_label)
        
        # Текст посередине
        text_layout = QVBoxLayout()
        title_label = QLabel(f"Производство: Кондитерская\n{name}")
        title_label.setFont(QFont("Calibri", 12, QFont.Bold))
        
        info_label = QLabel(f"Категория: Выпечка\nКоличество: {quantity}\nСостав: Мука, сахар, яйца")
        info_label.setFont(QFont("Calibri", 10))
        
        text_layout.addWidget(title_label)
        text_layout.addWidget(info_label)
        card_layout.addLayout(text_layout)
        
        # Цена справа (Задание 3.3)
        price_label = QLabel(f"{price} руб.")
        price_label.setFont(QFont("Calibri", 14, QFont.Bold))
        price_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        card_layout.addWidget(price_label)
        
        card.setLayout(card_layout)
        self.scroll_layout.addWidget(card)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CatalogWindow()
    window.show()
    sys.exit(app.exec())