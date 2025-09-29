from datetime import date,datetime,timedelta

def date_str_to_date(s):
    # Convert string 'YYYYMMDD' to date object
    # FIXME: replace code in other functions
    # where that was done manually.
    s = s.strip()
    if s.find('-') != -1:
        # String in the format YYYY-MM-DD
        year_s,month_s,day_s = s.split('-')
    else:
        # String in the format YYYYMMDD
        year_s  = s[0:4]
        month_s = s[4:6]
        day_s   = s[6:8]
    return date(int(year_s),int(month_s),int(day_s))

def prev_weekday(dt,weekday):
  weekday_cur = dt.isocalendar()[2]
  while True:
    if weekday_cur == weekday:
      break
    dt = dt - timedelta(days=1)
    weekday_cur = dt.isocalendar()[2]
  return dt

if __name__ == '__main__':
  dt = datetime.now().date()
  print prev_weekday(dt,1)

