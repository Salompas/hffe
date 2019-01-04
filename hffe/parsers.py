import numpy as np


class OptionChecker:
    def __init__(self, verbose=False, assert_=False):
        self.condition = (self.zeroBid, self.zeroAsk, self.stalePrices,)
        self.assertions = (self.assertOptionType,)
        self.verbose = verbose
        self.assert_ = assert_

    def __call__(self, option):
        if self.assert_:
            all(self.checkAssertions(option))
        return all(self.checkConditions(option))

    def checkConditions(self, option):
        """Checks multiple conditions to validate whether an option's data
        does not suffer liquidity issues."""
        for condition in self.condition:
            yield condition(option)

    def checkAssertions(self, option):
        """Checks whether option's data could have recording problems."""
        for assertion in self.assertions:
            yield assertion(option)

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

    def stalePrices(self, option):
        """Checks if prices do not change during the time period."""
        price = (option.bid + option.ask)/2  # mid quote price
        price_changes = np.diff(price, axis=0)
        if all(price_changes == 0):  # if prices do not change all day
            if self.verbose:
                print('stale prices')
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
        first_type = option.option_type[0]
        assert all(option.option_type ==
                   first_type), "Single option has put and call types"
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
