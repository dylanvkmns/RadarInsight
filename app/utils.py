def validate_date(date_str):
    try:
        day, month, year = map(int, date_str.split("/"))
        return 1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2999
    except ValueError:
        return False