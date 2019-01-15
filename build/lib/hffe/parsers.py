import numpy as np


class OptionChecker:
    def __init__(self, verbose=False, assert_=True):
        self.conditions = (self.zeroBid, self.zeroAsk, self.stalePrices)
        self.assertions = (self.assertOptionType, self.assertFirstLastDate)
        self.verbose = verbose
        self.assert_ = assert_

    def __call__(self, option):
        """Checks option data for liquidity issues and data recording issues.

        If the object is constructed with assert_=True, then recording issues
        are checked, and if any recording issue is found an AssertionError is
        raised.

        If the object is constructed with verbose=True, then whenever an
        option fails a check, a message is printed saying what failed.

        Args:
            option (pandas DataFrame): Dataframe containing options data. Must
                    have columns named bid and ask, containing bid and ask
                    prices stored as floats.

        Returns:
            result (bool): True if no issues are found in the data. False is
                    if some issue is encountered.
        """
        if self.assert_:
            all(self.checkAssertions(option))
        return all(self.checkConditions(option))

    def checkConditions(self, option):
        """Checks multiple conditions to validate whether an option's data
        does not suffer liquidity issues."""
        for condition in self.conditions:
            yield condition(option)

    def checkAssertions(self, option):
        """Checks whether option's data could have recording problems."""
        for assertion in self.assertions:
            yield assertion(option)

    def registerConditions(self, *extra_conditions):
        """Adds new conditions to be checked."""
        self.conditions = (*self.conditions, *extra_conditions)

    def registerAssertions(self, *extra_assertions):
        """Adds new assertions to be asserted."""
        self.assertions = (*self.assertions, *extra_assertions)

    # -------------- CONDITIONS ----------------
    # Conditions for an option's data to be considered ok
    #
    def zeroBid(self, option):
        """Checks if any of the reported bid prices are zero."""
        if any(option.bid == 0):
            if self.verbose:
                print('zero bid')
            return False
        else:
            return True

    def zeroAsk(self, option):
        """Checks if any of the reported ask prices are zero."""
        if any(option.ask == 0):
            if self.verbose:
                print('zero ask')
            return False
        else:
            return True

    def stalePrices(self, option, proportion=0.5):
        """Checks if prices do not change during most of the time period.

        Args:
            option (pandas DataFrame): Dataframe containing options data. Must
                    have columns named bid and ask, containing bid and ask
                    prices stored as floats.
            proportion (float): Number strictly between 0 and 1. Describes
                    the accepted proportion of stale prices in a day.
                    For example: if proportion is 0.3, then as long as less
                    than 30% of the price observations are stale (change),
                    then the option data is deemed ok. If more than 30% of
                    the options prices do not change from one time instant
                    to another, then the options data is considered stale.

        Returns:
            result (bool): True if prices are not stale, False otherwise.
        """
        price = (option.bid + option.ask)/2  # mid quote price
        no_changes = np.sum(np.diff(price) == 0)
        no_change_proportion = no_changes/price.size
        # if prices do not change most of the day
        if no_change_proportion > proportion:
            if self.verbose:
                print(f'stale prices: {100*no_change_proportion:.0f}% of day')
            return False
        else:
            return True
    # ------------------------------------------

    # -------------- ASSERTIONS ----------------
    # Assertions that show something is wrong in the data or code
    #
    def assertOptionType(self, option):
        """Checks if option type changes in the data, which indicates an error
        in the database or possibly the code.
        """
        first_type = option.option_type.iloc[0]
        assert all(option.option_type ==
                   first_type), "Single option has put and call types"
        return True

    def assertFirstLastDate(self, option, start='09:31:00', stop='16:15:00'):
        """Checks if the first and last quote times are as expected, and if
        there is no discrepancy in the dates."""
        f_date, f_time = option.quote_datetime.iloc[0].split(' ')
        assert f_time == start, f"Data has wrong start time (f{f_time})."
        l_date, l_time = option.quote_datetime.iloc[-1].split(' ')
        assert l_time == stop, f"Data has wrong stop time (f{l_time})."
        assert l_date == f_date, "Data ends at different date from start."
        return True
    # ------------------------------------------

    # -------------- UTILS ---------------------
    def isPut(self, option):
        """Checks if option is a put."""
        if all(option.option_type == 'P'):
            return True
        else:
            if self.verbose:
                print('call')
            return False
    # ------------------------------------------
