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
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from django.contrib.auth import views as auth_views

from hwork import views
from hwork import services
from hwork.views import confirm_register_view

urlpatterns = [
    path('admin/', admin.site.urls),  # Подключение панели администратора.
    path('accounts/', include('django.contrib.auth.urls')),
    #Register
    path('accounts/register', views.register, name='register'),
    path("register/confirm/<uidb64>/<token>", confirm_register_view, name="register-confirm"),
    #Reset_New_Password
    path("register/pasword-resetform", views.reset_form_view, name='resetform'),
    path("password-reset/", views.reset_password_view, name="reset-password"),
    path("password-reset/new-password<uidb64>/<token>", views.confirm_new_password_view, name="new-password"),
    # Home
    path("", views.home_page_view, name="home"),  # Добавим главную страницу.
    path("filter", views.filter_notes_view, name="filter-notes"),
    #Create/Delete/Update Note
    path("create", views.create_note_view, name="create-note"),
    path("post/<note_uuid>", views.show_note_view, name="show-note"),
    path("user/<username>/notes", views.owner_notes_view, name="owner-notes-view"),
    path("delete/<note_uuid>", views.delete_note, name="delete"),
    path("update/<note_uuid>", views.update_note, name="update-note"),
    #My Profile
    path("profile/<username>", views.profile_page_view, name="profile-view"),
    #About Site
    path("about", views.about_page_view, name="about"),
    #Messages history
    path('history/', views.history, name="history"),
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    path("__debug__/", include("debug_toolbar.urls")),
    path('ckeditor/', include('ckeditor_uploader.urls')),

    # path('password_reset/', views.password_reset_request, name='password_reset_request'),
    # path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    # path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    # path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    # path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    path('api/', include('hwork.api.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token-obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    path("register/confirm/<uidb64>/<token>", confirm_register_view, name="register-confirm"),

    path("__debug__/", include("debug_toolbar.urls")),
    path('ckeditor/', include('ckeditor_uploader.urls')),

]
