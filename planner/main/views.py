import datetime
import ast

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from .common_pool import select_pool, service_pool_info
from .forms import ListFilter, WeekFilter, CenzFormText, CenzFormDropDown, KpiForm, VacationForm
from .header_search import fast_search, advanced_search
from .logs_and_history import insert_action, select_actions
from .models import ModelFilter
from .list_view import list_material_list
from .permission_pannel import ask_db_permissions
from .week_view import week_material_list
from .kpi_admin_panel import kpi_summary_calc, kpi_personal_calc
from .ffmpeg_info import ffmpeg_dict
from .detail_view import full_info, cenz_info, schedule_info, change_db_cenz_info, change_task_status, update_file_path
from .distribution import main_distribution
from .month import report_calendar
from .work_calendar import my_work_calendar, drop_day_off, insert_day_off, vacation_info, insert_vacation, drop_vacation


@login_required()
def main_search(request):
    worker_id = request.user.id
    search_query = request.GET.get('fast_search', None)
    data = {'search_list': fast_search(search_query),
            'permissions': ask_db_permissions(worker_id)}
    return render(request, 'main/fast_search.html', data)

@login_required()
def dop_search(request):
    worker_id = request.user.id
    search_id = request.GET.get('search_id', 1)
    search_query = request.GET.get('search_query', None)
    data = {'search_list': advanced_search(int(search_id), search_query),
            'permissions': ask_db_permissions(worker_id)}
    return render(request, 'main/advanced_search.html', data)

def distribution(request):
    main_distribution()
    return redirect('home')

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
    worker_id = request.user.id
    if worker_id:
        init_dict = ModelFilter.objects.get(owner=worker_id)
    else:
        init_dict = ModelFilter.objects.get(owner=0)
    if request.method == 'POST':
        form = WeekFilter(request.POST, instance=init_dict)
        if form.is_valid():
            form.save()

            schedules = ast.literal_eval(form.cleaned_data.get('schedules'))
            engineers = ast.literal_eval(form.cleaned_data.get('engineers'))
            material_type = ast.literal_eval(form.cleaned_data.get('material_type'))
            task_status = ast.literal_eval(form.cleaned_data.get('task_status'))

        else:
            # channels = (2, 3, 4, 5, 6, 7, 8, 9, 10, 12)
            schedules = (3, 5, 6, 7, 8, 9, 10, 11, 12, 20)
            engineers = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)
            task_status = ('not_ready', 'ready', 'fix')
            material_type = ('film', 'season')
    else:
        schedules = ast.literal_eval(init_dict.schedules)
        engineers = ast.literal_eval(init_dict.engineers)
        material_type = ast.literal_eval(init_dict.material_type)
        task_status = ast.literal_eval(init_dict.task_status)

        initial_dict = {'schedules': schedules,
                        'engineers': engineers,
                        'material_type': material_type,
                        'task_status': task_status}
        form = WeekFilter(initial=initial_dict)
    material_list, service_dict = week_material_list(schedules, engineers, material_type, task_status, work_year, work_week)
    data = {'week_material_list': material_list,
            'service_dict': service_dict,
            'permissions': ask_db_permissions(worker_id),
            'form': form}
    return render(request, 'main/week.html', data)

def month(request):
    today = datetime.datetime.today()
    cal_year, cal_month = today.year, today.month
    return redirect(month_date, cal_year, cal_month)

@login_required()
def month_date(request, cal_year, cal_month):
    worker_id = request.user.id

    cal_day = request.POST.get('cal_day', None)
    if cal_day:
        cal_day = datetime.datetime.strptime(cal_day, '%Y-%m-%d')
        month_calendar, channels_list, service_dict = report_calendar(cal_year, cal_month, cal_day)
    else:
        month_calendar, channels_list, service_dict = report_calendar(cal_year, cal_month, datetime.date(cal_year, cal_month, day=1))
    data = {'month_calendar': month_calendar,
            'channels_list': channels_list,
            'service_dict': service_dict,
            'permissions': ask_db_permissions(worker_id)}
    return render(request, 'main/month.html', data)

@login_required()
def full_list(request):
    worker_id = request.user.id
    if worker_id:
        init_dict = ModelFilter.objects.get(owner=worker_id)
    else:
        init_dict = ModelFilter.objects.get(owner=0)

    if request.method == 'POST':
        form = ListFilter(request.POST, instance=init_dict)
        if form.is_valid():
            form.save()

            schedules = ast.literal_eval(form.cleaned_data.get('schedules'))
            engineers = ast.literal_eval(form.cleaned_data.get('engineers'))
            material_type = ast.literal_eval(form.cleaned_data.get('material_type'))
            work_dates = form.cleaned_data.get('work_dates')
            task_status = ast.literal_eval(form.cleaned_data.get('task_status'))


        else:
            schedules = (3, 5, 6, 7, 8, 9, 10, 11, 12, 20)
            work_dates = datetime.datetime.today().date()
            start_date = datetime.datetime.today().strftime('%d/%m/%Y')
            work_dates = f'{start_date} - {start_date}'
            engineers = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)
            task_status = ('not_ready', 'ready', 'fix')
            material_type = ('film', 'season')
    else:
        schedules = ast.literal_eval(init_dict.schedules)
        engineers = ast.literal_eval(init_dict.engineers)
        material_type = ast.literal_eval(init_dict.material_type)
        work_dates = init_dict.work_dates
        task_status = ast.literal_eval(init_dict.task_status)

        initial_dict = {'schedules': schedules,
                        'engineers': engineers,
                        'material_type': material_type,
                        'work_dates': work_dates,
                        'task_status': task_status}
        form = ListFilter(initial=initial_dict)


    # permissions = ask_permissions(worker_id)
    data = {'material_list': list_material_list(schedules, engineers, material_type, str(work_dates), task_status),
            'form': form, 'permissions': ask_db_permissions(worker_id)}
    return render(request, 'main/list.html', data)

