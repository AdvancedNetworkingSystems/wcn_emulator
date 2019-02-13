import numpy as np
import matplotlib
import matplotlib.pyplot as plt


def errorfill(x, y, yerr, color=None, alpha_fill=0.3, ax=None, label=""):
    ax = ax if ax is not None else plt.gca()
    if color is None:
        color = ax._get_lines.color_cycle.next()
    if np.isscalar(yerr) or len(yerr) == len(y):
        ymin = y - yerr
        ymax = y + yerr
    elif len(yerr) == 2:
        ymin, ymax = yerr
    ax.plot(x, y, color=color, label=label)
    ax.fill_between(x, ymax, ymin, color=color, alpha=alpha_fill)

data = np.load("temp.dat.npy")

data=np.reshape(data, (1, 6, 20))
print data
# np
# data.sort()
# 
# fig, ax = plt.subplots()
# colors = ["red", "green", "blue"]
# labels = ["NOPOP", "POP", "POPPEN"]
# for i in range(3):
#     errorfill(range(20), data[0, i, :], yerr=data[1, i, :], ax=ax, color=colors[i], label=labels[i])
# 
# plt.yscale("log")
# ax.legend()
# ax.set(xlabel='node id', ylabel='L',
#        title='Comparison of strategies')
# ax.grid()
# 
# #fig.savefig("test.png")
# plt.show()
