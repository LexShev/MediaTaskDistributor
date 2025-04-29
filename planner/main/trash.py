import calendar
import datetime
from decimal import Decimal

# # Создаем обычный текстовый календарь
# c = calendar.TextCalendar(calendar.MONDAY)
# string = c.formatmonth(2025, 3)
# print(string)
#
# # Создаем календарь в формате HTML
# hc = calendar.HTMLCalendar(calendar.MONDAY)
# string = hc.formatmonth(2025, 4)
# print(string)
# # перебираем через цикл дни месяца
# # нули указывают, что дни принадлежат смежному месяцу
# for i in c.itermonthdays4(2025, 3):
#     print(i)
#     # Календарь может выдавать информацию на основе локальных настроек, таких как название дней и месяцев (полных или сокращенных)
# # for name in calendar.month_name:
# #     print(name)
# # for day in calendar.day_name:
# #     print(day)
# # вычисляем день на основе правил: Например для каждого второго понедельника каждого месяца
# # Устанавливаем это для каждого месяца, мы можем использовать следующий скрипт
# for month in range(1, 13):
#     # Он извлекает список недель, который представляет месяц
#     mycal = calendar.monthcalendar(2025, month)
#     # Первый MONDAY должен принадлежать первой или второй неделе
#     week1 = mycal[1]
#     week2 = mycal[2]
#     if week1[calendar.MONDAY] != 0:
#         auditday = week1[calendar.MONDAY]
#     else:
#     # если первый MONDAY не принадлежит первой неделе, он должен быть на второй неделе
#         auditday = week2[calendar.MONDAY]
#         print("%10s %2d" % (calendar.month_name[month], auditday))
#
#
# print(list(hc.itermonthdays(2025, 3)))
# print(list(hc.itermonthdays4(2025, 3)))
# print(calendar.monthcalendar(2025, 3))
# print(datetime.date(2025, 10, 6).weekday())
# print()
# month = calendar.Calendar()
# for week in month.monthdatescalendar(2025, 3):
#     print(week)
# print()
# print(list(month.itermonthdates(2025, 3)))
# print([day for day in month.itermonthdates(2025, 3) if day.month == 3])


# def convert_frames_to_time(frames, fps=25):
#     sec = int(frames) / fps
#     yy = int((sec // 3600) // 24) // 365
#     dd = int((sec // 3600) // 24) % 365
#     hh = int((sec // 3600) % 24)
#     mm = int((sec % 3600) // 60)
#     ss = int((sec % 3600) % 60 // 1)
#     ff = int(sec % 1 * fps)
#     tf = f'{hh:02}:{mm:02}:{ss:02}.{ff:02}'
#     if dd < 1 and yy < 1:
#         return f'{hh:02}:{mm:02}:{ss:02}'
#     elif 0 < yy%10 < 5:
#         return f'{yy:02}г. {dd:02}д. {hh:02}:{mm:02}:{ss:02}'
#     else:
#         return f'{yy:02}л. {dd:02}д. {hh:02}:{mm:02}:{ss:02}'
# print(datetime.timedelta(seconds=60*60*24*366))
# print(datetime.datetime.fromtimestamp(15).strftime("%A, %B %d, %Y %I:%M:%S"))
# print(convert_frames_to_time((25*60*60*24*365*24)+(25*60*60*24*365)))
# print(int((((788400026/25)//3600)//24)+1)%365)
# print(convert_frames_to_time(25*60*60*24*367))
# print(0%10)
# print(int(False))
# d=5
# print(f'{d:05}')
# eng_list = [0, 1, 2, 3, 4, 5, None, 6, False, 7]
# for engineer_id in eng_list:
#     if engineer_id or engineer_id == 0:
#         print(engineer_id)

# print(datetime.datetime(2025, 4, 23, 13, 19, 18, 360000))
# print( datetime.datetime(2025, 4, 23, 13, 22, 4, 290000))

program_id_list = [1234, 4321, 9876]
comments_list = ['comment_01', 'comment_02', 'comment_03']

print([{'program_id': program_id} for program_id in program_id_list])

fix_tuple = list(zip(program_id_list, comments_list))
for program_id, comments in fix_tuple:
    print({'program_id': program_id, 'comments': comments})

for prog_id, comment in zip(program_id_list, comments_list):
    print(dict((('prog_id', prog_id), ('comment', comment))))

print([dict((('prog_id', prog_id), ('comment', comment), ('deadline', None))) for prog_id, comment in zip(program_id_list, comments_list)])