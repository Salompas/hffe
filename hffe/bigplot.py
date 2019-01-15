import matplotlib.pyplot as plt


class BigPlot:
    """BigPlot defines a metaclass to create 2D plots with matplotlib
    where points are incrementally added to the plot as the data is
    generated.
    """

    def __init__(self, create, update, filepath):
        """
        Args:
            create (function): Function that takes no arguments, creates
                   a figure with matplotlib.pyplot.subplots and returns
                   its fig and ax handles.
            update (function): Function that takes as arguments the ax
                   handles from the create function, and the data to plot.
                   This function should update the plot with the new data.
            filepath (string): File path to location where figure should
                   be saved.
        """
        self.filepath = filepath
        self.create = create
        self.update = update
        # Create figure and save it (still empty)
        self.fig, self.ax = self.create()
        self.save()

    def __call__(self, data, save=True):
        """Updates the figure with new data and saves it."""
        self.update(self.ax, data)
        if save:
            self.save()

    def save(self, dpi=200):
        """Saves plot to disk."""
        self.fig.savefig(self.filepath, dpi=dpi)

    def close(self):
        """Closes figure."""
        plt.close(self.fig)
