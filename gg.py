



dictD = {"a": (2,2), "b": (3, 1)}
lst = list(map(lambda tup: (tup[0], tup[1][1]), dictD.items()))

print(lst)
