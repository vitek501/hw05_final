from django.core.paginator import Paginator


def get_page_context(queryset, request, count_post=10):
    paginator = Paginator(queryset, count_post)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
