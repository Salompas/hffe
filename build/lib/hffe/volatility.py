import pandas as pd
import numpy as np

from .utilities import valuesAroundTime


def getSpotVolatility(series: pd.Series,
                      timestamp: pd.Timestamp,
                      window_size: int) -> (float, float):
    """Computes spot volatility for an intraday return time series.
    """
    before, after = valuesAroundTime(series, timestamp, window_size)
    assert len(before) > 0, "Empty series of returns before timestamp"
    assert len(after) > 0, "Empty series of returns after timestamp"
    delta_n = 1/len(series)
    # Spot volatility from the left
    kn_before = float(min(window_size, len(before)))
    spot_vol_before = np.sqrt((before**2).sum()/(kn_before*delta_n))
    # Spot volatility from the right
    kn_after = float(min(window_size, len(after)))
    spot_vol_after = np.sqrt((after**2).sum()/(kn_after*delta_n))
    return spot_vol_before, spot_vol_after
