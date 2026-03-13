from django.db import migrations, models, connection
import django.db.models.deletion


def create_models_if_not_exist(apps, schema_editor):
    """Створюємо моделі тільки якщо їх ще немає"""
    if connection.vendor != 'postgresql':
        return
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('products_brand', 'products_productreview')
        """)
        existing_tables = {row[0] for row in cursor.fetchall()}
        
        if 'products_brand' not in existing_tables:
            cursor.execute("""
                CREATE TABLE products_brand (
                    id BIGSERIAL PRIMARY KEY,
                    name VARCHAR(100) UNIQUE NOT NULL,
                    slug VARCHAR(100) UNIQUE NOT NULL,
                    logo VARCHAR(100),
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    sort_order INTEGER DEFAULT 0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
        
        if 'products_productreview' not in existing_tables:
            cursor.execute("""
                CREATE TABLE products_productreview (
                    id BIGSERIAL PRIMARY KEY,
                    author_name VARCHAR(100) DEFAULT 'Аноним',
                    rating SMALLINT DEFAULT 5,
                    text TEXT NOT NULL,
                    category_badge VARCHAR(50),
                    is_approved BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    product_id BIGINT REFERENCES products_product(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE INDEX products_pr_is_appr_b55fbf_idx 
                ON products_productreview(is_approved, created_at DESC)
            """)
            cursor.execute("""
                CREATE INDEX products_pr_product_160d92_idx 
                ON products_productreview(product_id, is_approved)
            """)


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('products', '0011_add_video_url'),
    ]

    operations = [
        migrations.RunPython(create_models_if_not_exist, reverse_func),
    ]

