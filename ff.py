dict = {"a":(3,1),"b":(3,2)}
lst = sorted(dict.items(), key=lambda tup: tup[1][1], reverse=True)
print(lst)


