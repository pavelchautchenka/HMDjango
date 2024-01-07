from django.contrib import admin
from django.db.models import QuerySet, F
from django.db.models.functions import Upper
from .models import Note, User, Tag
from django.utils.safestring import mark_safe
from django.db.models import Count

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ["active", "preview_image",'title', 'short_content', 'created_at', 'mod_time',"tags_function",'user']
    search_fields = ['title', 'content']
    date_hierarchy = "created_at"
    # Действия
    actions = ["title_up", "confirm_note"]
    # Поля, которые не имеют большого кол-ва уникальных вариантов!
    #list_filter = ["user__username", "user__email", "tags__name"]
    #filter_horizontal = ["tags"]
    #list_editable = можно редактировать прямо из предпросмотра
    readonly_fields = ["preview_image"]
    fieldsets = (
        # 1
        (None, {"fields": ("title", "user", "preview_image", "image", "tags")}),
        ("content", {"fields": ("content",)})
    )


    # def get_queryset(self, request):
    #     return (
    #         Note.objects.all()
    #         .select_related("user")  # Вытягивание связанных данных из таблицы User в один запрос
    #         .prefetch_related("tags")  # Вытягивание связанных данных из таблицы Tag в отдельные запросы
    #     )


    @admin.action(description='Confirm')
    def confirm_note(self, request, queryset):
        queryset.update(active=True)


    @admin.action(description="Upper Title")
    def title_up(self, form, queryset: QuerySet[Note]):
        queryset.update(title=Upper(F("title")))

    @admin.display()
    def short_content(self, obj: Note) -> str:
        return obj.content[:50] + "..."

    @admin.display(description="IMG")
    def preview_image(self, obj: Note) -> str:
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" height="64" />')
        return "X"

    @admin.display()
    def tags_function(self, obj: Note) -> str:
        tags = list(obj.tags.all())
        text = ""
        for tag in tags:
            text += f"<span style=\"color: blue;\">{tag}</span><br>"
        return mark_safe(text)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["is_active", 'username', 'first_name', 'last_name', 'note_count']
    search_fields = ['username', 'first_name']
    actions = ["block_user",]
    @admin.action(description='Block User')

    def block_user(self, request, queryset):
        queryset.update(is_active=True)

    fieldsets = (
        # 1  tuple(None, dict)
        (None, {"fields": ("username", "password")}),

        # 2  tuple(str, dict)
        ("Персональная информация", {"fields": ("first_name", "last_name", "email", "phone")}),

        # 3  tuple(str, dict)
        (
            "Права пользователя",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),

        # 4  tuple(str, dict)
        ("Важные даты", {"fields": ("last_login", "date_joined")}),
    )

    # def get_queryset(self, request):      #TODO: Так быстрее
    #     return super().get_queryset(request).annotate(count=Count("note"))
    #
    # @admin.display(description='Number of Notes')
    # def note_count(self, obj):
    #     return obj.count


    @admin.display(description='Number of notes')    #TODO: Так медленно
    def note_count(self, obj):
        return obj.note_set.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name"]