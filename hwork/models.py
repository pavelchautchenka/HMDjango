import pathlib
import uuid

from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth import get_user_model
from ckeditor.fields import RichTextField


class User(AbstractUser):
    """
    Наследуем все поля из `AbstractUser`
    И добавляем новое поле `phone`
    """
    is_active = models.BooleanField(default=True)
    phone = models.CharField(max_length=11, null=True, blank=True)
    #objects = models.Manager()

    class Meta:
        db_table = "users"
        #verbose_name = "USERS Test"
        # ordering = ['-created_at']  # Дефис это означает DESC сортировку (обратную).
        # indexes = [
        #     models.Index(fields=("created_at",), name="created_at_index"),
        # ]


def upload_to(instance: "Note", filename: str):
    return f"{instance.uuid}/{filename}"


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Note(models.Model):
    # Стандартный ID для каждой таблицы можно не указывать, Django по умолчанию это добавит.

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    active = models.BooleanField(default=True)
    title = models.CharField(max_length=255, help_text='max 255 symbols') #verbose_name = "заголовок" для панели администратора
    content = RichTextField()
    created_at = models.DateTimeField(auto_now_add=True)        #db_index=True
    mod_time = models.DateTimeField(null=True, blank=True, db_index=True)
    image = models.ImageField(upload_to=upload_to, null=True,blank=True)
    # auto_now_add=True автоматически добавляет текущую дату и время.

    tags = models.ManyToManyField(Tag, related_name="notes", verbose_name="Теги")
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, null=True, blank=True)
    # `on_delete=models.CASCADE`
    # При удалении пользователя, удалятся все его записи.

    # Менеджер объектов (Это и так будет по умолчанию добавлено).
    # Но мы указываем явно, чтобы понимать, откуда это берется.
    objects = models.Manager()       # Он подключается к базе

    class Meta:
        ordering = ["mod_time"]
        indexes = [models.Index(fields=("created_at",), name="created_at_index"),
                   models.Index(fields=("mod_time",), name="mod_time_index"),
        ]

    def __str__(self):
        return f"Заметка: \"{self.title}\""


@receiver(post_delete, sender=Note)
def after_delete_note(sender, instance: Note, **kwargs):
    if instance.image:
        note_media_folder: pathlib.Path = (settings.MEDIA_ROOT / str(instance.uuid))

        for file in note_media_folder.glob("*"):
            file.unlink(missing_ok=True)
        note_media_folder.rmdir()

