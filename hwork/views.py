from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseRedirect, Http404, HttpRequest, HttpResponse
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q

from django.contrib.auth import authenticate, login
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from .mail import ConfirmUserRegisterEmailSender
from .models import Note, User, Tag
from .services import ret_queryset, create_note, update_user
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from .forms import PasswordResetRequestForm

from django.template.loader import render_to_string
from django.shortcuts import render, redirect
from django.contrib.sites.shortcuts import get_current_site


@permission_classes([AllowAny])
def home_page_view(request: WSGIRequest):

    queryset = ret_queryset()
    queryset = queryset.filter(active=True)
    return render(request, 'home.html', {'notes': queryset[:100]},)


@permission_classes([IsAuthenticated])
def owner_notes_view(request: WSGIRequest, username):
    queryset = ret_queryset()
    queryset = queryset.filter(username=username)

    return render(request, 'notes/owner_notes.html', {"notes": queryset})


@permission_classes([IsAuthenticated])
def profile_page_view(request: WSGIRequest, username):
    if request.method == 'POST':
        user = User.objects.get(username=username)
        update_user(request, user)
        return HttpResponseRedirect(reverse("home",))
    user = User.objects.get(username=username)
    tags_queryset = Tag.objects.filter(notes__user=user).distinct()

    return render(request, 'profile.html',{'tags': tags_queryset} )


@permission_classes([IsAuthenticated])
def update_note(request: WSGIRequest, note_uuid):
    if request.method == "POST":
        note = Note.objects.get(uuid=note_uuid)
        note = update_note(request, note)
        return HttpResponseRedirect(reverse('show-note', args=[note.uuid]))
    note = Note.objects.get(uuid=note_uuid)
    return render(request, "notes/update_form.html", {"note": note})



def create_note_view(request: WSGIRequest):
    if request.method == "POST":
        note = create_note(request)
        return HttpResponseRedirect(reverse('show-note', args=[note.uuid]))

    # Вернется только, если метод не POST.
    return render(request, "notes/create_form.html")


@permission_classes([IsAuthenticatedOrReadOnly])
def show_note_view(request: WSGIRequest, note_uuid):

    note = get_object_or_404(Note, uuid=note_uuid)
    viewed_notes = request.session.get('viewed_notes', [])
    if note_uuid not in viewed_notes:
        viewed_notes.insert(0, note_uuid)
    if len(viewed_notes) > 20:
        viewed_notes = viewed_notes[:20]
    request.session['viewed_notes'] = viewed_notes
    return render(request, "notes/note.html", {"note": note})


def history(request: WSGIRequest):
    viewed_notes = request.session.get('viewed_notes', [])
    notes = Note.objects.filter(uuid__in=viewed_notes)
    return render(request, 'notes/viewed_notes.html', {'notes': notes})


@permission_classes([IsAuthenticated])
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
    user = User.objects.create_user(
        username=request.POST["username"],
        email=request.POST["email"],
        password=request.POST["password1"],
        first_name=request.POST["first_name"],
        last_name=request.POST["last_name"],
        phone=request.POST["phone"]
    )

    ConfirmUserRegisterEmailSender(request, user).send_mail()
    # При регистрации редирект на главную страницу под логинам
    user = authenticate(username=request.POST["username"], password=request.POST["password1"])
    if user is not None:
        login(request, user)

    return HttpResponseRedirect(reverse('home'))


def confirm_register_view(request: WSGIRequest, uidb64: str, token: str):
    username = force_str(urlsafe_base64_decode(uidb64))

    user = get_object_or_404(User, username=username)
    if default_token_generator.check_token(user, token):
        user.is_active = True
        user.save(update_fields=["is_active"])
        return HttpResponseRedirect(reverse("login"))

    return render(request, "registration/invalid_email_confirm.html", {"username": user.username})


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






