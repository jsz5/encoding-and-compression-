import math
import os
import sys
from struct import pack, unpack


class Data:
    def __init__(self, file_name):
        self.file_name = file_name
        self.symbols_count = dict()
        self.all_symbols = 0

    def count_symbols(self):
        with open(self.file_name, "rb") as f:
            file = f.read()
            for index, value in enumerate(file):
                self.symbols_count[value] = self.symbols_count.get(value, 0) + 1
        self.all_symbols = os.stat(self.file_name).st_size

    def count_entropy(self):
        entropy = 0
        for s in self.symbols_count.values():
            entropy += (math.log2(s) - math.log2(self.all_symbols)) * (s / self.all_symbols)
        if entropy != 0:
            entropy *= -1
        return entropy


class Coding:
    def __init__(self, alphabet_size, save_file):
        self.symbols = dict()
        self.alphabet = dict()
        self.alphabet_size = alphabet_size
        self.__init_symbols()
        self.code_length = 0
        self.save_file = save_file

    def __init_symbols(self):
        for i in range(self.alphabet_size):
            self.symbols[str(i)] = i
            self.alphabet[i] = str(i)

    def encode(self, file_name):
        coded = open(self.save_file, 'wb')
        i = self.alphabet_size
        with open(file_name, "rb") as f:
            file = f.read()
            c = str(file[0])
            for index, value in enumerate(file[1:]):
                s = str(value)
                concat = self.__concat(c, s)
                if concat in self.symbols:
                    c = concat
                else:
                    coded.write(pack('<I', self.symbols[c]))
                    self.code_length += 1
                    self.symbols[concat] = i
                    i += 1
                    c = s
            coded.write(pack('<I', self.symbols[c]))
            self.code_length += 1
        coded.close()

    def decode(self, file_name):
        decoded = open(self.save_file, 'w+b')
        i = self.alphabet_size
        file = []
        with open(file_name, "rb") as f:
            data = f.read(4)
            while len(data) == 4:
                (unpacked_data,) = unpack('<I', data)
                file.append(unpacked_data)
                data = f.read(4)


            pk = int(file[0])
            for code in file[1:]:
                code = int(code)
                pc = self.alphabet[pk]
                if code in self.alphabet:
                    first_symbol = self.alphabet[code].split(" ")[0]
                else:
                    first_symbol = pc.split(" ")[0]
                self.alphabet[i] = self.__concat(pc, first_symbol)
                i += 1
                pk = int(code)
        result = []
        for code in file:
            self.__print_decoded(self.alphabet[int(code)], result)
        decoded.write(bytes(bytearray(result)))
        decoded.close()

    def __concat(self, c, s):
        return c + " " + s

    def __print_decoded(self, c, result):
        codes = c.split(" ")
        for code in codes:
            result.append(int(code))


def bad_parameters():
    print("Błędne parametry.")


if __name__ == "__main__":
    if len(sys.argv) == 4:
        flag = sys.argv[1]
        file_name = sys.argv[2]
        if flag == "-encode":
            compressed_file = sys.argv[3]
            data_to_code = Data(file_name)
            data_to_code.count_symbols()
            print("Entropia kodowanego tekstu: ", data_to_code.count_entropy())
            print("Długość kodowanego tekstu: ", data_to_code.all_symbols)
            coding = Coding(512, compressed_file)
            coding.encode(file_name)
            coded_data = Data(compressed_file)
            coded_data.count_symbols()
            print("Entropia kodu: ", coded_data.count_entropy())
            print("Długość kodu: ", os.stat(compressed_file).st_size)
            print("Stopień kompresji: ", (os.stat(file_name).st_size/os.stat(compressed_file).st_size))
        elif flag == "-decode":
            decompressed_file = sys.argv[3]
            coding = Coding(512, decompressed_file)
            coding.decode(file_name)
        else:
            bad_parameters()
    else:
        bad_parameters()
