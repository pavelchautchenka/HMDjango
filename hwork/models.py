import pathlib
import uuid

from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth import get_user_model


class User(AbstractUser):
    """
    Наследуем все поля из `AbstractUser`
    И добавляем новое поле `phone`
    """
    phone = models.CharField(max_length=11, null=True, blank=True)

    class Meta:
        db_table = "users"


def upload_to(instance: "Note", filename: str):
    return f"{instance.uuid}/{filename}"


class Note(models.Model):
    # Стандартный ID для каждой таблицы можно не указывать, Django по умолчанию это добавит.

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    mod_time = models.DateTimeField(null=True, blank=True)
    image = models.ImageField(upload_to=upload_to, null=True)
    # auto_now_add=True автоматически добавляет текущую дату и время.

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE,null=True, blank=True)
    # `on_delete=models.CASCADE`
    # При удалении пользователя, удалятся все его записи.

    # Менеджер объектов (Это и так будет по умолчанию добавлено).
    # Но мы указываем явно, чтобы понимать, откуда это берется.
    objects = models.Manager()       # Он подключается к базе

    class Meta:
        ordering = ["-created_at"]


@receiver(post_delete, sender=Note)
def after_delete_note(sender, instance: Note, **kwargs):
    if instance.image:
        note_media_folder: pathlib.Path = (settings.MEDIA_ROOT / str(instance.uuid))

        for file in note_media_folder.glob("*"):
            file.unlink(missing_ok=True)
        note_media_folder.unlink(missing_ok=True)
