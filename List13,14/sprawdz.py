from sys import argv


def from_file(filename):
    with open(filename, "rb") as f:
        file = f.read()
    return ''.join("{0:08b}".format(byte) for byte in file)


if __name__ == '__main__':
    if len(argv) != 3:
        print("Błędne parametry.")
    else:
        bits1 = from_file(argv[1])
        bits2 = from_file(argv[2])
        if len(bits1) != len(bits2):
            print("Pliki mają różną wielkość.")
            exit(0)

        bits_length = min(len(bits1), len(bits2))

        different_blocks = 0
        for i in range(0, bits_length, 4):
            if bits1[i:i + 4] != bits2[i:i + 4]:
                different_blocks += 1

        print(f"Liczba różnych bloków: {different_blocks}")
