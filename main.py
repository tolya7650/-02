"""PySide6 catalogue application."""
from __future__ import annotations

import sys
from pathlib import Path
import shutil
import uuid

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QWidget, QVBoxLayout, QPushButton, QHBoxLayout,
    QLabel, QScrollArea, QFrame, QMessageBox, QLineEdit, QComboBox, QDialog, QSpinBox, QFileDialog,
    QTableWidget, QTableWidgetItem
)

from database import (
    PROJECT_DIR, fetch_catalog, fetch_product_by_id, authenticate, fetch_categories, 
    update_product_image, save_order, delete_product
)

RESOURCES = PROJECT_DIR / "resources"
IMAGES = PROJECT_DIR / "images"
PLACEHOLDER = RESOURCES / "picture.png"
LOGO = RESOURCES / "Мир велосипедов.png"
ICON = RESOURCES / "Мир велосипедов.ico"


class ProductCardDialog(QDialog):
    def __init__(self, product_id, main_window, parent=None):
        super().__init__(parent)
        self.product_id = product_id
        self.main_window = main_window
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
            
            stock_qty = self.product["quantity"]
            
            self.image_label = QLabel()
            self.image_label.setFixedSize(200, 150)
            self.image_label.setAlignment(Qt.AlignCenter)
            self.update_image_display(self.product["image_name"])
            layout.addWidget(self.image_label)
            
            upload_button = QPushButton("Загрузить изображение")
            upload_button.clicked.connect(self.load_image)
            layout.addWidget(upload_button)
            
            layout.addWidget(QLabel("Размер:"))
            self.size_combo = QComboBox()
            self.size_combo.addItems(["S", "M", "L", "XL"])
            layout.addWidget(self.size_combo)
            
            layout.addWidget(QLabel("Количество:"))
            self.quantity_spin = QSpinBox()
            self.quantity_spin.setMinimum(1)
            self.quantity_spin.setMaximum(stock_qty)
            layout.addWidget(self.quantity_spin)
            
            add_button = QPushButton("Добавить в корзину")
            add_button.clicked.connect(self.add_to_cart)
            layout.addWidget(add_button)
            
            # --- НОВОЕ ДЛЯ ПАРЫ 23 ---
            delete_button = QPushButton("Удалить товар")
            delete_button.setStyleSheet("background-color: #d9534f; color: white;")
            delete_button.clicked.connect(self.delete_product)
            layout.addWidget(delete_button)
        else:
            layout.addWidget(QLabel("Товар не найден"))

    def update_image_display(self, image_path):
        pixmap = QPixmap(str(image_path)) if image_path else QPixmap()
        if pixmap.isNull():
            pixmap = QPixmap(str(PLACEHOLDER))
        if pixmap.isNull():
            self.image_label.setText("Нет фото")
        else:
            self.image_label.setPixmap(pixmap.scaled(200, 150, Qt.KeepAspectRatio))

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите изображение", "", "Images (*.png *.jpg *.jpeg)"
        )
        if not file_path:
            return
        if QPixmap(file_path).isNull():
            QMessageBox.warning(self, "Ошибка", "Файл не является изображением")
            return
        IMAGES.mkdir(exist_ok=True)
        target = IMAGES / (uuid.uuid4().hex + Path(file_path).suffix)
        try:
            shutil.copy2(file_path, target)
            if update_product_image(self.product_id, str(target)):
                self.update_image_display(str(target))
                self.product["image_name"] = str(target)
            else:
                raise Exception("Ошибка БД")
        except Exception as e:
            if target.exists():
                target.unlink()
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить изображение: {e}")

    def add_to_cart(self):
        name = self.product["name"]
        quantity = self.quantity_spin.value()
        price = float(self.product["price"])
        self.main_window.add_to_cart(name, quantity, price, self.product_id)
        self.accept()

    # --- НОВОЕ ДЛЯ ПАРЫ 23 ---
    def delete_product(self):
        reply = QMessageBox.question(
            self, "Удаление", "Вы уверены, что хотите удалить товар?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
            
        success, message = delete_product(self.product_id)
        if success:
            QMessageBox.information(self, "Успех", message)
            self.main_window.load_catalog()
            self.accept()
        else:
            QMessageBox.critical(self, "Ошибка", message)


class ProductCard(QFrame):
    def __init__(self, product, parent_window) -> None:
        super().__init__()
        self.parent_window = parent_window
        self.product_id = product["product_id"]
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

        self.mousePressEvent = lambda event: self.open_card()

    def open_card(self):
        dialog = ProductCardDialog(self.product_id, self.parent_window, self.parent_window)
        dialog.exec()


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
        
        self.stacked_widget = QStackedWidget()
        self.catalog_page = QWidget()
        self.cart_page = QWidget()
        self.orders_page = QWidget()
        
        self.setup_catalog_page()
        self.setup_cart_page()
        self.setup_orders_page()
        
        self.stacked_widget.addWidget(self.catalog_page)
        self.stacked_widget.addWidget(self.cart_page)
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
        
        self.btn_cart = QPushButton("Корзина")
        self.btn_cart.clicked.connect(lambda: self.switch_page(1))
        header.addWidget(self.btn_cart)
        
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

    def setup_cart_page(self):
        layout = QVBoxLayout(self.cart_page)
        
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(5)
        self.cart_table.setHorizontalHeaderLabels(["Наименование", "Количество", "Цена", "Сумма", "ID"])
        self.cart_table.setColumnHidden(4, True)
        layout.addWidget(self.cart_table)
        
        self.total_label = QLabel("Итого: 0 ₽")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(self.total_label)
        
        change_layout = QHBoxLayout()
        change_layout.addWidget(QLabel("Новое количество:"))
        self.change_quantity_spin = QSpinBox()
        self.change_quantity_spin.setMinimum(1)
        change_layout.addWidget(self.change_quantity_spin)
        
        change_btn = QPushButton("Изменить")
        change_btn.clicked.connect(self.change_quantity)
        change_layout.addWidget(change_btn)
        
        layout.addLayout(change_layout)
        
        remove_button = QPushButton("Удалить выбранное")
        remove_button.clicked.connect(self.remove_from_cart)
        layout.addWidget(remove_button)
        
        confirm_button = QPushButton("Оформить заказ")
        confirm_button.setStyleSheet("background-color: #2E8B57; color: white; font-weight: bold; padding: 10px;")
        confirm_button.clicked.connect(self.confirm_order)
        layout.addWidget(confirm_button)

    def setup_orders_page(self):
        layout = QVBoxLayout(self.orders_page)
        layout.addWidget(QLabel("Страница: Заказы"))

    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)
        titles = ["Мир велосипедов — Каталог", "Мир велосипедов — Корзина", "Мир велосипедов — Заказы"]
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
            card = ProductCard(product, self)
            self.catalog_layout.addWidget(card)

    def add_to_cart(self, name, quantity, price, product_id):
        row = self.cart_table.rowCount()
        self.cart_table.insertRow(row)
        self.cart_table.setItem(row, 0, QTableWidgetItem(name))
        self.cart_table.setItem(row, 1, QTableWidgetItem(str(quantity)))
        self.cart_table.setItem(row, 2, QTableWidgetItem(str(price)))
        self.cart_table.setItem(row, 3, QTableWidgetItem(str(quantity * price)))
        self.cart_table.setItem(row, 4, QTableWidgetItem(str(product_id)))
        self.update_total()

    def change_quantity(self):
        row = self.cart_table.currentRow()
        if row >= 0:
            new_quantity = self.change_quantity_spin.value()
            price = float(self.cart_table.item(row, 2).text())
            self.cart_table.setItem(row, 1, QTableWidgetItem(str(new_quantity)))
            self.cart_table.setItem(row, 3, QTableWidgetItem(str(new_quantity * price)))
            self.update_total()

    def remove_from_cart(self):
        row = self.cart_table.currentRow()
        if row >= 0:
            self.cart_table.removeRow(row)
            self.update_total()

    def update_total(self):
        total = 0
        for row in range(self.cart_table.rowCount()):
            total += float(self.cart_table.item(row, 3).text())
        self.total_label.setText(f"Итого: {total} ₽")
        if self.cart_table.rowCount() == 0:
            self.total_label.setText("Итого: 0 ₽")

    def confirm_order(self):
        if self.cart_table.rowCount() == 0:
            QMessageBox.warning(self, "Ошибка", "Корзина пуста")
            return
            
        cart_items = []
        for row in range(self.cart_table.rowCount()):
            product_id = int(self.cart_table.item(row, 4).text())
            quantity = int(self.cart_table.item(row, 1).text())
            price = float(self.cart_table.item(row, 2).text())
            cart_items.append({'product_id': product_id, 'quantity': quantity, 'price': price})
            
        success, message = save_order(self.user_id, cart_items)
        if success:
            QMessageBox.information(self, "Успех", message)
            self.cart_table.setRowCount(0)
            self.update_total()
        else:
            QMessageBox.critical(self, "Ошибка", message)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("PP02")
    app.setStyleSheet(
        """
        QWidget { font-family: Calibri; font-size: 14px; color: #000000; background: #FFFFFF; }
        QPushButton { background: #70B2AF; padding: 7px 12px; border: 0; border-radius: 4px; }
        QPushButton:hover { background: #D2F6E7; }
        #title, #productName { font-weight: bold; font-size: 18px; }
        #productCard { border: 1px solid #70B2AF; border-radius: 6px; margin: 4px; padding: 4px; }
        #price { font-weight: bold; font-size: 16px; }
        QLineEdit, QComboBox, QSpinBox { padding: 6px; border: 1px solid #70B2AF; border-radius: 3px; }
        """
    )
    
    from login_window import LoginWindow
    login_win = LoginWindow()
    
    if login_win.exec():
        return app.exec()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())