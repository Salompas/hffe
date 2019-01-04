from pandas import read_csv


# class Option:
#     def __init__(self, bid, ask):
#         self.bid = bid
#         self.ask = ask
#         self.price = (bid + ask)/2


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
