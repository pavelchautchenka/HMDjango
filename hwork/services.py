from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.urls import reverse
from django.http import HttpResponseRedirect, Http404, HttpRequest
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q
from django.contrib.auth import authenticate, login
from .models import Note, User, Tag
import os
from django.db.models import F
from django.contrib.postgres.aggregates import ArrayAgg
from django.contrib.auth.decorators import login_required


def ret_queryset():
    return (Note.objects.all()  # Получение всех объектов из таблицы Note
            .select_related("user")  # Вытягивание связанных данных из таблицы User в один запрос
            .prefetch_related("tags")  # Вытягивание связанных данных из таблицы Tag в отдельные запросы
            .annotate(
        # Создание нового вычисляемого поля username из связанной таблицы User
        username=F('user__username'),

        # Создание массива уникальных имен тегов для каждой заметки
        tag_names=ArrayAgg('tags__name', distinct=True)
    )
            .values("uuid", "title", "created_at", "mod_time", "username",
                    "tag_names", "active")  # Выбор только указанных полей для результата
            .distinct()  # Убирание дубликатов, если они есть
            .order_by("-created_at")  # Сортировка результатов по убыванию по полю created_at
            )


def create_note(request):
    images: list | None = request.FILES.getlist("noteImage")
    user = request.user if not request.user.is_anonymous else None
    note = Note.objects.create(
        title=request.POST["title"],
        content=request.POST["content"],
        user=user,
        image=images[0] if images else None,
    )
    # Если нет тегов, то будет пустой список
    tags_names: list[str] = request.POST.get("tags", "").split(",")
    tags_names = list(map(str.strip, tags_names)) # Убираем лишние пробелы

    tags_objects: list[Tag] = []
    for tag in tags_names:
        tag_obj, created = Tag.objects.get_or_create(name=tag)
        tags_objects.append(tag_obj)
    note.tags.set(tags_objects)
    return note


def update_user(request, username):
    user = User.objects.get(username=username)
    user.first_name = request.POST.get("first_name", user.first_name)
    user.last_name = request.POST.get("last_name", user.last_name)
    user.phone = request.POST.get("phone", user.phone)
    user.save()
    return user


def update_note(request, note):
    new_image = request.FILES.get("image")
    if new_image:
        # Удаление старого изображения
        if note.image:
            old_image_path = os.path.join(settings.MEDIA_ROOT, note.image.name)
            if os.path.isfile(old_image_path):
                os.remove(old_image_path)

        note.image = new_image
    note.title = request.POST.get('title', note.title)
    note.content = request.POST.get('content', note.content)
    note.mod_time = timezone.now()
    note.save()
    return note


#def register_note(request):
