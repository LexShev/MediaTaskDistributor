from django.template.defaulttags import register


@register.filter
def fields_name(field_id):
    if field_id:
        field_id = int(field_id)
    fields_dict = {
        5: 'Краткое описание',
        7: 'Дата отсмотра',
        8: 'ЛГБТ',
        9: 'Сигареты',
        10: 'Обнаженка',
        11: 'Наркотики',
        12: 'Мат',
        13: 'Другое',
        14: 'Ценз отсмотра',
        15: 'Тайтл проверил',
        16: 'Редакторские замечания',
        17: 'Meta',
        18: 'Теги',
        19: 'Иноагент'}
    return fields_dict.get(field_id)