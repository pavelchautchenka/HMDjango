# Generated by Django 5.0 on 2024-01-06 23:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hwork', '0011_alter_note_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='note',
            name='active',
            field=models.BooleanField(default=False),
        ),
    ]
