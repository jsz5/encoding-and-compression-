from sys import argv
import random

if __name__ == '__main__':

    if len(argv) != 4:
        print("Błędne parametry.")
    else:
        probability = float(argv[1])
        input = argv[2]
        output = argv[3]
        with open(input, "rb") as f:
            file = f.read()
        bits = ''.join("{0:08b}".format(byte) for byte in file)
        bits_with_noise = ''.join(str(int(not int(bit)))
                                  if random.random() <= probability else bit for bit in bits)

        with open(output, "wb") as f:
            f.write(bytes(int(bits_with_noise[i:i + 8], 2) for i in range(0, len(bits_with_noise), 8)))
