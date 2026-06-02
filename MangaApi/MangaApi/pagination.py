from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsPagination(PageNumberPagination):
    """
    Paginación estándar para listas de catálogo.

    Query params:
        page      → número de página (default: 1)
        page_size → tamaño de página (default global de settings.PAGE_SIZE, máximo: 100)

    Ejemplo: GET /api/manga/mangas/?page=2&page_size=12
    """

    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(
            {
                "pagination": {
                    "count": self.page.paginator.count,
                    "pages": self.page.paginator.num_pages,
                    "page": self.page.number,
                    "page_size": self.get_page_size(self.request),
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                },
                "results": data,
            }
        )

    def get_paginated_response_schema(self, schema):
        """Esquema OpenAPI para drf-spectacular (si se usa)."""
        return {
            "type": "object",
            "required": ["pagination", "results"],
            "properties": {
                "pagination": {
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer", "example": 240},
                        "pages": {"type": "integer", "example": 10},
                        "page": {"type": "integer", "example": 1},
                        "page_size": {"type": "integer", "example": 24},
                        "next": {
                            "type": "string",
                            "nullable": True,
                            "example": "https://api.miswebtoons.uk/api/manga/mangas/?page=2",
                        },
                        "previous": {"type": "string", "nullable": True, "example": None},
                    },
                },
                "results": schema,
            },
        }
