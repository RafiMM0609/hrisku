import calendar

def get_days_in_month(year, month):
    return calendar.monthrange(year, month)[1]

# Contoh penggunaan
year = 2025
month = 4

days_in_month = get_days_in_month(year, month)
print(f"Bulan {month}/{year} memiliki {days_in_month} hari.")

