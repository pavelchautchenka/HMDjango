# Generated by Django 5.0 on 2023-12-27 22:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hwork', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='note',
            name='created_at',
            field=models.DateTimeField(),
        ),
    ]