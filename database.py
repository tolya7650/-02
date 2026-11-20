import psycopg
from pathlib import Path

PROJECT_DIR = Path(__file__).parent

def initialise_database():
    pass

def fetch_catalog(search_query=""):
    try:
        conn = psycopg.connect("host=localhost port=5432 dbname=formadessert user=postgres password=123")
        cursor = conn.cursor()
        
        if search_query:
            # Если есть поисковый запрос, ищем по названию и описанию (ILIKE)
            cursor.execute("""
                SELECT product_id, name, 'Категория' as category, 'Подкатегория' as subcategory, 
                       'Производитель' as manufacturer, 'Состав' as composition, 
                       price as base_price, price as minimum_price, 10 as quantity, NULL as image_name
                FROM products 
                WHERE name ILIKE %s OR 'Состав' ILIKE %s
                LIMIT 20;
            """, (f"%{search_query}%", f"%{search_query}%"))
        else:
            # Если пусто, показываем все товары
            cursor.execute("""
                SELECT product_id, name, 'Категория' as category, 'Подкатегория' as subcategory, 
                       'Производитель' as manufacturer, 'Состав' as composition, 
                       price as base_price, price as minimum_price, 10 as quantity, NULL as image_name
                FROM products LIMIT 20;
            """)
            
        columns = [desc[0] for desc in cursor.description]
        products = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return products
    except Exception as e:
        print(f"Ошибка БД: {e}")
        return []

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