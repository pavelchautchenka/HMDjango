# Generated by Django 5.0 on 2024-01-07 11:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hwork', '0014_alter_user_managers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
    ]
