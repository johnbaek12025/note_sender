def list_chunk(lst, n):
    li = []
    for i in range(0, len(lst), n):
        if i == len(lst) - n - 1:
            li.append(lst[i:])
            break
        else:
            li.append(lst[i:i+n])
    return li