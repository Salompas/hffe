from datetime import datetime
from functools import partial

from pandas import read_csv

from .utilities import get3rdFriday
from .parsers import OptionChecker


class optionsFromCSV:
    def __init__(self, filepath, N, usecols=None, dtype=None):
        """Constructor: creates an iterable over options data stored
                        in a CSV file.

        Args:
            filepath (str): String to csv file containing options data.
            N (int): Number of obversvations per option. For example: N=405
                     means there are 405 observations per option in the file,
                     which amounts to 1-minute observations.
            usecols (tuple of int): A tuple of integers denoting which
                     columns to import from the file.
                     For example: usecols=(0, 2) will import the first and
                     third columns of the file. The default is None and
                     imports all columns.
            dtype (str or dict): If a string is passed, then all values
                     are imported using the same data type. If a dict is
                     passed, then the keys should denote the column numbers
                     and the values should be strings with the desired types.
                     For example: {0: 'float_', 1: 'int_', 13: 'str_'}.
        """
        self.filepath = filepath
        self.N = N              # number of observations per option per day
        config = {'sep': ',', 'header': 0, 'usecols': usecols, 'dtype': dtype}
        self.data = read_csv(filepath, **config)
        if len(self.data) % N != 0:
            raise ValueError("Total observations not divisible by N.")

    def optionsIterator(self):
        """Iterates over the options data, yielding data for each of
        the options.
        """
        total_obs = len(self.data)//self.N
        for i in range(total_obs):
            start = i*self.N
            stop = (i+1)*self.N - 1  # pandas slicing includes last index
            yield self.data.loc[start:stop, :]

    def __iter__(self):
        return self.optionsIterator()


class SPX:
    MINUTES_IN_YEAR = (365 * 24 * 60)
    SYMBOLS = set(['SPX', 'SPXW', 'SPXQ',
                   'SPB', 'SPQ', 'SPT', 'SPV', 'SPZ',
                   'SVP', 'SXB', 'SXM', 'SXY', 'SXZ',
                   'SYG', 'SYU', 'SYV', 'SZP', ])

    @classmethod
    def Checker(cls, verbose=False, assert_=True):
        """Checker returns an instance of the class hffe.parsers.OptionChecker,
        augmented to check for issues specific to SPX options."""
        conditions = (cls.acceptedSymbol, cls.weekly)
        if verbose:
            conditions = [partial(func, verbose=True) for func in conditions]
        checker = OptionChecker(verbose=verbose, assert_=assert_)
        checker.registerConditions(*conditions)
        return checker

    @classmethod
    def acceptedSymbol(cls, option, verbose=False):
        """Checks if option ticker symbol (root) corresponds to an accepted
        symbol."""
        if option.root.iloc[0] in cls.SYMBOLS:
            return True
        else:
            if verbose:
                print('Option root symbol not accepted')
            return False

    @classmethod
    def weekly(cls, option, verbose=False):
        """Keep only SPX options that are standard or weekly but being traded
        after 2013."""
        exp_date = datetime.strptime(option.expiration.iloc[0], '%Y-%m-%d')
        if cls.isWeekly(exp_date) and exp_date.year <= 2013:
            if verbose:
                print('Weekly option and before 2014')
            return False
        return True

    @classmethod
    def tenor(cls, today, expiration):
        """tenor computes the tenor of an SPX option following the
        CBOE's VIX methodology (see white paper).

        Args:
            today (datetime): A datetime object containing the quote datetime
                   of the option. Must have year, month, day, hour, minute and
                   second.
            expiration (date): A date object containing the expiration
                   date of the option. Must have year, month and day only.

        Returns:
            tenor (float): Tenor of the option in years.
        """
        assert expiration.isoweekday() != 7, "Option expires on Sunday"
        # some options have the expiration date set to saturday
        # change it to friday to compute tenor correctly
        if expiration.isoweekday() == 6:
            expiration = expiration.replace(day=(expiration.day - 1))
        # compute remaining minutes in current day
        # +1 for the minute between 23:59 and 24:00
        minutes_current_day = (
            (today.replace(hour=23, minute=59) - today).seconds // 60) + 1
        # compute remaining minutes for days until the expiration date
        # -1 for the day the option expires
        minutes_other = ((expiration - today.date()).days - 1) * (24 * 60)
        # compute remaining minutes on the settlement date
        # if the option is Weekly the settlement time is at 4 PM
        # if the option is Standard the settlement is at 9:30 AM
        # (PM settled if Weekly, AM settled if Standard SPX)
        # Standard SPX options expire on the 3rd Friday of the month
        if cls.isStandard(expiration):
            minutes_settlement = 9.5 * 60
        else:
            minutes_settlement = (9.5 + 2.5 + 4) * 60
        # Total minutes to expiration
        minutes_to_expiration = (minutes_current_day + minutes_other +
                                 minutes_settlement)
        return minutes_to_expiration / cls.MINUTES_IN_YEAR

    @staticmethod
    def isStandard(expiration):
        """isWeekly checks if expiration date corresponds to a Standard SPX
        option.

        Standard SPX options expire on the 3rd Friday of the month with AM
        settlement, meaning they close at the market open.

        Args:
            expiration (date): A date object containing the expiration
                       date of the option. Must have year, month and
                       day.

        Returns:
            (bool): True if Standard SPX option.
        """
        # some options have the expiration date set to saturday
        # change it to friday to compute tenor correctly
        if expiration.isoweekday() == 6:
            expiration = expiration.replace(day=(expiration.day - 1))
        third_friday = get3rdFriday(expiration.year, expiration.month)
        return expiration == third_friday

    @classmethod
    def isWeekly(cls, expiration):
        """isWeekly checks if the expiration date corresponds to a Weekly
        SPX option.

        Weeklys were introduced in 2005, but had a very low liquidity for many
        years. The CBOE itself did not include Weeklys in the computation of
        the VIX until after 2013 (in 2014 Weeklys were included). For this
        reason, when selecting options it is often argued that Weeklys
        prior to 2014 should be disconsidered.

        Args:
            expiration (date): A date object containing the expiration
                       date of the option. Must have year, month and
                       day.

        Returns:
            (bool): True if Weekly SPX option.

        """
        return not cls.isStandard(expiration)
