"""
URL configuration for Lesson21_Django project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls.static import serve
from django.conf import settings
from hwork import views
from hwork.views import home_page_view, create_note_view, show_note_view, about_page_view, delete_note, update_note

urlpatterns = [
    path('admin/', admin.site.urls),  # Подключение панели администратора.
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/register', views.register, name='register'),


    path("", views.home_page_view, name="home"),  # Добавим главную страницу.
    path("filter", views.filter_notes_view, name="filter-notes"),
    path("create", views.create_note_view, name="create-note"),
    path("post/<note_uuid>", views.show_note_view, name="show-note"),


    path("user/<username>/notes", views.owner_notes_view, name="owner-notes-view"),


    path("about", views.about_page_view, name="about"),
    path("delete/<note_uuid>", views.delete_note, name="delete"),

    path("user/<username>/notes", views.user_notes_view, name="user_notes"),

    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT})


]
