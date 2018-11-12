import numpy as np
import bisect
from datetime import datetime, timedelta


class Stock:
    def __init__(self, prices, dates, timestamps=None):
        """Constructor: creates a Stock instance by loading the stock data.

        Args:
            prices (numpy.ndarray, float): A vector containing stock prices.
            dates (numpy.ndarray, int): A vector containing dates associated with
                    the stock prices. The dates must be in the format YYYYMMDD, where
                    YYYY stands in for the year, MM for the month and DD for days. For
                    example: 20080304, 20090512, 20121231.
            timestamps (numpy.ndarray, int): A vector containing time stamps associated
                    with the stock prices. The timestamps must be in the format HHMM,
                    where HH stands for the hour information and MM for the minutes.
                    For example: 1234, 1435, 1001, 935, 901.
        """
        if len(prices) != len(dates):
            raise ValueError("Length of prices and dates do not match.")
        if timestamps is not None and len(prices) != len(timestamps):
            raise ValueError("Length of prices and time stamps do not match")
        # setup variables for printing class via __repr__
        self.__filepath = None    # updated via the `fromCSV` constructor
        self.__repr = {'prices': repr(prices),
                       'dates': repr(dates),
                       'timestamps': repr(timestamps)}
        # fill instance with: date and time stamps, returns, variances and jumps
        self.datetimes = self.getDatetime(dates, timestamps)
        totals = self.getCount(self.datetimes)
        self.total = {'prices': totals[0],  # number of price observations per day
                      'returns': totals[0] - 1,  # number of returns per day
                      'days': totals[1]}         # total number of days
        self.returns = self.getReturns(
            prices, self.total['prices'], self.total['days'])
        self.RV = self.getRV(self.returns)
        self.BV = self.getBV(self.returns)
        self.TOD = self.getTOD(self.returns)
        self.rc, self.rd = self.separateReturns(
            self.returns, self.BV, self.TOD)
        self.total['jumps'] = np.sum(self.rd != 0)
        self.total['diffusive'] = self.total['returns'] * \
            self.total['days'] - self.total['jumps']

    def __repr__(self):
        if self.__filepath is None:
            spacing = ' '*len('Stock(')
            return (f'Stock(\n'
                    f'{spacing}prices={self.__repr["prices"]},\n'
                    f'{spacing}dates={self.__repr["dates"]},\n'
                    f'{spacing}timestamps={self.__repr["timestamps"]})')
        else:
            return f"Stock.fromCSV('{self.__filepath}')"

    @classmethod
    def fromCSV(cls, filepath):
        """Constructor: creates a Stock instance by loading the stock data
           from a CSV file.

        The file should contain no headers and have 3 columns.
        The 1st column should have date stamps in the format YYYYMMDD (year,
        month and  day). The 2nd column should have time stamps in the format HHMM
        (hour and minute). The 3rd column should have stock price values.

        Examples of valid lines:
        20070805,0935,12.34
        20121231,1404,0.35

        The first two columns are imported as integers, and the last column is
        imported as floats.

        Args:
            filepath (string): Path to the CSV file to be imported.

        Returns:
            (Stock): An instance of the Stock class where prices and date/time stamps
                     were loaded from the supplied CSV file.
        """
        data = cls.importStock(filepath)
        stock = cls(prices=data['price'],
                    dates=data['date'],
                    timestamps=data['time'])
        stock.filepath = filepath
        return stock

    @classmethod
    def fromDatetimes(cls, prices, datetimes):
        """Constructor: creates a Stock instance by using date and time stamps already
        in the datetime.datetime format.

        Note:
            This constructor is not faster than the default constructor. It only
            offers convenience if you already have a vector with datetime.datetime
            instances.

        Args:
            prices (numpy.ndarray, float): A vector containing stock prices.
            dates (numpy.ndarray, int): A vector containing datetime.datetime instances
                    each containing date (and possible time) stamps associated with
                    the price observations.

        Returns:
            (Stock): An instance of the Stock class.
        """
        def toDate(datetime):
            return datetime.year*10**4 + datetime.month*10**2 + datetime.day

        def toTime(datetime):
            return datetime.hour*10**2 + datetime.minute

        dates = np.vectorize(toDate)(datetimes)
        times = np.vectorize(toTime)(datetimes)
        return Stock(prices, dates, times)

    @staticmethod
    def importStock(filepath):
        """Imports a CSV file containing stock prices and their associated
           date and time stamps.

        The file should contain no headers and have 3 columns.
        The 1st column should have date stamps in the format YYYYMMDD (year,
        month and  day). The 2nd column should have time stamps in the format HHMM
        (hour and minute). The 3rd column should have stock price values.

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

    @staticmethod
    def getDatetime(date, time=None):
        """Creates datetime.datetime instances from sorted lists containing
           date and time stamps of stock prices.

        Args:
            date (iterable): List of dates in the format YYYYMMDD (year, month and day).
            time (iterable): List of time stamps in the format HHMM (hour and minute).

        Returns:
            datetimes (numpy.ndarray): List containing datetime.datetime instances.
        """
        # define splits for YYYYMMDD and HHMM
        date_slice = (slice(0, 4), slice(4, 6), slice(6, 8))
        time_slice = (slice(0, -2), slice(-2, 4))
        datetimes = []
        if time is not None:
            for YYYYMMDD, HHMM in zip(date, time):
                date_str, time_str = str(YYYYMMDD), str(HHMM)
                datetimes.append(
                    datetime(*[int(date_str[slice_]) for slice_ in date_slice],
                             *[int(time_str[slice_]) for slice_ in time_slice]))
        else:                   # no time stamp is supplied, only dates
            for YYYYMMDD in date:
                date_str = str(YYYYMMDD)
                datetimes.append(
                    datetime(*[int(date_str[slice_]) for slice_ in date_slice]))
        return np.array(datetimes)

    @staticmethod
    def getCount(datetimes):
        """Calculates the total number of days and prices per day
           assuming rectangular data (same number of prices per day for each day).

        Args:
            datetimes (numpy.ndarray): List containing datetime.datetime instances.
                                       Assumes list is sorted.

        Returns:
            prices_per_day (int): Total number of price observations per day.
                                  This number only makes sense for rectangular data.
            total_days (int): Total number of days.
        """
        # use bisect for fast search since datetimes is sorted
        # create a datetime that has no time information
        # this guarantees it will be >= the first day
        # and also <= the second day
        first_day = datetimes[0]
        next_day = datetime(first_day.year,
                            first_day.month,
                            first_day.day) + timedelta(1)
        prices_per_day = bisect.bisect_right(datetimes, next_day)
        assert prices_per_day > 0, "Zero prices per day"
        total_days = len(datetimes) // prices_per_day
        assert len(datetimes) == total_days * prices_per_day,\
            "Non-rectangular data"
        return prices_per_day, total_days

    @staticmethod
    def getReturns(prices, N, T):
        """Calculates intraday geometric (log) returns from prices.
           Excludes overnight returns.

        Args:
            prices (numpy.ndarray): List of a stock price in dollars.
                                    There should be a total of N * T prices
            N (int): Number of prices per day in the data
            T (int): Total number of days in the data

        Returns:
            (numpy.ndarray): A matrix of dimensions N x T containing geometric
                             returns. Each column represents a day, and each line
                             the return over a period of the day.
        """
        assert len(prices) == N*T, "Non-rectangular data"
        assert np.all(prices > 0), "Negative price"
        matrix = prices.reshape((N, T), order='F')
        return np.diff(np.log(matrix), axis=0)

    @staticmethod
    def getRV(returns):
        """Calculates the daily Realized Variance from intraday returns.

        Args:
            returns (numpy.ndarray): An n x T matrix containing intraday geometric
                                     returns, where n is the number of returns in
                                     any given day and T is the number of days.

        Returns:
            (numpy.ndarray): A vector of size T containing the realized variance
                             for each day.
        """
        return np.sum(returns**2, axis=0)

    @staticmethod
    def getBV(returns):
        """Calculates the daily Bipower Variance from intraday returns.

        Args:
            returns (numpy.ndarray): An n x T matrix containing intraday geometric
                                     returns, where n is the number of returns in
                                     any given day and T is the number of days.

        Returns:
            (numpy.ndarray): A vector of size T containing the bipower variance
                             for each day.
        """
        scaling = np.pi/2
        return scaling*np.sum(np.abs(returns[:-1, :]*returns[1:, :]), axis=0)

    @staticmethod
    def getTOD(returns):
        """Calculates the time of day factor (intraday variance pattern) from
           intraday returns.

        Args:
            returns (numpy.ndarray): An n x T matrix containing intraday geometric
                                     returns, where n is the number of returns in
                                     any given day and T is the number of days.

        Returns:
            (numpy.ndarray): A vector of size n containing the time of day factor
                             for each sampling period of the day.
        """
        tod = np.mean(np.abs(returns[:-1, :] * returns[1:, :]), axis=1)
        # need to scale tod to have average equal to 1
        tod = np.insert(tod, 0, tod[0])  # duplicate the first value
        return tod/np.mean(tod)

    @staticmethod
    def separateReturns(returns, BV, TOD, alpha=5):
        """Separates diffusive returns from jump returns.

        Args:
            returns (numpy.ndarray): An n x T matrix containing intraday geometric
                                     returns, where n is the number of returns in
                                     any given day and T is the number of days.
            BV (numpy.ndarray): A vector of size T containing the bipower variance
                                for each day.
            TOD (numpy.ndarray): A vector of size n containing the time of day factor
                                 for each sampling period of the day.

        Returns:
            rc (numpy.ndarray): An n x T matrix containing the intraday diffusive
                                returns.
            rd (numpy.ndarray): An n x T matrix containing the intraday jump
                                returns.
        """
        # count number of returns and number of days
        n, T = returns.shape[0], returns.shape[1]
        assert len(BV) == T,\
            "Number of days does not match with Bipower Variance dimension"
        assert len(TOD) == n,\
            "Number of returns per day does not match with Time of day factor dimension"
        # compute jump threshold, one per return
        scaling = alpha*(1/n)**0.49
        threshold = scaling * \
            np.sqrt(np.kron(BV, TOD).reshape((n, T), order='F'))
        # separate diffusive from jump returns
        rc, rd = np.zeros(returns.shape), np.zeros(returns.shape)
        rc_indices = np.abs(returns) <= threshold
        rd_indices = np.logical_not(rc_indices)
        rc[rc_indices] = returns[rc_indices]
        rd[rd_indices] = returns[rd_indices]
        return rc, rd