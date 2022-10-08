from datetime import datetime
from dateutil import relativedelta


def months_between(start_date, end_date):
    date1 = datetime.strptime(str(start_date), '%Y-%m-%d')
    date2 = datetime.strptime(str(end_date), '%Y-%m-%d')
    return (date2.year - date1.year) * 12 + date2.month - date1.month

def dd_mm_yyy_to_y_m_d(date_str: str) -> str:
    """Formats date format mm/dd/yyyy eg.07/01/1988 to %Y-%m-%d
        OR  date format yyyy/mm/dd to  %Y-%m-%d
    Args:
        date (str): date string to be formated

    Returns:
        str: The formated date
    """
    if not date_str:
        return

    data = date_str.split('/')
    if len(data) > 2 and len(data[0]) ==2: #format mm/dd/yyyy
        try:
            #mm, dd, yy = int(data[0]), int(data[1]), data[2]
            dd, mm, yy = int(data[0]), int(data[1]), data[2]

            if mm > 12: #eg 04/21/2021" then reformat to 21/04/2021"
                dd, mm = mm, dd
            if mm > 12 or dd > 31 or len(yy) != 4:
                return
            return f"{yy}-{mm}-{dd}"
        except Exception:
            return
