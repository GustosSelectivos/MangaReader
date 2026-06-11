from math import ceil
from typing import Any
from domains.mangas.schemas import PaginationMeta

def paginate(items: list[Any], total: int, page: int, page_size: int) -> dict:
    """
    Estandariza el formato de respuesta paginada para la API.
    """
    pages = ceil(total / page_size) if page_size else 1
    return {
        "pagination": PaginationMeta(
            count=total, pages=pages, page=page, page_size=page_size
        ),
        "results": items,
    }
