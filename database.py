import psycopg
from pathlib import Path

PROJECT_DIR = Path(__file__).parent

def initialise_database():
    pass

def fetch_catalog(search_query="", category=""):
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
            
        query += " LIMIT 20;"
        
        cursor.execute(query, tuple(params))
        columns = [desc[0] for desc in cursor.description]
        products = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return products
    except Exception as e:
        print(f"Ошибка БД: {e}")
        return []

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