def sort_on(d):
    return d['num']

def get_num_words(text):
    return len(text.split())

def freq(text):
    d = {}
    for c in text.lower():
        d[c] = d.get(c, 0) + 1
    return d

def sorted(d):
    ls = []
    for i in d:
        ls.append({"char": i, "num": d[i]})
    ls.sort(reverse=True,key=sort_on)
    return ls