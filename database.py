import psycopg
from pathlib import Path

PROJECT_DIR = Path(__file__).parent

def initialise_database():
    pass

def fetch_catalog(search_query="", category="", sort_order="ASC"):
    try:
        conn = psycopg.connect("host=localhost port=5432 dbname=formadessert user=postgres password=123")
        cursor = conn.cursor()
        
        query = """
            SELECT product_id, name, 'Категория 1' as category, 'Подкатегория' as subcategory, 
                   'Производитель' as manufacturer, 'Состав' as composition, 
                   price as base_price, price as minimum_price, 10 as quantity, NULL as image_name
            FROM products 
            WHERE name ILIKE %s
        """
        params = [f"%{search_query}%"]
        
        if category and category != "Все категории":
            query += " AND 'Категория 1' = %s" 
            params.append(category)
            
        if sort_order == "ASC":
            query += " ORDER BY price ASC"
        else:
            query += " ORDER BY price DESC"
            
        query += " LIMIT 20;"
        
        cursor.execute(query, tuple(params))
        columns = [desc[0] for desc in cursor.description]
        products = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return products
    except Exception as e:
        print(f"Ошибка БД: {e}")
        return []

def fetch_product_by_id(product_id):
    try:
        conn = psycopg.connect("host=localhost port=5432 dbname=formadessert user=postgres password=123")
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS image_path VARCHAR(255);")
        conn.commit()
        cursor.execute("""
            SELECT product_id, name, price, 'Описание товара' as description, image_path, 10 as quantity 
            FROM products WHERE product_id = %s
        """, (product_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {'product_id': row[0], 'name': row[1], 'price': row[2], 'description': row[3], 'image_name': row[4], 'quantity': row[5]}
        return None
    except Exception as e:
        print(f"Ошибка БД: {e}")
        return None

def update_product_image(product_id, image_path):
    try:
        conn = psycopg.connect("host=localhost port=5432 dbname=formadessert user=postgres password=123")
        cursor = conn.cursor()
        cursor.execute("UPDATE products SET image_path = %s WHERE product_id = %s", (image_path, product_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Ошибка обновления БД: {e}")
        return False

def fetch_categories():
    return ["Все категории", "Категория 1", "Категория 2", "Категория 3"]

def authenticate(login):
    try:
        conn = psycopg.connect("host=localhost port=5432 dbname=formadessert user=postgres password=123")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, last_name, first_name, 'Отчество' as patronymic, 'Роль' as role FROM users WHERE login = %s", (login,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {'user_id': row[0], 'last_name': row[1], 'first_name': row[2], 'patronymic': row[3], 'role': row[4]}
        return None
    except Exception as e:
        print(f"Ошибка БД: {e}")
        return None

def save_order(user_id, cart_items):
    try:
        conn = psycopg.connect("host=localhost port=5432 dbname=formadessert user=postgres password=123")
        cursor = conn.cursor()
        
        cursor.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'Новый';")
        conn.commit()
        
        for item in cart_items:
            product_id = item['product_id']
            quantity = item['quantity']
            cursor.execute("SELECT COALESCE(SUM(quantity), 0) FROM stock_items WHERE product_id = %s", (product_id,))
            stock = cursor.fetchone()[0]
            if stock < quantity:
                conn.rollback()
                return False, f"Недостаточно товара (ID {product_id}) на складе"
        
        cursor.execute(
            "INSERT INTO orders (order_date, user_id, status) VALUES (CURRENT_DATE, %s, 'Новый') RETURNING order_id",
            (user_id,)
        )
        order_id = cursor.fetchone()[0]
        
        for item in cart_items:
            product_id = item['product_id']
            quantity = item['quantity']
            price = item['price']
            
            cursor.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)",
                (order_id, product_id, quantity, price)
            )
            cursor.execute(
                "UPDATE stock_items SET quantity = quantity - %s WHERE product_id = %s",
                (quantity, product_id)
            )
            if cursor.rowcount == 0:
                conn.rollback()
                return False, f"Нет остатков для товара (ID {product_id})"
            
        conn.commit()
        conn.close()
        return True, "Заказ оформлен"
    except Exception as e:
        print(f"Ошибка сохранения заказа: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False, str(e)

def delete_product(product_id):
    try:
        conn = psycopg.connect("host=localhost port=5432 dbname=formadessert user=postgres password=123")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE product_id = %s", (product_id,))
        conn.commit()
        conn.close()
        return True, "Товар удалён"
    except psycopg.errors.ForeignKeyViolation:
        if 'conn' in locals():
            conn.rollback()
        return False, "Товар нельзя удалить: он есть в заказах"
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        return False, str(e)