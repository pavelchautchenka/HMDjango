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


def home_page_view(request: WSGIRequest):
    # Обязательно! каждая функция view должна принимать первым параметром request.
    all_notes = Note.objects.all()  # Получение всех записей из таблицы этой модели.
    context: dict = {
        "notes": all_notes
    }
    print(request.user)
    return render(request, "home.html", context)


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


    user_notes = Note.objects.filter(user=user)

    return render(request, 'owner_notes.html', {"notes": user_notes})


#Заметки пользователя в логине
def user_notes_view(request: WSGIRequest, username):
    if request.user.is_authenticated:
        user = User.objects.get(username=username)
        user_notes = Note.objects.filter(user=user)
        return render(request,'all notes.html', {"notes": user_notes})
    else:
        return render(request, "registration/login.html" )


def create_note_view(request: WSGIRequest):
    print(request.user)

    # if not request.user.is_authenticated:
    # return render(request, "registration/login.html", {"errors": "Необходимо войти"})

    if request.user.is_anonymous and request.method == "POST":
        images: list | None = request.FILES.getlist("noteImage")
        note = Note.objects.create(
            title=request.POST["title"],
            content=request.POST["content"],
            user=None,
            image=images[0] if images else None,
        )
        return HttpResponseRedirect(reverse('show-note', args=[note.uuid]))

    if request.method == "POST":
        images: list | None = request.FILES.getlist("noteImage")
        note = Note.objects.create(
            title=request.POST["title"],
            content=request.POST["content"],
            user=request.user,
            image=images[0] if images else None,
        )
        return HttpResponseRedirect(reverse('show-note', args=[note.uuid]))

    # Вернется только, если метод не POST.
    return render(request, "create_form.html")


def show_note_view(request: WSGIRequest, note_uuid):
    try:
        note = Note.objects.get(uuid=note_uuid)  # Получение только ОДНОЙ записи.

    except Note.DoesNotExist:
        # Если не найдено такой записи.
        raise Http404

    return render(request, "note.html", {"note": note})


def delete_note(request: WSGIRequest, note_uuid):
    try:

        note = Note.objects.get(uuid=note_uuid)

        note.delete()

    except Note.DoesNotExist:
        # Если не найдено такой записи.
        raise Http404

    return render(request, "confirm.html", {"note": note})


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
    return render(request, "update_form.html", {"note": note})


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
        password=request.POST["password1"]
    )

    # При регистрации редирект на главную страницу под логинам
    user = authenticate(username=request.POST["username"], password=request.POST["password1"])
    if user is not None:
        login(request, user)

    return HttpResponseRedirect(reverse('home'))
