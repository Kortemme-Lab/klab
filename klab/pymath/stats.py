import math

def get_mean_and_standard_deviation(values):
    # todo: this should be replaced with calls to numpy
    sum = 0
    n = len(values)

    for v in values:
        sum += v

    mean = sum / n
    sumsqdiff = 0

    for v in values:
        t = (v - mean)
        sumsqdiff += t * t

    variance = sumsqdiff / n
    stddev = math.sqrt(variance)

    return mean, stddev, variance
