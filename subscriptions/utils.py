import jdatetime

def add_jalali_months(g_date, months_to_add):
    if not g_date:
        return None
    j_date = jdatetime.datetime.fromgregorian(datetime=g_date)
    new_month = j_date.month + months_to_add
    new_year = j_date.year + (new_month - 1) // 12
    new_month = (new_month - 1) % 12 + 1
    
    if new_month == 12 and jdatetime.date(new_year, 1, 1).isleap():
        max_days = 30
    elif new_month == 12:
        max_days = 29
    elif new_month <= 6:
        max_days = 31
    else:
        max_days = 30
        
    new_day = min(j_date.day, max_days)
    new_j_date = jdatetime.datetime(new_year, new_month, new_day, j_date.hour, j_date.minute, j_date.second, j_date.microsecond, tzinfo=j_date.tzinfo)
    return new_j_date.togregorian()
