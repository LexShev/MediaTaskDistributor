from datetime import datetime, timedelta

start_date = datetime.strptime('2025-03-18', '%Y-%m-%d')  # Замените на нужную стартовую дату
end_date = datetime.strptime('2025-03-23', '%Y-%m-%d')    # Замените на требуемую конечную дату
delta = timedelta(days=1)                                 # Интервал между датами установлен в 1 день

while start_date <= end_date:
    print(start_date.date())                              # Выводим дату
    start_date += delta

def date_generator(start, end, step):
    while start <= end:
        yield start                  # Возвращаем текущую дату
        start += step

print(list(date_generator(start_date, end_date, timedelta(days=1))))