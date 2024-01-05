from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.urls import reverse
from django.http import HttpResponseRedirect, Http404, HttpRequest
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q
from django.contrib.auth import authenticate, login
from .models import Note, User
import os
from django.db.models import F
from django.contrib.postgres.aggregates import ArrayAgg
from django.contrib.auth.decorators import login_required


def filter_notes_view(request: WSGIRequest):
    """
    Фильтруем записи по запросу пользователя.
    HTTP метод - GET.
    Обрабатывает URL вида: /filter/?search=<text>
    """

    search: str = request.GET.get("search", "")  # `get` - получение по ключу. Если такого нет, то - "",

    # Если строка поиска не пустая, то фильтруем записи по ней.
    if search:
        # ❗️Нет обращения к базе❗️
        # Через запятую запросы формируются c ❗️AND❗️
        # notes_queryset = Note.objects.filter(title__icontains=search, content__icontains=search)
        # SELECT "posts_note"."uuid", "posts_note"."title", "posts_note"."content", "posts_note"."created_at"
        # FROM "posts_note" WHERE (
        # "posts_note"."title" LIKE %search% ESCAPE '\' AND "posts_note"."content" LIKE %search% ESCAPE '\')

        # ❗️Все импорты сверху файла❗️
        # from django.db.models import Q

        notes_queryset = Note.objects.filter(title__icontains=search, content__icontains=search)
        # Аналогия
        notes_queryset = Note.objects.filter(Q(title__icontains=search), Q(content__icontains=search))

        # Оператор - `|` Означает `ИЛИ`.
        # Оператор - `&` Означает `И`.
        notes_queryset = Note.objects.filter(Q(title__icontains=search) | Q(content__icontains=search))

    else:
        # Если нет строки поиска.
        notes_queryset = Note.objects.all()  # Получение всех записей из модели.

    notes_queryset = notes_queryset.order_by("-created_at")  # ❗️Нет обращения к базе❗️

    # SELECT "posts_note"."uuid", "posts_note"."title", "posts_note"."content", "posts_note"."created_at"
    # FROM "posts_note" WHERE
    # ("posts_note"."title" LIKE %python% ESCAPE '\' OR "posts_note"."content" LIKE %python% ESCAPE '\')
    # ORDER BY "posts_note"."created_at" DESC

    print(notes_queryset.query)

    context: dict = {
        "notes": notes_queryset,
        "search_value_form": search,
    }
    return render(request, "home.html", context)


def about_page_view(request: WSGIRequest):
    return render(request, "about.html")


# все заметки любого другого пользователя
def owner_notes_view(request: WSGIRequest, username):
    user = User.objects.get(username=username)
    queryset = (Note.objects.filter(user=user)
                .select_related('user')
                .annotate(username=F('user__username'))
                .values("uuid", "title", "created_at", 'mod_time', "username"))

    return render(request, 'notes/owner_notes.html', {"notes": queryset})


# Заметки пользователя в логине
@login_required()
def user_notes_view(request: WSGIRequest, username):
        user = User.objects.get(username=username)
        queryset = (Note.objects.filter(user=user)
                    .select_related('user')
                    .annotate(username=F('user__username'))
                    .values("uuid", "title", "created_at", 'mod_time', "username"))

        return render(request, 'notes/owner_notes.html', {"notes": queryset})


# все заметки любого другого пользователя
# def owner_notes_view(request: WSGIRequest, username):
#     user = User.objects.get(username=username)
#
#     queryset = (Note.objects.filter(user=user)
#                     .select_related('user')
#                     .values("uuid", "title", "created_at", 'mod_time', "user__username"))
#
#     return render(request, 'notes/owner_notes.html', {"notes": queryset})
#
#
# Заметки пользователя в логине
# def user_notes_view(request: WSGIRequest, username):
#     if request.user.is_authenticated:
#         user = User.objects.get(username=username)
#         queryset = (Note.objects
#                     .filter(user=user)  # Получение всех объектов из таблицы Note
#                     .select_related("user")  # Вытягивание связанных данных из таблицы User в один запрос
#                     .prefetch_related("tags")  # Вытягивание связанных данных из таблицы Tag в отдельные запросы
#                     .annotate(
#             # Создание нового вычисляемого поля username из связанной таблицы User
#             username=F('user__username'),
#
#             # Создание массива уникальных имен тегов для каждой заметки
#             tag_names=ArrayAgg('tags__name', distinct=True)
#         )
#                     .values("uuid", "title", "created_at", "mod_time", "username",
#                             "tag_names")  # Выбор только указанных полей для результата
#                     .filter(user=user)
#                     .distinct()  # Убирание дубликатов, если они есть
#                     .order_by("-created_at")  # Сортировка результатов по убыванию по полю created_at
#                     )
#         print(queryset.query)
#         print(queryset)
#         return render(request, 'notes/owner_notes.html', {"notes": queryset[:3]})
#
#     else:
#         return render(request, "registration/login.html")

# def user_notes_view(request: WSGIRequest, username):
#     if request.user.is_authenticated:
#         user = User.objects.get(username=username)
#         user_notes = Note.objects.filter(user=user)
#         return render(request, 'notes/owner_notes.html', {"notes": user_notes})
#     else:
#         return render(request, "registration/login.html")
