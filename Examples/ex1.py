import os

data = OptionsFromCSV(os.path.join("Data", "20070108.csv"), 405)
for option in data:
    # Validate data
    # Filter data
    # Split by minute
