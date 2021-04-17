from sys import argv


class HammingCode:
    def __init__(self, input, output):
        self.bits = self.__get_bits(input)
        self.output = output

    def __get_bits(self, input):
        with open(input, "rb") as f:
            data = f.read()
        return ''.join("{0:08b}".format(byte) for byte in data)

    def parity(self, bits, p):
        return str(len([1 for i in p if bits[i] == "1"]) % 2)

    def encode(self):
        result = []
        with open(self.output, "wb") as f:
            for i in range(0, len(self.bits), 4):
                data = self.bits[i:i + 4]
                p1 = self.parity(data, [0, 1, 3])
                p2 = self.parity(data, [0, 2, 3])
                p3 = self.parity(data, [1, 2, 3])
                p = self.parity(p1 + p2 + data[0] + p3 + data[1:], range(7))
                hamming = p1 + p2 + data[0] + p3 + data[1:] + p
                result.append(int(hamming, 2))
            with open(self.output, "wb") as f:
                f.write(bytes(r for r in result))


if __name__ == '__main__':
    if len(argv) != 3:
        print("Błędne parametry.")
    else:
        HammingCode(argv[1], argv[2]).encode()
