from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class AstroImagePagination(PageNumberPagination):
    """Gallery-specific pagination for the public astrophotography feed."""

    page_size = 24
    page_size_query_param = "limit"
    max_page_size = 48

    def get_paginated_response(self, data):
        assert self.page is not None

        return Response(
            {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )
