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
            'final_fail': 'Не прошёл ЭК'
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
            'final_fail': 'danger'
        }