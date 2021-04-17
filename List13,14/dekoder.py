from sys import argv


class HammingCode:
    def __init__(self, input, output):
        self.input = input
        self.output = output
        self.codes = [
            "00000000",
            "11010010",
            "01010101",
            "10000111",
            "10011001",
            "01001011",
            "11001100",
            "00011110",
            "11100001",
            "00110011",
            "10110100",
            "01100110",
            "01111000",
            "10101010",
            "00101101",
            "11111111",
        ]
        self.errors = 0

    def get_decoded(self, bits):
        for code in self.codes:
            diffs = 0
            for first, second in zip(bits, code):
                if first != second:
                    diffs += 1
            if diffs < 2:
                return code[2] + code[4] + code[5] + code[6]
            elif diffs == 2:
                self.errors += 1
                return "0000"

        return "0000"

    def decode(self):
        with open(self.input, "rb") as f:
            file = f.read()
        decoded = ''.join(self.get_decoded("{0:08b}".format(byte)) for byte in file)
        with open(self.output, "wb") as f:
            f.write(bytes(int(decoded[i:i + 8], 2) for i in range(0, len(decoded), 8)))


if __name__ == '__main__':
    if len(argv) != 3:
        print("Błędne parametry.")
    else:
        HammingCode(argv[1], argv[2]).decode()
