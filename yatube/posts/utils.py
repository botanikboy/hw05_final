from django.core.paginator import Paginator

from .constants import POSTS_COUNT


def paginator_create(post_list, page_number):
    paginator = Paginator(post_list, POSTS_COUNT)
    return paginator.get_page(page_number)
