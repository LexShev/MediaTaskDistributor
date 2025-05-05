from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from main.permission_pannel import ask_db_permissions

from .models import AdvancedSearch
from .forms import AdvancedSearchForm
from .header_search import fast_search
from .advanced_search import query_selector


@login_required()
def main_search(request):
    worker_id = request.user.id
    search_query = request.GET.get('fast_search', None)

    data = {'search_list': fast_search(search_query),
            'permissions': ask_db_permissions(worker_id)}
    return render(request, 'advanced_search/fast_search.html', data)

@login_required()
def dop_search(request):
    worker_id = request.user.id
    search_id = request.GET.get('search_id', 1)
    sql_set = request.GET.get('sql_set', 100)
    if search_id == '3':
        search_query = request.GET.get('engineers')
    else:
        search_query = request.GET.get('search_input')

    if worker_id:
        try:
            init_dict = AdvancedSearch.objects.get(owner=worker_id)
        except ObjectDoesNotExist:
            default_advanced_search = AdvancedSearch(owner=worker_id, search_id=1)
            default_advanced_search.save()
            init_dict = AdvancedSearch.objects.get(owner=worker_id)
            print("Новый поиск создан")
    else:
        init_dict = AdvancedSearch.objects.get(owner=0)
    print('search_query', search_query)
    if search_query:
        form = AdvancedSearchForm(request.GET, instance=init_dict)
        print('try to save data')
        if form.is_valid():
            print('new data saved')
            form.save()
    else:
        form = AdvancedSearchForm(initial={'search_id': 1, 'sql_set': sql_set})


    data = {'search_list': query_selector(int(search_id), int(sql_set), search_query),
            'search_id': int(search_id),
            'search_query': search_query,
            'permissions': ask_db_permissions(worker_id),
            'form': form,
            }
    return render(request, 'advanced_search/advanced_search.html', data)

