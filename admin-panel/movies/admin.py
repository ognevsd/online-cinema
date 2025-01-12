from django.contrib import admin
from .models import Genre, Filmwork, GenreFilmwork, Person, PersonFilmwork


class GenreFilmworkInline(admin.TabularInline):
    model = GenreFilmwork
    autocomplete_fields = ("genre",)


class PersonFilmworkInline(admin.TabularInline):
    model = PersonFilmwork
    autocomplete_fields = ("person",)


# Register your models here.
@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    # Поиск по полям
    search_fields = ("name",)


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    # Поиск по полям
    search_fields = ("full_name",)


@admin.register(Filmwork)
class FilmworkAdmin(admin.ModelAdmin):
    inlines = (
        GenreFilmworkInline,
        PersonFilmworkInline,
    )
    # Отображение полей в списке
    list_display = (
        "title",
        "type",
        "creation_date",
        "rating",
    )
    # Фильтрация в списке
    list_filter = ("type", "creation_date")
    # Поиск по полям
    search_fields = ("title", "description", "id")
