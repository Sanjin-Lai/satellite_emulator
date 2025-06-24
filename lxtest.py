import numpy as np

def test(start, end, step):
    randNum = np.linspace(start, end, step).tolist()
    print(randNum[::-1])


test(0.8450, 0.8650, 5)

x = [0.995, 0.9625, 0.9299999999999999, 0.8975, 0.865,
     0.86, 0.855, 0.85, 0.845, ]