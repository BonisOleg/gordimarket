from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0033_remove_category_cat_active_parent_idx_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE EXTENSION IF NOT EXISTS pg_trgm;
                CREATE INDEX IF NOT EXISTS products_product_brand_gin_trgm_idx
                ON products_product
                USING gin (brand gin_trgm_ops);
            """,
            reverse_sql="DROP INDEX IF EXISTS products_product_brand_gin_trgm_idx;",
        ),
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS products_product_vendor_name_gin_trgm_idx
                ON products_product
                USING gin (vendor_name gin_trgm_ops);
            """,
            reverse_sql="DROP INDEX IF EXISTS products_product_vendor_name_gin_trgm_idx;",
        ),
    ]
