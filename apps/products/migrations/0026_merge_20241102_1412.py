# Merge migration to resolve conflicts between parallel branches

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0021_improve_search_indexes'),
        ('products', '0025_alter_product_index'),
    ]

    operations = [
        # No operations needed - this is just a merge migration
    ]

