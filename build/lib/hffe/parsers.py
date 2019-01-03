import numpy as np


def stockFromCSV(filepath):
    """Imports a CSV file containing stock prices and their associated
       date and time stamps.

    The file should contain no headers and have 3 columns.
    The 1st column should have date stamps in the format YYYYMMDD (year,
    month and  day).
    The 2nd column should have time stamps in the format HHMM (hour and
    minute) or HHMSS (hour, minute and seconds).
    The 3rd column should have stock price values.

    Examples of valid lines:
    20070805,0935,12.34
    20121231,1404,0.35

    The first two columns are imported as integers, and the last column is
    imported as floats.

    Args:
        filepath (string): Path to the CSV file to be imported.

    Returns:
        (numpy.ndarray): Structured numpy array containing the keys 'date',
                         'time' and 'price'.
    """
    return np.loadtxt(filepath,
                      delimiter=',',
                      dtype={'names': ('date', 'time', 'price'),
                             'formats': ('int_', 'int_', 'float_')})
