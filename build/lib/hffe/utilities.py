import time
from datetime import datetime


def timeFunction(func, *args, **kwargs):
    """Times one execution of function.

    Args:
        func (function): Function that takes no arguments.

    Returns:
        wrapper (function): Function that executes func and prints the time
                it took to finish running (in seconds).
    """
    def wrapper(*args, **kwargs):
        start = time.time()
        results = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f'Elapsed time: {elapsed:.2f} seconds.')
        return results
    return wrapper


def get3rdFriday(year, month):
    """get3rdFriday computes the 3rd friday of the month in a given year.

    The idea is to start with the earliest possible day that could be a
    Friday. This is the 15th of any month, since the fastest way to get to
    a 3rd Friday is for the 1st day of the month to be a Friday, so that
    after 2 weeks (14 days) we have the 3rd Friday.
    The Python datetime object knows what is the day of the week for any
    given day. We then check if the 15th is a Friday, if it is then we are
    done. If it is not, we know what day of the week it is, so we add
    however many days we need to reach the next Friday.

    Args:
        year (int): Integer representing year in the format YYYY.
        month (int): Integer representing month. Must be a value between
              1 and 12.

    Returns:
        friday (datetime): A datetime object containing the date of the
               3rd friday of the corresponding month and year.
    """
    d = datetime(year, month, 15)  # earliest possible 3rd friday
    # is d a Friday?
    w = d.weekday()
    # weekday()==4 for Friday (isoweekday()==5)
    if w != 4:
        d = d.replace(day=(15 + (4 - w) % 7))
    return d
