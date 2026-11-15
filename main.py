"""PySide6 catalogue application."""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication, QDialog, QFormLayout, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from database import PROJECT_DIR, authenticate, fetch_catalog, initialise_database

RESOURCES = PROJECT_DIR / "resources"
IMAGES = RESOURCES / "images"
PLACEHOLDER = RESOURCES / "picture.png"
LOGO = RESOURCES / "Мир велосипедов.png"
ICON = RESOURCES / "Мир велосипедов.ico"

def calculate_price(product_id, base_price, cursor):
    try:
        cursor.execute("""
            SELECT COUNT(*) FROM order_items oi
            JOIN orders o ON oi.order_id = o.order_id
            WHERE oi.product_id = %s
            AND o.order_date >= CURRENT_DATE - INTERVAL '1 month'
        """, (product_id,))
        orders_count = cursor.fetchone()[0]
        if orders_count == 0:
            return round(float(base_price) * 0.75, 2)
    except Exception:
        pass
    return float(base_price)

class ProductCard(QFrame):
    def __init__(self, product) -> None:
        super().__init__()
        self.setObjectName("productCard")
        self.setFrameShape(QFrame.StyledPanel)
        
        if product["quantity"] <= 3:
            self.setStyleSheet("background-color: #ff8080; border: 1px solid #70B2AF; border-radius: 6px; margin: 4px; padding: 4px;")
            
        layout = QHBoxLayout(self)
        
        image = QLabel()
        image.setFixedSize(150, 110)
        image.setAlignment(Qt.AlignCenter)
        image_path = IMAGES / (product["image_name"] or "")
        pixmap = QPixmap(str(image_path if image_path.exists() else PLACEHOLDER))
        image.setPixmap(pixmap.scaled(145, 105, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(image)
        
        info = QVBoxLayout()
        name = QLabel(product["name"])
        name.setObjectName("productName")
        info.addWidget(name)
        info.addWidget(QLabel(f"{product['category']} · {product['subcategory']}"))
        info.addWidget(QLabel(f"Производитель: {product['manufacturer']}"))
        info.addWidget(QLabel(product["composition"]))
        stock = "Нет на складе" if product["quantity"] == 0 else f"В наличии: {product['quantity']} шт."
        info.addWidget(QLabel(stock))
        layout.addLayout(info, 1)
        
        price = QLabel(f"от {float(product['minimum_price'] or product['base_price']):,.2f} ₽".replace(",", " "))
        price.setObjectName("price")
        layout.addWidget(price, alignment=Qt.AlignRight | Qt.AlignVCenter)

class MainWindow(QMainWindow):
    def __init__(self, user_id=None, role_id=None, full_name=None) -> None:
        super().__init__()
        self.user_id = user_id
        self.role_id = role_id
        self.full_name = full_name
        
        self.setWindowTitle("Мир велосипедов")
        if ICON.exists():
            self.setWindowIcon(QIcon(str(ICON)))
        self.resize(980, 720)
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        
        # Шапка с логотипом и ФИО
        header = QHBoxLayout()
        logo = QLabel()
        logo_pixmap = QPixmap(str(LOGO))
        if LOGO.exists():
            logo.setPixmap(logo_pixmap.scaledToHeight(55, Qt.SmoothTransformation))
        else:
            logo.setText("Мир велосипедов")
        header.addWidget(logo)
        
        header.addStretch()
        
        # Вывод ФИО (если пользователь авторизован)
        if self.full_name:
            self.name_label = QLabel(f"ФИО: {self.full_name}")
            self.name_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-right: 15px;")
            header.addWidget(self.name_label)
        else:
            self.name_label = QLabel("Гость")
            header.addWidget(self.name_label)
            
        root.addLayout(header)
        
        self.catalog_layout = QVBoxLayout()
        self.catalog_layout.setAlignment(Qt.AlignTop)
        container = QWidget()
        container.setLayout(self.catalog_layout)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)
        root.addWidget(scroll, 1)
        self.statusBar().showMessage("Каталог загружен")
        self.load_catalog()

    def load_catalog(self) -> None:
        while self.catalog_layout.count():
            item = self.catalog_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        products = fetch_catalog()
        for product in products:
            self.catalog_layout.addWidget(ProductCard(product))
        self.statusBar().showMessage(f"Найдено моделей: {len(products)}")

def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(
        """
        QWidget { font-family: Calibri; font-size: 14px; color: #000000; background: #FFFFFF; }
        QPushButton { background: #70B2AF; padding: 7px 12px; border: 0; border-radius: 4px; }
        QPushButton:hover { background: #D2F6E7; }
        #title, #productName { font-weight: bold; font-size: 18px; }
        #productCard { border: 1px solid #70B2AF; border-radius: 6px; margin: 4px; padding: 4px; }
        #price { font-weight: bold; font-size: 16px; }
        QLineEdit, QComboBox { padding: 6px; border: 1px solid #70B2AF; border-radius: 3px; }
        """
    )
    
    from login_window import LoginWindow
    login_win = LoginWindow()
    
    if login_win.exec():
        return app.exec()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())