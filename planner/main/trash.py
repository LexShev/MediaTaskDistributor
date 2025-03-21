import calendar
import datetime
# # Создаем обычный текстовый календарь
c = calendar.TextCalendar(calendar.MONDAY)
string = c.formatmonth(2025, 3)
print(string)
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
print(calendar.monthcalendar(2025, 3))
print(datetime.date(2025, 10, 6).weekday())
print()
month = calendar.Calendar()
for week in month.monthdatescalendar(2025, 3):
    print(week)
print()
print(list(month.itermonthdates(2025, 3)))
print([day for day in month.itermonthdates(2025, 3) if day.month == 3])
