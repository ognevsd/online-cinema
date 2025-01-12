from django.http import JsonResponse
from django.views.generic.list import BaseListView
from django.views.generic.detail import BaseDetailView
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Q, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404


from movies.models import Filmwork


class MoviesApiMixin:
    model = Filmwork
    http_method_names = ["get"]

    def get_queryset(self):
        filmworks = Filmwork.objects.values(
            "id",
            "title",
            "description",
            "creation_date",
            "rating",
            "type",
        ).annotate(
            genres=Coalesce(ArrayAgg("genre__name", distinct=True), Value([])),
            actors=Coalesce(
                ArrayAgg(
                    "person__full_name",
                    filter=Q(personfilmwork__role="actor"),
                    distinct=True,
                ),
                Value([]),
            ),
            directors=Coalesce(
                ArrayAgg(
                    "person__full_name",
                    filter=Q(personfilmwork__role="director"),
                    distinct=True,
                ),
                Value([]),
            ),
            writers=Coalesce(
                ArrayAgg(
                    "person__full_name",
                    filter=Q(personfilmwork__role="writer"),
                    distinct=True,
                ),
                Value([]),
            ),
        )
        return filmworks

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(context)


class MoviesListApi(MoviesApiMixin, BaseListView):
    model = Filmwork
    http_method_names = ["get"]
    paginate_by = 50

    def get_context_data(self, *, object_list=None, **kwargs):
        queryset = self.get_queryset()
        paginator, page, queryset, is_paginated = self.paginate_queryset(
            queryset, self.paginate_by
        )
        context = {
            "count": paginator.count,
            "total_pages": paginator.num_pages,
            "prev": page.previous_page_number()
            if page.has_previous()
            else None,
            "next": page.next_page_number() if page.has_next() else None,
            "results": list(queryset),
        }
        return context


class MoviesDetailApi(MoviesApiMixin, BaseDetailView):
    def get_context_data(self, **kwargs):
        pk = self.kwargs.get("pk", None)
        movie = get_object_or_404(self.get_queryset(), id=pk)
        return movie  # Словарь с данными объекта
