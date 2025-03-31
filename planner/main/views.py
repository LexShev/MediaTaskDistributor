import datetime
import ast
# import calendar

from django.shortcuts import render, redirect

from .full_material_list import select_pool, service_pool_info
from .forms import ListForm, WeekForm, CenzFormText, CenzFormDropDown, KpiForm, VacationForm
from .logs_and_history import insert_action, select_actions
from .models import MainFilter

from .list_view import list_material_list
from .week_view import week_material_list
from .kpi_admin_panel import kpi_summary_calc, kpi_personal_calc
from .ffmpeg_info import ffmpeg_dict
from .detail_view import full_info, cenz_info, schedule_info, change_db_cenz_info, change_task_status
from .distribution import main_distribution
from .report_calendar import my_report_calendar
from .work_calendar import my_work_calendar, drop_day_off, insert_day_off, vacation_info, insert_vacation, drop_vacation
from django.contrib.auth.decorators import login_required


def index(request):
    return render(request, 'main/index.html')

def day(request):
    return render(request, 'main/day.html')


def week(request):
    start_day = datetime.datetime.today()
    start_day.strftime('%Y/%U')
    return redirect(week_date, start_day.year, start_day.isocalendar().week)

@login_required()
def week_date(request, work_year, work_week):
    if request.user.id:
        init = MainFilter.objects.get(owner=request.user.id)
    else:
        init = MainFilter.objects.get(owner=0)
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
    today = datetime.datetime.today()
    cal_year, cal_month = today.year, today.month
    return redirect(month_date, cal_year, cal_month)

@login_required()
def month_date(request, cal_year, cal_month):
    month_calendar, task_list, service_dict = my_report_calendar(cal_year, cal_month)
    data = {'month_calendar': month_calendar,
            'task_list': task_list,
            'service_dict': service_dict}
    return render(request, 'main/month.html', data)

@login_required()
def full_list(request):
    # main_search = request.GET.get('search', None)
    # print('main_search', main_search)
    if request.user.id:
        init = MainFilter.objects.get(owner=request.user.id)
    else:
        init = MainFilter.objects.get(owner=0)

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

@login_required()
def material_card(request, program_id):

    custom_fields = cenz_info(program_id)
    old_values_dict = {
        17: custom_fields.get(17),
        7: custom_fields.get(7),
        14: custom_fields.get(14),
        15: custom_fields.get(15),
        18: custom_fields.get(18),
        19: custom_fields.get(19),
        8: custom_fields.get(8),
        9: custom_fields.get(9),
        10: custom_fields.get(10),
        11: custom_fields.get(11),
        12: custom_fields.get(12),
        13: custom_fields.get(13),
        16: custom_fields.get(16)
    }
    # work_date
    if custom_fields.get(7) and not isinstance(custom_fields.get(7), str):
        custom_fields[7] = str(custom_fields.get(7).date())

    if request.method == 'POST':
        form_drop = CenzFormDropDown(request.POST)
        form_text = CenzFormText(request.POST)
        if form_text.is_valid() and form_drop.is_valid():
            new_values_dict = {
                17: form_drop.cleaned_data.get('meta_form'),
                7: form_drop.cleaned_data.get('work_date_form'),
                14: form_drop.cleaned_data.get('cenz_rate_form'),
                15: form_drop.cleaned_data.get('cenz_worker_form'),
                18: form_drop.cleaned_data.get('tags_form'),
                19: form_drop.cleaned_data.get('inoagent_form'),
                8: form_text.cleaned_data.get('lgbt_form'),
                9: form_text.cleaned_data.get('sig_form'),
                10: form_text.cleaned_data.get('obnazh_form'),
                11: form_text.cleaned_data.get('narc_form'),
                12: form_text.cleaned_data.get('mat_form'),
                13: form_text.cleaned_data.get('other_form'),
                16: form_text.cleaned_data.get('editor_form')
            }
            service_info_dict = {
                'program_id': program_id,
                'worker_id': 11
            }


            insert_action(service_info_dict, old_values_dict, new_values_dict)
            change_db_cenz_info(service_info_dict, old_values_dict, new_values_dict)

            cenz_worker = new_values_dict.get(15)
            work_date = new_values_dict.get(7)
            change_task_status(program_id, cenz_worker, work_date)


    else:
        form_drop = CenzFormDropDown(
            initial={
                'meta_form': custom_fields.get(17),
                'work_date_form': custom_fields.get(7),
                'cenz_rate_form': custom_fields.get(14),
                'cenz_worker_form': custom_fields.get(15),
                'tags_form': custom_fields.get(18),
                'inoagent_form': custom_fields.get(19),
            })
        form_text = CenzFormText(
            initial={
                'lgbt_form': custom_fields.get(8),
                'sig_form': custom_fields.get(9),
                'obnazh_form': custom_fields.get(10),
                'narc_form': custom_fields.get(11),
                'mat_form': custom_fields.get(12),
                'other_form': custom_fields.get(13),
                'editor_form': custom_fields.get(16)
            })

    data = {'full_info': full_info(program_id),
            'custom_fields': custom_fields,
            'schedule_info': schedule_info(program_id),
            'actions_list': select_actions(program_id),
            'ffmpeg': ffmpeg_dict(program_id),
            'form_text': form_text,
            'form_drop': form_drop,
            }
    return render(request, 'main/full_info_card.html', data)

