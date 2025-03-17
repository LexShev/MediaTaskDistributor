import datetime
import ast
import calendar

from django.shortcuts import render, redirect
from .forms import ListForm, WeekForm, CenzFormText, CenzFormDropDown, KpiForm
from .insert_history import insert_action
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
    calendar_dict = calendar.HTMLCalendar(0).formatyear(2025)
    calendar_dict = calendar.HTMLCalendar(0).formatmonth(2025, 1)
    return render(request, 'main/month.html', {'calendar_dict': calendar_dict})

def full_list(request):
    # main_search = request.GET.get('search', None)
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

def material_card(request, program_id):

    custom_fields = cenz_info(program_id)

    old_meta = custom_fields.get(17)
    old_work_date = custom_fields.get(7)
    old_cenz_rate = custom_fields.get(14)
    old_cenz_worker = custom_fields.get(15)
    old_tags = custom_fields.get(18)
    old_inoagent = custom_fields.get(19)

    old_lgbt = custom_fields.get(8)
    old_sig = custom_fields.get(9)
    old_obnazh = custom_fields.get(10)
    old_narc = custom_fields.get(11)
    old_mat = custom_fields.get(12)
    old_other = custom_fields.get(13)
    old_editor = custom_fields.get(16)

    if old_work_date and not isinstance(old_work_date, str):
        old_work_date = str(old_work_date.date())

    if request.method == 'POST':
        form_drop = CenzFormDropDown(request.POST)
        form_text = CenzFormText(request.POST)
        if form_text.is_valid() and form_drop.is_valid():
            new_meta = form_drop.cleaned_data.get('meta_form')
            new_work_date = form_drop.cleaned_data.get('work_date_form')
            new_cenz_rate = form_drop.cleaned_data.get('cenz_rate_form')
            new_cenz_worker = form_drop.cleaned_data.get('cenz_worker_form')
            new_tags = form_drop.cleaned_data.get('tags_form')
            new_inoagent = form_drop.cleaned_data.get('inoagent_form')

            new_lgbt = form_text.cleaned_data.get('lgbt_form')
            new_sig = form_text.cleaned_data.get('sig_form')
            new_obnazh = form_text.cleaned_data.get('obnazh_form')
            new_narc = form_text.cleaned_data.get('narc_form')
            new_mat = form_text.cleaned_data.get('mat_form')
            new_other = form_text.cleaned_data.get('other_form')
            new_editor = form_text.cleaned_data.get('editor_form')
            # keys = (
            #     ('old_meta', 'new_meta'),
            #     ('old_work_date', 'new_work_date'),
            #     ('old_cenz_rate', 'new_cenz_rate'),
            #     ('old_cenz_worker', 'new_cenz_worker'),
            #     ('old_tags', 'new_tags'),
            #     ('old_inoagent', 'new_inoagent'),
            #     ('old_lgbt', 'new_lgbt'),
            #     ('old_sig', 'new_sig'),
            #     ('old_obnazh', 'new_obnazh'),
            #     ('old_narc', 'new_narc'),
            #     ('old_mat', 'new_mat'),
            #     ('old_other', 'new_other'),
            #     ('old_editor', 'new_editor'))
            # values = (
            #     (old_meta, new_meta),
            #     (old_work_date, new_work_date),
            #     (old_cenz_rate, new_cenz_rate),
            #     (old_cenz_worker, new_cenz_worker),
            #     (old_tags, new_tags),
            #     (old_inoagent, new_inoagent),
            #     (old_lgbt, new_lgbt),
            #     (old_sig, new_sig),
            #     (old_obnazh, new_obnazh),
            #     (old_narc, new_narc),
            #     (old_mat, new_mat),
            #     (old_other, new_other),
            #     (old_editor, new_editor))
            #
            # insert_dict = {'worker_id': 'worker_id', 'worker': 'worker', 'date_of_change': datetime.datetime.now()}
            # for key, val in zip(keys, values):
            #     old_key, new_key = key
            #     old_val, new_val = val
            #     if old_val or new_val:
            #         insert_dict[old_key] = old_val
            #         insert_dict[new_key] = new_val

            keys = (
                'old_meta', 'new_meta',
                'old_work_date', 'new_work_date',
                'old_cenz_rate', 'new_cenz_rate',
                'old_cenz_worker', 'new_cenz_worker',
                'old_tags', 'new_tags',
                'old_inoagent', 'new_inoagent',
                'old_lgbt', 'new_lgbt',
                'old_sig', 'new_sig',
                'old_obnazh', 'new_obnazh',
                'old_narc', 'new_narc',
                'old_mat', 'new_mat',
                'old_other', 'new_other',
                'old_editor', 'new_editor')
            values = (
                old_meta, new_meta,
                old_work_date, new_work_date,
                old_cenz_rate, new_cenz_rate,
                old_cenz_worker, new_cenz_worker,
                old_tags, new_tags,
                old_inoagent, new_inoagent,
                old_lgbt, new_lgbt,
                old_sig, new_sig,
                old_obnazh, new_obnazh,
                old_narc, new_narc,
                old_mat, new_mat,
                old_other, new_other,
                old_editor, new_editor)

            insert_dict = {'worker_id': 11, 'worker': 'Алексей Шевченко', 'date_of_change': str(datetime.datetime.now())}
            # .strftime("%Y-%m-%d %H:%M:%S")
            for key, val in zip(keys, values):
                if val:
                    if val == True:
                        val = 1
                    elif isinstance(val, datetime.date):
                        val = val.strftime('%Y-%m-%d')
                    insert_dict[key] = val

            insert_action(**insert_dict)

    else:
        form_drop = CenzFormDropDown(
            initial={
                'meta_form': old_meta,
                'work_date_form': old_work_date,
                'cenz_rate_form': old_cenz_rate,
                'cenz_worker_form': old_cenz_worker,
                'tags_form': old_tags,
                'inoagent_form': old_inoagent,
            })
        form_text = CenzFormText(
            initial={
                'lgbt_form': old_lgbt,
                'sig_form': old_sig,
                'obnazh_form': old_obnazh,
                'narc_form': old_narc,
                'mat_form': old_mat,
                'other_form': old_other,
                'editor_form': old_editor
            })

    data = {'full_info': full_info(program_id),
            'custom_fields': custom_fields,
            'schedule_info': schedule_info(program_id),
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