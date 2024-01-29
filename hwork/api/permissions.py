
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Любой пользователь может просматривать объект
        if request.method in SAFE_METHODS:
            return True
        # Только владелец объекта и суперпользователь могут изменять объект
        return obj.user == request.user or request.user.is_superuser
