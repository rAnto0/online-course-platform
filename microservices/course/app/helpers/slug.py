from slugify import slugify


def slugify_name(value: str) -> str:
    """
    Генерирует slug из названия. Использует транслитерацию для не-ASCII.
    """
    return slugify(value, lowercase=True)
