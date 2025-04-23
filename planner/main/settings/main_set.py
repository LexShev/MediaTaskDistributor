class MainSettings:
    status_dict = {
            'no_material': 'Материал отсутствует',
            'not_ready': 'Не готов',
            'fix': 'Исправление исходника',
            'ready': 'Отсмотрен',
            'otk': 'Прошёл ОТК',
            'otk_fail': 'На доработке',
            'final': 'Готов к эфиру',
            'ready_fail': 'На пересмотр'
        }

    color_dict = {
            'no_material': 'text-danger',
            'not_ready': 'text-primary',
            'fix': 'text-warning',
            'ready': 'text-success',
            'otk': 'text-success',
            'otk_fail': 'text-danger',
            'final': 'text-success',
            'ready_fail': 'text-danger'
        }