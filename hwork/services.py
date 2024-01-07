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



