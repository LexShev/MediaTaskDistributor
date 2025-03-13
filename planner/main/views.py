import datetime
import ast
import calendar

from django.shortcuts import render, redirect
from .forms import ListForm, WeekForm, CenzFormText, CenzFormDropDown
from .models import MainFilter

from .list_view import list_material_list
from .week_view import week_material_list
from .kpi_admin_panel import kpi_summary_calc, kpi_personal_calc
from .ffmpeg_info import ffmpeg_dict
from .detail_view import full_info, cenz_info, schedule_info
from .distribution import main_distribution


def index(request):
    return render(request, 'main/index.html')

def day(request):
    return render(request, 'main/day.html')

def week(request):
    start_day = datetime.datetime.today()
    start_day.strftime('%Y/%U')
    return redirect(week_date, start_day.year, start_day.isocalendar().week)

def week_date(request, work_year, work_week):
    init = MainFilter.objects.get(owner=request.user.id)
    if request.method == 'POST':
        form = WeekForm(request.POST, instance=init)
        if form.is_valid():
            form.save()

            channels = ast.literal_eval(form.cleaned_data.get('channels'))
            workers = ast.literal_eval(form.cleaned_data.get('workers'))
            material_type = ast.literal_eval(form.cleaned_data.get('material_type'))
            task_status = ast.literal_eval(form.cleaned_data.get('task_status'))

        else:
            channels = (2, 3, 4, 5, 6, 7, 8, 9, 10, 12)
            workers = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)
            task_status = ('not_ready', 'ready', 'fix')
            material_type = ('film', 'season')
    else:
        channels = ast.literal_eval(init.channels)
        workers = ast.literal_eval(init.workers)
        material_type = ast.literal_eval(init.material_type)
        work_dates = str(init.work_dates)
        task_status = ast.literal_eval(init.task_status)

        initial_dict = {'channels': channels,
                        'workers': workers,
                        'material_type': material_type,
                        'work_dates': work_dates,
                        'task_status': task_status}
        form = WeekForm(initial=initial_dict)
    material_list, service_dict = week_material_list(channels, workers, material_type, task_status, work_year, work_week)
    data = {'week_material_list': material_list, 'service_dict': service_dict, 'form': form}
    return render(request, 'main/week.html', data)

def month(request):
    calendar_dict = calendar.HTMLCalendar(0).formatyear(2025)
    calendar_dict = calendar.HTMLCalendar(0).formatmonth(2025, 1)
    return render(request, 'main/month.html', {'calendar_dict': calendar_dict})

def full_list(request):
    # main_search = request.GET.get('search', None)
    init = MainFilter.objects.get(owner=request.user.id)
    if request.method == 'POST':
        form = ListForm(request.POST, instance=init)
        if form.is_valid():
            form.save()

            # MainFilter.objects.filter(id=5).update(form)
            # form.save()
            # list_filter = form.save(commit=False)
            # list_filter.owner = request.user.id
            # print('request.user.id', request.user.id)
            channels = ast.literal_eval(form.cleaned_data.get('channels'))
            workers = ast.literal_eval(form.cleaned_data.get('workers'))
            material_type = ast.literal_eval(form.cleaned_data.get('material_type'))
            work_dates = form.cleaned_data.get('work_dates')
            task_status = ast.literal_eval(form.cleaned_data.get('task_status'))

        else:
            channels = (2, 3, 4, 5, 6, 7, 8, 9, 10, 12)
            work_dates = datetime.datetime.today().date()
            workers = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)
            task_status = ('not_ready', 'ready', 'fix')
            material_type = ('film', 'season')
    else:
        channels = ast.literal_eval(init.channels)
        workers = ast.literal_eval(init.workers)
        material_type = ast.literal_eval(init.material_type)
        work_dates = str(init.work_dates)
        task_status = ast.literal_eval(init.task_status)

        # initial_dict = {'channels': channels,
        #                 'workers': workers,
        #                 'material_type': material_type,
        #                 'work_dates': str(datetime.datetime.today().date()),
        #                 'task_status': task_status}
        initial_dict = {'channels': channels,
                        'workers': workers,
                        'material_type': material_type,
                        'work_dates': work_dates,
                        'task_status': task_status}
        form = ListForm(initial=initial_dict)

    data = {'material_list': list_material_list(channels, workers, material_type, str(work_dates), task_status),
            'form': form}
    # main_distribution()
    return render(request, 'main/list.html', data)

def material_card(request, program_id):
    custom_fields = cenz_info(program_id)
    if request.method == 'POST':
        form_drop = CenzFormDropDown(request.POST)
        form_text = CenzFormText(request.POST)
        if form_text.is_valid():
            lgbt_form = form_text.cleaned_data['lgbt_form']
            print('lgbt_form', lgbt_form)
        if form_drop.is_valid():
            tags_form = form_drop.cleaned_data['cenz_rate_form']
            print('tags_form', tags_form)
            meta_form = form_drop.cleaned_data['meta_form']
            print('meta_form', meta_form)

    else:
        print('no')
        form_drop = CenzFormDropDown(
            initial={'meta_form': custom_fields.get(17),
            'work_date_form': custom_fields.get(7),
            'cenz_rate_form': custom_fields.get(14),
            'cenz_worker_form': custom_fields.get(15),
            'tags_form': custom_fields.get(18),
            'inoagent_form': custom_fields.get(19),
            })
        print('custom_fields.get(7)', custom_fields.get(7))
        form_text = CenzFormText(
            initial={'lgbt_form': custom_fields.get(8),
            'sig_form': custom_fields.get(9),
            'obnazh_form': custom_fields.get(10),
            'narc_form': custom_fields.get(11),
            'mat_form': custom_fields.get(12),
            'other_form': custom_fields.get(13),
            'editor_form': custom_fields.get(16)})

    data = {'full_info': full_info(program_id),
            'custom_fields': custom_fields,
            'schedule_info': schedule_info(program_id),
            'ffmpeg': ffmpeg_dict(program_id),
            'form_text': form_text,
            'form_drop': form_drop,
            }
    return render(request, 'main/full_info_card.html', data)

def kpi_info(request):
    work_date = request.POST.get('work_date', str(datetime.datetime.today().date()))
    workers = request.POST.get('workers', (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11))
    data = kpi_summary_calc(work_date, workers)
    return render(request, 'main/kpi_admin_panel.html', data)

def kpi_worker(request, worker_id):
    work_date = request.POST.get('work_date', str(datetime.datetime.today().date()))
    data = kpi_personal_calc(work_date, worker_id)
    return render(request, 'main/kpi_worker.html', data)

def test_page(request):
    print(list(request.POST.items()))
    return render(request, 'main/test_page.html')

def my_view(request):
    print(list(request.POST.items()))
    if request.method == 'POST':
        form = ListForm(request.POST)
        print(form)
        if form.is_valid():
            selected_date = form.cleaned_data['date']
            selected_channels = form.cleaned_data['channels']
            selected_workers = form.cleaned_data['workers']
            print('selected_date', selected_date)
            print('selected_channels', selected_channels)
            print('selected_workers', selected_workers)

            # Process the selected values as a list
            # ...
    else:
        form = ListForm()

    return render(request, 'main/list_filter.html', {'form': form})