def kpi_info(request):
    work_date = str(datetime.datetime.today().date())
    workers = ''
    task_status = ''
    material_type = ''
    if request.method == 'POST':
        form = KpiForm(request.POST)
        if form.is_valid():
            work_date = str(form.cleaned_data.get('work_date_form'))
            workers = form.cleaned_data.get('workers_form')
            material_type = form.cleaned_data.get('material_type_form')
            task_status = form.cleaned_data.get('task_status_form')
    else:
        form = KpiForm(initial={
            'work_date_form': work_date,
            'workers_form': workers,
            'material_type_form': material_type,
            'task_status': task_status})

    # work_date = request.POST.get('work_date', str(datetime.datetime.today().date()))
    # workers = request.POST.get('workers', (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11))
    task_list, summary_dict = kpi_summary_calc(work_date, workers, material_type, task_status)
    data = {'task_list': task_list,
            'summary_dict': summary_dict,
            'today': datetime.datetime.today().date(),
            'form': form}
    return render(request, 'main/kpi_admin_panel.html', data)

def kpi_worker(request, worker_id):
    work_date = str(datetime.datetime.today().date())
    task_status = ''
    material_type = ''
    if request.method == 'POST':
        form = KpiForm(request.POST)
        if form.is_valid():
            work_date = str(form.cleaned_data.get('work_date_form'))
            material_type = form.cleaned_data.get('material_type_form')
            task_status = form.cleaned_data.get('task_status_form')
    else:
        form = KpiForm(initial={
            'work_date_form': work_date,
            'material_type': material_type,
            'task_status': task_status})
    task_list, summary_dict = kpi_personal_calc(work_date, worker_id, material_type, task_status)
    data = {'task_list': task_list,
            'summary_dict': summary_dict,
            'today': datetime.datetime.today().date(),
            'form': form}
    return render(request, 'main/kpi_worker.html', data)

def test_page(request):
    return render(request, 'main/dynamic_search.html')

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

def common_pool(request):
    data = {'pool_list': select_pool(), 'service_dict': service_pool_info()}
    return render(request, 'main/common_pool.html', data)

def work_calendar(request, cal_year):
    delete_day_off = request.POST.get('delete_day_off', None)
    approve_day_off = request.POST.get('approve_day_off', None)
    delete_vacation = request.POST.get('delete_vacation', None)
    if request.method == 'POST':
        form = VacationForm(request.POST)
        if form.is_valid():
            worker_id = form.cleaned_data['workers_form']
            start_date = form.cleaned_data['start_date_form']
            end_date = form.cleaned_data['end_date_form']
            description = form.cleaned_data['description_form']
            insert_vacation(worker_id, start_date, end_date, description)
        form = VacationForm()
    else:
        form = VacationForm()

    if delete_day_off:
        drop_day_off(delete_day_off)
    if approve_day_off:
        insert_day_off(approve_day_off)

    if delete_vacation:
        drop_vacation(delete_vacation)

    data = {'year_calendar': my_work_calendar(cal_year),
            'prev_year': cal_year-1,
            'year_num': cal_year,
            'next_year': cal_year+1,
            'vacation_list': vacation_info(cal_year),
            'form': form}
    return render(request, 'main/work_calendar.html', data)