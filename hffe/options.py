from os import cpu_count
from concurrent import futures
from collections import namedtuple
from datetime import datetime
from functools import partial

from pandas import read_csv, DataFrame
from tqdm import tqdm
import numpy as np

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
    # List of symbols for SPX options, see Appendix A.1 of ABG2011
    SYMBOLS = set(['SPX', 'SPXW', 'SPXQ',
                   'SPB', 'SPQ', 'SPT', 'SPV', 'SPZ',
                   'SVP', 'SXB', 'SXM', 'SXY', 'SXZ',
                   'SYG', 'SYU', 'SYV', 'SZP', ])
    # Define field names for SPX data from CBOE
    # currently CBOE is the official vendor of SPX options data
    Field = namedtuple('Field', ('column_number', 'field_type'))
    # The strings below are the column names in each of the csv
    # files containing SPX options data.
    Columns = {'quote_datetime': Field(1, 'str_'),
               'root':           Field(2, 'str_'),
               'expiration':     Field(3, 'str_'),
               'strike':         Field(4, 'float_'),
               'option_type':    Field(5, 'str_'),
               'trade_volume':   Field(10, 'float_'),
               'bid_size':       Field(11, 'float_'),
               'bid':            Field(12, 'float_'),
               'ask_size':       Field(13, 'float_'),
               'ask':            Field(14, 'float_'), }
    # Fields to be fetched
    FIELDS = ('quote_datetime', 'root', 'expiration', 'strike',
              'option_type', 'trade_volume', 'bid', 'ask',
              'bid_size', 'ask_size')

    @classmethod
    def getCSVConfig(cls, column_names):
        """Generates mapping of column numbers and data types required
        for reading the options data.

        The resulting dictionary is passed to the optionsFromCSV class
        constructor.

        Args:
            column_names (list of str): List containing the column names
                of the columns we want to fetch from the data.

        Returns:
            result (dict): Dictionary containing the column indices
                that correspond to the column names we want, and the
                corresponding data types of each column.

        Example:
            config = getCSVConfig('bid', 'ask')
            filename = '2007-03-01.csv'
            options_iterator = optionsFromCSV(filename, N=405, **config)
        """
        column_numbers = [
            cls.Columns[name].column_number for name in column_names]
        dtypes = {cls.Columns[name].column_number: cls.Columns[name].field_type for
                  name in column_names}
        config = {'usecols': column_numbers, 'dtype': dtypes}
        return config

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
    def createChecker(cls,
                      verbose=False,
                      assert_=True,
                      symbols=True,
                      weekly=True,
                      put_only=True,
                      traded=False):
        """Checker returns an instance of the class hffe.parsers.OptionChecker,
        augmented to check for issues specific to SPX options."""
        # Create basic checker
        checker = OptionChecker(verbose=verbose, assert_=assert_)
        # Add extra checkers for SPX type options
        conditions = []
        if symbols:
            conditions.append(cls.acceptedSymbol)
        if weekly:
            conditions.append(cls.weekly)
        if traded:
            conditions.append(cls.traded)
        if verbose:
            conditions = [partial(func, verbose=True) for func in conditions]
        if put_only:
            conditions.append(checker.isPut)  # isPut does not take verbose
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
    def traded(cls, option, threshold=1.0, verbose=False):
        """Keep only SPX options that have at least a certain number of trades
        at the given day."""
        if np.sum(option.trade_volume >= threshold):
            return True
        else:
            if verbose:
                print(f'Total trade volume for option is below {threshold}')
            return False

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
            expiration (datetime): A datetime object containing the expiration
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
        # get3rdFriday returns datetime so expiration needs to be datetime
        # otherwise comparison always fails
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
            expiration (datetime): A datetime object containing the expiration
                       date of the option. Must have year, month and
                       day.

        Returns:
            (bool): True if Weekly SPX option.

        """
        return not cls.isStandard(expiration)

    @classmethod
    def createQuery(cls, checker, parser):
        """Creates a dataframe containing all options data from
        a given filename.
        """
        config = cls.getCSVConfig(cls.FIELDS)

        def query(filename):
            data = []
            for option in optionsFromCSV(filename, N=405, **config):
                if checker(option):
                    data.append(parser(option))
            return DataFrame(data)
        return query

    @classmethod
    def getOptionsThreaded(cls, filenames, query):
        """Obtains all options data from a list of files. Uses threads to
        speed up I/O.

        Args:
            filenames (list[str]): Set containings the csv filenames from where
                to recover the options data.
            query (function): A function that parses one csv file, extracting
                the options data. To construct this function use
                SPX.createQuery.

        Returns:
            result (dict): Dictionary mapping filenames to dataframes with
                the options data.
        """
        to_do_map = {}
        errors = {}
        done_map = {}
        with futures.ThreadPoolExecutor(max_workers=2*cpu_count()) as executor:
            count = 0
            # Submit query for each filename
            for filename in filenames:
                future = executor.submit(query, filename)
                to_do_map[future] = filename
                count += 1
            done_iter = tqdm(futures.as_completed(to_do_map), total=count)
            for future in done_iter:
                filename = to_do_map[future]
                try:
                    res = future.result()
                except Exception as excep:
                    errors[filename] = excep
                else:
                    done_map[filename] = res
        return done_map, errors
