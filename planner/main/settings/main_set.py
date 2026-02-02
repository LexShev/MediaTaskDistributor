class MainSettings:
    status_dict = {
        'no_material': 'Материал отсутствует',
        'not_ready': 'Не готов',
        'fix': 'Исправление исходника',
        'fix_ready': 'Исходник исправлен',
        'ready': 'Отсмотрен',
        'otk': 'Прошёл ОТК',
        'otk_fail': 'Не прошёл ОТК',
        'final': 'Готов к эфиру',
        'final_fail': 'Не прошёл ЭК',
        'oplan_ready': 'Отсмотрен в Oplan3',
        'no_task_list': 'Не распределён',
        'common_pool': 'Материал из общего пула',
        'card_error': 'Карточка материала заполнена неверно',
    }

    color_dict = {
        'no_material': 'danger',
        'not_ready': 'primary',
        'fix': 'warning',
        'fix_ready': 'warning',
        'ready': 'success',
        'otk': 'info',
        'otk_fail': 'danger',
        'final': 'success',
        'final_fail': 'danger',
        'oplan_ready': 'success',
        'no_task_list': 'warning',
        'common_pool': 'info',
        'card_error': 'danger',
    }

    on_air_color_dict = {
        'no_material': 'danger',
        'not_ready': 'danger',
        'fix': 'warning',
        'fix_ready': 'warning',
        'ready': 'warning',
        'otk': 'warning',
        'otk_fail': 'danger',
        'final': 'success',
        'final_fail': 'danger',
        'oplan_ready': 'success',
        'no_task_list': 'warning',
        'common_pool': 'info',
        'card_error': 'danger',
    }

    channel_color_dict = {
        3: {'name': 'red', 'hex': '#dc3545', 'rgb': '220, 53, 69'},  # Крепкое
        5: {'name': 'blue', 'hex': '#0d6efd', 'rgb': '13, 110, 253'},  # Планета дети
        6: {'name': 'yellow', 'hex': '#ffc107', 'rgb': '255, 193, 7'},  # Мировой сериал
        7: {'name': 'orange', 'hex': '#fd7e14', 'rgb': '253, 126, 20'},  # Мужской сериал
        8: {'name': 'cyan', 'hex': '#0dcaf0', 'rgb': '13, 202, 240'},  # Наше детство
        9: {'name': 'pink', 'hex': '#d63384', 'rgb': '214, 51, 132'},  # Романтичный сериал
        10: {'name': 'green', 'hex': '#198754', 'rgb': '25, 135, 84'},  # Наше родное кино
        11: {'name': 'purple', 'hex': '#6f42c1', 'rgb': '111, 66, 193'},  # Семейное кино
        12: {'name': 'teal', 'hex': '#20c997', 'rgb': '32, 201, 151'},  # Советское родное кино
        20: {'name': 'indigo', 'hex': '#6610f2', 'rgb': '102, 16, 242'},  # Кино +
        36: {'name': 'orange-700', 'hex': '#984c0c', 'rgb': '152, 76, 12'}  # Кино Индии
    }
