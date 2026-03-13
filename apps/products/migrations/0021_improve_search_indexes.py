# Generated manually for improved PostgreSQL search indexes
# Оптимізація пошуку для української мови з використанням триграм

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0020_add_postgres_search_indexes'),
    ]

    operations = [
        # Видаляємо старі Full-Text Search індекси з 'english' словником
        # Вони не підходять для української мови
        migrations.RunSQL(
            sql="DROP INDEX IF EXISTS products_product_name_search_idx;",
            reverse_sql="""
                CREATE INDEX IF NOT EXISTS products_product_name_search_idx 
                ON products_product 
                USING gin (to_tsvector('english', COALESCE(name, '')));
            """,
        ),
        
        migrations.RunSQL(
            sql="DROP INDEX IF EXISTS products_product_description_search_idx;",
            reverse_sql="""
                CREATE INDEX IF NOT EXISTS products_product_description_search_idx 
                ON products_product 
                USING gin (to_tsvector('english', COALESCE(description, '')));
            """,
        ),
        
        # Тригами (pg_trgm) індекси вже створені в попередній міграції
        # Вони працюють добре з будь-якою мовою
        # Залишаємо їх як є: products_product_name_gin_trgm_idx
        # та products_product_description_gin_trgm_idx
        
        # Додаємо додаткові BTree індекси для прискорення сортування
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS products_product_name_lower_idx 
                ON products_product (LOWER(name));
            """,
            reverse_sql="DROP INDEX IF EXISTS products_product_name_lower_idx;",
        ),
        
        # Індекс для сортування за створенням (для пошуку)
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS products_product_active_created_idx 
                ON products_product (is_active, created_at DESC) 
                WHERE is_active = true;
            """,
            reverse_sql="DROP INDEX IF EXISTS products_product_active_created_idx;",
        ),
        
        # Індекс для акційних товарів
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS products_product_sale_active_idx 
                ON products_product (is_sale, sale_price) 
                WHERE is_active = true AND is_sale = true;
            """,
            reverse_sql="DROP INDEX IF EXISTS products_product_sale_active_idx;",
        ),
        
        # Композитний індекс для пошуку з фільтрацією
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS products_product_active_category_idx 
                ON products_product (is_active, primary_category_id, sort_order) 
                WHERE is_active = true;
            """,
            reverse_sql="DROP INDEX IF EXISTS products_product_active_category_idx;",
        ),
    ]

