# Generated by Django 5.0 on 2024-01-05 01:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hwork', '0004_note_created_at_index'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='note',
            name='tags',
            field=models.ManyToManyField(related_name='notes', to='hwork.tag', verbose_name='Теги'),
        ),
    ]
