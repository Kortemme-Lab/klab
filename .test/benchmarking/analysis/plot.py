import random

from tools.benchmarking.analysis.plot import plot
from tools.plot.rtools import RInterface

# Create a random dataset that is skewed towards correlation
test_table = []
for x in range(1, 1001):
    exp = random.uniform(-5, 5)
    if random.random() < 0.2:
        pred = exp + random.uniform(-1, 1)
        test_table.append(dict(DatasetID = x, Experimental = exp, Predicted = pred))
    elif random.random() < 0.5:
        pred = exp + random.uniform(-2, 2)
        test_table.append(dict(DatasetID = x, Experimental = exp, Predicted = pred))
    else:
        test_table.append(dict(DatasetID = x, Experimental = exp, Predicted = random.uniform(-5, 5)))

plot(test_table, 'test.png', RInterface.correlation_coefficient_gplot)