@login_required()
def material_card(request, program_id):
    worker_id = request.user.id
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

        upload_ready_file = request.POST.get('upload_ready_file_form')
        update_file_path(program_id, upload_ready_file)
        print('upload_ready_file_form', upload_ready_file)
        if form_text.is_valid() and form_drop.is_valid():
            new_values_dict = {
                17: form_drop.cleaned_data.get('meta_form'),
                7: form_drop.cleaned_data.get('work_date_form'),
                14: form_drop.cleaned_data.get('cenz_rate_form'),
                15: form_drop.cleaned_data.get('engineers_form'),
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
                'worker_id': worker_id
            }
            insert_action(service_info_dict, old_values_dict, new_values_dict)
            change_db_cenz_info(service_info_dict, old_values_dict, new_values_dict)

            engineer = new_values_dict.get(15)
            work_date = new_values_dict.get(7)
            change_task_status(program_id, engineer, work_date, 'ready')


    else:
        form_drop = CenzFormDropDown(
            initial={
                'meta_form': custom_fields.get(17),
                'work_date_form': custom_fields.get(7),
                'cenz_rate_form': custom_fields.get(14),
                'engineers_form': custom_fields.get(15),
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
            'permissions': ask_db_permissions(worker_id)
            }
    return render(request, 'main/full_info_card.html', data)

@login_required()
def kpi_info(request):
    worker_id = request.user.id
    work_date = str(datetime.datetime.today().date())
    engineers = ''
    task_status = ''
    material_type = ''
    if request.method == 'POST':
        form = KpiForm(request.POST)
        if form.is_valid():
            work_date = str(form.cleaned_data.get('work_date_form'))
            engineers = form.cleaned_data.get('engineers_form')
            material_type = form.cleaned_data.get('material_type_form')
            task_status = form.cleaned_data.get('task_status_form')
    else:
        form = KpiForm(initial={
            'work_date_form': work_date,
            'engineers_form': engineers,
            'material_type_form': material_type,
            'task_status': task_status})

    # work_date = request.POST.get('work_date', str(datetime.datetime.today().date()))
    # engineers = request.POST.get('engineers', (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11))
    task_list, summary_dict = kpi_summary_calc(work_date, engineers, material_type, task_status)
    data = {'task_list': task_list,
            'summary_dict': summary_dict,
            'today': datetime.datetime.today().date(),
            'form': form,
            'permissions': ask_db_permissions(worker_id)}
    return render(request, 'main/kpi_admin_panel.html', data)

@login_required()
def engineer_profile(request, engineer_id):
    worker_id = request.user.id
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
    task_list, summary_dict = kpi_personal_calc(work_date, engineer_id, material_type, task_status)
    data = {'engineer_id': engineer_id,
            'task_list': task_list,
            'summary_dict': summary_dict,
            'today': datetime.datetime.today().date(),
            'permissions': ask_db_permissions(worker_id),
            'form': form}
    return render(request, 'main/kpi_engineer.html', data)

def test_page(request):
    return render(request, 'main/daterange_picker.html')

@login_required()
def common_pool(request):
    worker_id = request.user.id
    data = {'pool_list': select_pool(),
            'service_dict': service_pool_info(),
            'permissions': ask_db_permissions(worker_id)}
    return render(request, 'main/common_pool.html', data)

@login_required()
def work_year_calendar(request, cal_year):
    worker_id = request.user.id

    approve_day_off = request.POST.get('approve_day_off', None)
    if approve_day_off:
        insert_day_off(approve_day_off)
    delete_day_off = request.POST.get('delete_day_off', None)
    if delete_day_off:
        drop_day_off(delete_day_off)

    if request.method == 'POST':
        form = VacationForm(request.POST)
        if form.is_valid():
            engineer_id = form.cleaned_data['engineers_form']
            start_date = form.cleaned_data['start_date_form']
            end_date = form.cleaned_data['end_date_form']
            description = form.cleaned_data['description_form']
            insert_vacation(engineer_id, start_date, end_date, description)
        form = VacationForm()
    else:
        form = VacationForm()
    delete_vacation = request.POST.get('delete_vacation', None)
    if delete_vacation:
        drop_vacation(delete_vacation)

    data = {'year_calendar': my_work_calendar(cal_year),
            'prev_year': cal_year-1,
            'year_num': cal_year,
            'next_year': cal_year+1,
            'vacation_list': vacation_info(cal_year),
            'permissions': ask_db_permissions(worker_id),
            'form': form}
    return render(request, 'main/work_calendar.html', data)

def work_calendar(request):
    start_year = datetime.datetime.today().year
    return redirect(work_year_calendar, start_year)