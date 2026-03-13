# Generated manually for PostgreSQL Full-Text Search optimization

from django.db import migrations, connection


def apply_postgres_indexes(apps, schema_editor):
    """Застосовуємо індекси тільки для PostgreSQL"""
    if connection.vendor != 'postgresql':
        return
    
    with connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS products_product_name_gin_trgm_idx 
            ON products_product 
            USING gin (name gin_trgm_ops);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS products_product_description_gin_trgm_idx 
            ON products_product 
            USING gin (description gin_trgm_ops);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS products_product_name_search_idx 
            ON products_product 
            USING gin (to_tsvector('english', COALESCE(name, '')));
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS products_product_description_search_idx 
            ON products_product 
            USING gin (to_tsvector('english', COALESCE(description, '')));
        """)


def reverse_postgres_indexes(apps, schema_editor):
    """Видаляємо індекси тільки для PostgreSQL"""
    if connection.vendor != 'postgresql':
        return
    
    with connection.cursor() as cursor:
        cursor.execute("DROP INDEX IF EXISTS products_product_name_gin_trgm_idx;")
        cursor.execute("DROP INDEX IF EXISTS products_product_description_gin_trgm_idx;")
        cursor.execute("DROP INDEX IF EXISTS products_product_name_search_idx;")
        cursor.execute("DROP INDEX IF EXISTS products_product_description_search_idx;")
        cursor.execute("DROP EXTENSION IF EXISTS pg_trgm;")


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0019_add_search_indexes'),
    ]

    operations = [
        migrations.RunPython(apply_postgres_indexes, reverse_postgres_indexes),
    ]

