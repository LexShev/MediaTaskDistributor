from django.shortcuts import render


def main_view(request):
    return render(request, 'otk/work_list.html')
