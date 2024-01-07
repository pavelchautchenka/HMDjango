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


def home_page_view(request: WSGIRequest):
    # # Обязательно! каждая функция view должна принимать первым параметром request.
    # all_notes = Note.objects.all()[:510] # Получение всех записей из таблицы этой модели.
    # context: dict = {
    #     "notes": all_notes
    # }
    # print(request.user)
    # return render(request, "home.html", context)

    queryset = (
        Note.objects.all()  # Получение всех объектов из таблицы Note
        .select_related("user")  # Вытягивание связанных данных из таблицы User в один запрос
        .prefetch_related("tags")  # Вытягивание связанных данных из таблицы Tag в отдельные запросы
        .annotate(
            # Создание нового вычисляемого поля username из связанной таблицы User
            username=F('user__username'),

            # Создание массива уникальных имен тегов для каждой заметки
            tag_names=ArrayAgg('tags__name', distinct=True)
        )
        .values("uuid", "title", "created_at", "mod_time", "username",
                "tag_names")  # Выбор только указанных полей для результата
        .distinct()  # Убирание дубликатов, если они есть
        .order_by("-created_at")  # Сортировка результатов по убыванию по полю created_at
    )
    print(queryset.query)

    return render(request, 'home.html', {'notes': queryset[:100]})


def profile_page_view(request: WSGIRequest, username):
    if request.method == 'POST':
        user = User.objects.get(username=username)
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name = request.POST.get("last_name", user.last_name)
        user.phone = request.POST.get("phone", user.phone)
        user.save()
        return HttpResponseRedirect(reverse("home",))
    user = User.objects.get(username=username)
    tags_queryset = Tag.objects.filter(notes__user=user).distinct()

    return render(request, 'profile.html',{'tags': tags_queryset} )


def update_note(request: WSGIRequest, note_uuid):
    if request.method == "POST":
        note = Note.objects.get(uuid=note_uuid)
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
        return HttpResponseRedirect(reverse('show-note', args=[note.uuid]))
    note = Note.objects.get(uuid=note_uuid)
    return render(request, "notes/update_form.html", {"note": note})


def create_note_view(request: WSGIRequest):
    if request.method == "POST":
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
        tags_names = list(map(str.strip, tags_names))  # Убираем лишние пробелы

        tags_objects: list[Tag] = []
        for tag in tags_names:
            tag_obj, created = Tag.objects.get_or_create(name=tag)
            tags_objects.append(tag_obj)

        note.tags.set(tags_objects)
        return HttpResponseRedirect(reverse('show-note', args=[note.uuid]))

    # Вернется только, если метод не POST.
    return render(request, "notes/create_form.html")


def show_note_view(request: WSGIRequest, note_uuid):
    try:
        note = Note.objects.get(uuid=note_uuid)  # Получение только ОДНОЙ записи.

    except Note.DoesNotExist:
        # Если не найдено такой записи.
        raise Http404

    return render(request, "notes/note.html", {"note": note})


def delete_note(request: WSGIRequest, note_uuid):
    try:
        note = Note.objects.get(uuid=note_uuid)
        note.delete()
    except Note.DoesNotExist:
        # Если не найдено такой записи.
        raise Http404
    return render(request, "notes/confirm.html", {"note": note})


def register(request: WSGIRequest):
    if request.method != "POST":
        return render(request, "registration/register.html")
    print(request.POST)
    if not request.POST.get("username") or not request.POST.get("email") or not request.POST.get("password1"):
        return render(
            request,
            "registration/register.html",
            {"errors": "Укажите все поля!"}
        )
    print(User.objects.filter(
        Q(username=request.POST["username"]) | Q(email=request.POST["email"])
    ))
    # Если уже есть такой пользователь с username или email.
    if User.objects.filter(
            Q(username=request.POST["username"]) | Q(email=request.POST["email"])
    ).count() > 0:
        return render(
            request,
            "registration/register.html",
            {"errors": "Если уже есть такой пользователь с username или email"}
        )

    # Сравниваем два пароля!
    if request.POST.get("password1") != request.POST.get("password2"):
        return render(
            request,
            "registration/register.html",
            {"errors": "Пароли не совпадают"}
        )

    # Создадим учетную запись пользователя.
    # Пароль надо хранить в БД в шифрованном виде.
    User.objects.create_user(
        username=request.POST["username"],
        email=request.POST["email"],
        password=request.POST["password1"],
        first_name=request.POST["first_name"],
        last_name=request.POST["last_name"],
        phone=request.POST["phone"]
    )

    # При регистрации редирект на главную страницу под логинам
    user = authenticate(username=request.POST["username"], password=request.POST["password1"])
    if user is not None:
        login(request, user)

    return HttpResponseRedirect(reverse('home'))

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
    queryset = (Note.objects
                .filter(user=user)  # Получение всех объектов из таблицы Note
                .select_related("user")  # Вытягивание связанных данных из таблицы User в один запрос
                .prefetch_related("tags")  # Вытягивание связанных данных из таблицы Tag в отдельные запросы
                .annotate(
        # Создание нового вычисляемого поля username из связанной таблицы User
        username=F('user__username'),

        # Создание массива уникальных имен тегов для каждой заметки
        tag_names=ArrayAgg('tags__name', distinct=True)
    )
                .values("uuid", "title", "created_at", "mod_time", "username",
                        "tag_names")  # Выбор только указанных полей для результата
                .filter(user=user)
                .distinct()  # Убирание дубликатов, если они есть
                .order_by("-created_at")  # Сортировка результатов по убыванию по полю created_at
                )

    return render(request, 'notes/owner_notes.html', {"notes": queryset})