"""PySide6 catalogue application."""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QWidget, QVBoxLayout, QPushButton, QHBoxLayout,
    QLabel, QScrollArea, QFrame, QMessageBox, QLineEdit, QComboBox, QDialog
)

from database import PROJECT_DIR, fetch_catalog, fetch_product_by_id, authenticate, fetch_categories

RESOURCES = PROJECT_DIR / "resources"
IMAGES = RESOURCES / "images"
PLACEHOLDER = RESOURCES / "picture.png"
LOGO = RESOURCES / "Мир велосипедов.png"
ICON = RESOURCES / "Мир велосипедов.ico"


class ProductCardDialog(QDialog):
    def __init__(self, product_id, parent=None):
        super().__init__(parent)
        self.product_id = product_id
        self.setWindowTitle("Карточка товара")
        self.setMinimumWidth(400)
        
        self.product = fetch_product_by_id(product_id)
        
        layout = QVBoxLayout(self)
        
        if self.product:
            name = QLabel(self.product["name"])
            name.setStyleSheet("font-weight: bold; font-size: 18px;")
            layout.addWidget(name)
            
            price = QLabel(f"Цена: {self.product['price']} ₽")
            price.setStyleSheet("font-size: 16px;")
            layout.addWidget(price)
            
            desc = QLabel(self.product["description"])
            desc.setWordWrap(True)
            layout.addWidget(desc)
        else:
            layout.addWidget(QLabel("Товар не найден"))

        self.variant_combo = QComboBox()
        self.variant_combo.addItem("Красный")
        self.variant_combo.addItem("Синий")
        self.variant_combo.addItem("Зелёный")
        layout.addWidget(QLabel("Вариант:"))
        layout.addWidget(self.variant_combo)

        add_button = QPushButton("Добавить в корзину")
        add_button.clicked.connect(self.on_add_clicked)
        layout.addWidget(add_button)

    def on_add_clicked(self):
        QMessageBox.information(self, "Этап разработки", "Корзина будет подключена в РТ 19")


class ProductCard(QFrame):
    def __init__(self, product, parent_window) -> None:
        super().__init__()
        self.parent_window = parent_window
        self.setObjectName("productCard")
        self.setFrameShape(QFrame.StyledPanel)
        
        if product["quantity"] <= 3:
            self.setStyleSheet("background-color: #ff8080; border: 1px solid #70B2AF; border-radius: 6px; margin: 4px; padding: 4px;")
            
        layout = QHBoxLayout(self)
        
        image = QLabel()
        image.setFixedSize(150, 110)
        image.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(str(PLACEHOLDER))
        if not pixmap.isNull():
            image.setPixmap(pixmap.scaled(145, 105, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            image.setText("Нет фото")
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

        # Делаем всю карточку кликабельной
        self.mousePressEvent = lambda event: self.open_card()

    def open_card(self):
        dialog = ProductCardDialog(self.parent_window.current_product_id, self.parent_window)
        dialog.exec()


class MainWindow(QMainWindow):
    def __init__(self, user_id=None, role_id=None, full_name=None) -> None:
        super().__init__()
        self.user_id = user_id
        self.role_id = role_id
        self.full_name = full_name
        self.current_product_id = None
        
        self.setWindowTitle("Мир велосипедов")
        if ICON.exists():
            self.setWindowIcon(QIcon(str(ICON)))
        self.resize(980, 720)
        
        self.stacked_widget = QStackedWidget()
        
        self.catalog_page = QWidget()
        self.product_page = QWidget()
        self.orders_page = QWidget()
        
        self.setup_catalog_page()
        self.setup_product_page()
        self.setup_orders_page()
        
        self.stacked_widget.addWidget(self.catalog_page)
        self.stacked_widget.addWidget(self.product_page)
        self.stacked_widget.addWidget(self.orders_page)
        
        self.back_button = QPushButton("Назад")
        self.back_button.clicked.connect(self.go_back)
        self.back_button.setVisible(False)
        
        header = QHBoxLayout()
        logo = QLabel()
        logo_pixmap = QPixmap(str(LOGO))
        if not logo_pixmap.isNull():
            logo.setPixmap(logo_pixmap.scaledToHeight(55, Qt.SmoothTransformation))
        else:
            logo.setText("Мир велосипедов")
        header.addWidget(logo)
        
        header.addStretch()
        
        self.btn_product = QPushButton("Карточка товара")
        self.btn_product.clicked.connect(lambda: self.switch_page(1))
        header.addWidget(self.btn_product)
        
        self.btn_orders = QPushButton("Заказы")
        self.btn_orders.clicked.connect(lambda: self.switch_page(2))
        header.addWidget(self.btn_orders)
        
        if self.full_name:
            self.name_label = QLabel(f"ФИО: {self.full_name}")
            self.name_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-right: 15px;")
            header.addWidget(self.name_label)
        else:
            self.name_label = QLabel("Гость")
            header.addWidget(self.name_label)
        
        layout = QVBoxLayout()
        layout.addLayout(header)
        layout.addWidget(self.back_button)
        layout.addWidget(self.stacked_widget)
        
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        self.switch_page(0)
        self.load_catalog()

    def closeEvent(self, event):
        reply = QMessageBox.warning(
            self, "Предупреждение", 
            "Вы уверены, что хотите выйти?", 
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def setup_catalog_page(self):
        layout = QVBoxLayout(self.catalog_page)
        layout.setAlignment(Qt.AlignTop)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск...")
        self.search_input.textChanged.connect(self.load_catalog)
        layout.addWidget(self.search_input)
        
        self.category_combo = QComboBox()
        self.category_combo.addItems(fetch_categories())
        self.category_combo.currentIndexChanged.connect(self.load_catalog)
        layout.addWidget(self.category_combo)
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["По возрастанию", "По убыванию"])
        self.sort_combo.currentIndexChanged.connect(self.load_catalog)
        layout.addWidget(self.sort_combo)
        
        self.catalog_layout = QVBoxLayout()
        self.catalog_layout.setAlignment(Qt.AlignTop)
        
        container = QWidget()
        container.setLayout(self.catalog_layout)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)
        layout.addWidget(scroll)

    def setup_product_page(self):
        layout = QVBoxLayout(self.product_page)
        layout.addWidget(QLabel("Страница: Карточка товара"))

    def setup_orders_page(self):
        layout = QVBoxLayout(self.orders_page)
        layout.addWidget(QLabel("Страница: Заказы"))

    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)
        titles = ["Мир велосипедов — Каталог", "Мир велосипедов — Карточка товара", "Мир велосипедов — Заказы"]
        self.setWindowTitle(titles[index])
        
        if index == 0:
            self.back_button.setVisible(False)
        else:
            self.back_button.setVisible(True)
            
        if index == 0:
            self.refresh_catalog()

    def go_back(self):
        current_index = self.stacked_widget.currentIndex()
        if current_index > 0:
            self.switch_page(current_index - 1)

    def refresh_catalog(self):
        self.load_catalog()

    def load_catalog(self) -> None:
        while self.catalog_layout.count():
            item = self.catalog_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        search = self.search_input.text().strip()
        category = self.category_combo.currentText()
        sort_order = "ASC" if self.sort_combo.currentText() == "По возрастанию" else "DESC"
        
        products = fetch_catalog(search_query=search, category=category, sort_order=sort_order)
        
        for product in products:
            self.current_product_id = product["product_id"]
            card = ProductCard(product, self)
            self.catalog_layout.addWidget(card)


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