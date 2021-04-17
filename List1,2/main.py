import math


def count_symbols():
    symbols = dict()
    cond_symbols = dict()
    file_size = 0
    with open(file_name, "rb") as f:
        file = f.read()
        for index, value in enumerate(file):
            symbols[value] = symbols.get(value, 0) + 1
            file_size += 1
            if index == 0:
                cond_symbols[(value, 0)] = cond_symbols.get((value, 0), 0) + 1
            else:
                cond_symbols[(value, file[index - 1])] = cond_symbols.get((value, file[index - 1]), 0) + 1
    return symbols, cond_symbols, file_size


def count_entropy():
    entropy = 0
    for s in symbols.values():
        entropy += (math.log2(s) - math.log2(file_size)) * (s / file_size)
    if entropy != 0:
        entropy *= -1
    return entropy


def count_cond_entropy():
    cond_entropy = 0
    for s_key, s_value in symbols.items():
        cond_sum = 0
        for key, value in cond_symbols.items():
            if key[1] == s_key:
                cond_sum += (math.log2(value) - math.log2(s_value)) * (value / s_value)
        cond_entropy += cond_sum * (s_value / file_size)
    if cond_entropy != 0:
        cond_entropy *= -1
    return cond_entropy


if __name__ == "__main__":
    file_name = "testy.zip"
    (symbols, cond_symbols, file_size) = count_symbols()
    print("Entropy: ", count_entropy())
    print("Conditional entropy: ", count_cond_entropy())
