import copy
import math
from sys import argv


class Quantization:
    def __init__(self, filename, red, green, blue):
        self.width = None
        self.height = None
        self.image, self.width, self.height = self.__get_image(filename)
        self.original = copy.deepcopy(self.image)
        self.red = self.__delta(red)
        self.green = self.__delta(green)
        self.blue = self.__delta(blue)
        self.shift = 18
        self.mse = {}
        self.snr = {}
        self.partition = {
            "red": red,
            "green": green,
            "blue": blue
        }

    def __get_image(self, filename):
        with open(filename, "rb") as f:
            file = f.read()
        return list(file), file[13] * 256 + file[12], file[15] * 256 + file[14]

    def __delta(self, bits):
        return 256 / 2 ** bits

    def image_to_file(self, output):
        file = open(output, 'wb')
        file.write(bytes(self.image))

    def quantize(self):
        for i in range(self.height):
            for j in range(self.width):
                index = 3 * (i * self.width + j)
                self.image[self.shift + index + 2] = self.__quantized_value(self.image[self.shift + index + 2],
                                                                            self.red)
                self.image[self.shift + index + 1] = self.__quantized_value(self.image[self.shift + index + 1],
                                                                            self.green)
                self.image[self.shift + index] = self.__quantized_value(self.image[self.shift + index], self.blue)

    def __quantized_value(self, old_value, delta):
        return int(math.floor(old_value / delta) * delta + (delta / 2))

    def __mse_difference(self, i):
        return (self.original[i] - self.image[i]) ** 2

    def __snr_sum(self, i):
        return self.original[i] ** 2

    def __snr_to_db(self, snr):
        if snr == 0:
            return 0
        return 10 * math.log10(snr)

    def count_mse(self):
        red_mse = 0
        green_mse = 0
        blue_mse = 0
        for i in range(self.height):
            for j in range(self.width):
                index = 3 * (i * self.width + j)
                red_mse += self.__mse_difference(self.shift + index + 2)
                green_mse += self.__mse_difference(self.shift + index + 1)
                blue_mse += self.__mse_difference(self.shift + index)

        mult = 1 / (self.height * self.width)
        all_mse = mult * (red_mse + green_mse + blue_mse) / 3
        red_mse *= mult
        green_mse *= mult
        blue_mse *= mult

        self.mse = {
            "all": all_mse,
            "red": red_mse,
            "green": green_mse,
            "blue": blue_mse
        }

    def count_snr(self):
        sum_red = 0
        sum_green = 0
        sum_blue = 0
        for i in range(self.height):
            for j in range(self.width):
                index = 3 * (i * self.width + j)
                sum_red += self.__snr_sum(self.shift + index + 2)
                sum_green += self.__snr_sum(self.shift + index + 1)
                sum_blue += self.__snr_sum(self.shift + index)
        mult = 1 / (self.height * self.width)
        red_snr = (sum_red * mult / self.mse["red"] if self.mse["red"] != 0 else math.inf)
        green_snr = (sum_green * mult / self.mse["green"] if self.mse["green"] != 0 else math.inf)
        blue_snr = (sum_blue * mult / self.mse["blue"] if self.mse["blue"] != 0 else math.inf)
        all_snr = ((sum_red + sum_green + sum_blue) / 3 * mult / self.mse["all"] if self.mse["all"] != 0 else math.inf)
        self.snr = {
            "all": all_snr,
            "red": red_snr,
            "green": green_snr,
            "blue": blue_snr
        }

    def print_errors(self):
        print(f"mse = {self.mse['all']}")
        print(f"mse(r) = {self.mse['red']}")
        print(f"mse(g) = {self.mse['green']}")
        print(f"mse(b) = {self.mse['blue']}")
        print(f"SNR = {self.snr['all']} ({self.__snr_to_db(self.snr['all'])} dB)")
        print(f"SNR(r) = {self.snr['red']} ({self.__snr_to_db(self.snr['red'])} dB)")
        print(f"SNR(g) = {self.snr['green']} ({self.__snr_to_db(self.snr['green'])} dB)")
        print(f"SNR(b) = {self.snr['blue']} ({self.__snr_to_db(self.snr['blue'])} dB)")
        print(f"Partition: {self.partition}")


def partition(filename, output, bits, criterion):
    best_solution = None
    for i in range(9):
        for j in range(9):
            for k in range(9):
                if i + j + k == bits:
                    quantization = Quantization(filename, i, j, k)
                    quantization.quantize()
                    quantization.count_mse()
                    if criterion == "MSE":
                        if not best_solution or best_solution.mse["all"] > quantization.mse["all"]:
                            best_solution = quantization
                    else:
                        quantization.count_snr()
                        if not best_solution or best_solution.snr["all"] < quantization.snr["all"]:
                            best_solution = quantization
    if criterion == "MSE":
        best_solution.count_snr()
    best_solution.print_errors()
    best_solution.image_to_file(output)


if __name__ == "__main__":
    filename = argv[1]
    output = argv[2]
    bits = int(argv[3])
    criterion = argv[4]
    if criterion not in ["MSE", "SNR"] or bits < 0 or bits > 24:
        print("Błędne parametry.")
    else:
        partition(filename, output, bits, criterion)
