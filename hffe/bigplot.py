import matplotlib.pyplot as plt


class BigPlot:
    def __init__(self, create, update, filepath):
        self.filepath = filepath
        self.create = create
        self.update = update
        self.fig, self.ax = self.create()
        self.save()

    def __call__(self, data, save=True):
        self.update(self.ax, data)
        if save:
            self.save()

    def save(self):
        self.fig.savefig(self.filepath, dpi=200)

    def close(self):
        plt.close(self.fig)
