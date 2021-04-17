import copy
import math
from sys import argv


class Pixel:
    def __init__(self, red=0, green=0, blue=0):
        self.red = red
        self.green = green
        self.blue = blue
        self.previous = None
        self.error = None

    def __repr__(self):
        return f"R {self.red},G {self.green},B {self.blue}"

    def __add__(self, other):
        return Pixel(red=self.red + other.red, green=self.green + other.green, blue=self.blue + other.blue)

    def __mul__(self, num):
        return Pixel(red=self.red * num, green=self.green * num, blue=self.blue * num)

    def __sub__(self, other):
        return Pixel(red=self.red - other.red, green=self.green - other.green, blue=self.blue - other.blue)

    def __floordiv__(self, num):
        return Pixel(red=self.red // num, green=self.green // num, blue=self.blue // num)

    def __truediv__(self, num):
        return Pixel(red=self.red / num, green=self.green / num, blue=self.blue / num)

    def __lt__(self, other):
        return (self.red + self.green + self.blue) < (other.red + other.green + other.blue)

    def __le__(self, other):
        return (self.red + self.green + self.blue) <= (other.red + other.green + other.blue)

    def __gt__(self, other):
        return (self.red + self.green + self.blue) > (other.red + other.green + other.blue)

    def __ge__(self, other):
        return (self.red + self.green + self.blue) >= (other.red + other.green + other.blue)

    def __pow__(self, num):
        return Pixel(red=self.red ** num, green=self.green ** num, blue=self.blue ** num)

    def quantized(self, delta):
        return Pixel(self.__quantized_value(self.red, delta), self.__quantized_value(self.green, delta),
                     self.__quantized_value(self.blue, delta))

    def __quantized_value(self, old_value, delta):
        value = abs(old_value)
        quantized = int(math.floor(value / delta) * delta + (delta / 2))
        if old_value < 0:
            quantized *= -1
        return quantized

    def fix_pixel_value(self):
        if self.red < 0:
            self.red = 0
        if self.red > 255:
            self.red = 255
        if self.green < 0:
            self.green = 0
        if self.green > 255:
            self.green = 255
        if self.blue < 0:
            self.blue = 0
        if self.blue > 255:
            self.blue = 255


class Encode:
    def __init__(self, filename, k):
        self.width = None
        self.height = None
        self.original = None
        self.delta = self.__delta(k)
        self.bitmap = self.__get_bitmap(filename)
        self.original_bitmap = copy.deepcopy(self.bitmap)
        self.encoded = self.bitmap
        self.decoded = None
        self.mse = {}
        self.snr = {}
        self.partition = {
            "red": k,
            "green": k,
            "blue": k
        }

    def __get_bitmap(self, filename):
        with open(filename, "rb") as f:
            image = f.read()

        self.width = image[13] * 256 + image[12]
        self.height = image[15] * 256 + image[14]
        self.original = list(image)
        image = image[18:]
        result = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                index = 3 * (i * self.width + j)
                pixel = Pixel(red=image[index + 2], green=image[index + 1], blue=image[index])

                row.append(pixel)
            result.insert(0, row)
        return result

    def __delta(self, bits):
        return 256 / 2 ** bits

    def image_to_file(self, image, output):

        file = open(output, 'wb')
        shift = 18

        for i in range(self.height):
            for j in range(self.width):
                index = 3 * ((self.height - 1 - i) * self.width + j) + shift
                image[i][j].fix_pixel_value()
                self.original[index + 2] = int(image[i][j].red)
                self.original[index + 1] = int(image[i][j].green)
                self.original[index] = int(image[i][j].blue)
        file.write(bytes(self.original))

    def quantize(self):
        error = Pixel(0, 0, 0)
        tmp = Pixel(128, 128, 128)
        previous = Pixel(0, 0, 0)

        for i, row in enumerate(self.bitmap):
            for j, pixel in enumerate(row):
                current = self.bitmap[i][j]
                differential = current - previous - error
                quantized = differential.quantized(self.delta)
                self.encoded[i][j] = (quantized // 2) + tmp
                error = quantized - differential
                previous = current
        return self.encoded

    def check_pixel_range(self, pixel, previous):
        if pixel.red < 0:
            pixel.red = 0
            previous.red = 0
        if pixel.red > 255:
            pixel.red = 255
            previous.red = 255
        if pixel.green < 0:
            pixel.green = 0
            previous.green = 0
        if pixel.green > 255:
            pixel.green = 255
            previous.green = 255
        if pixel.blue < 0:
            pixel.blue = 0
            previous.blue = 0
        if pixel.blue > 255:
            pixel.blue = 255
            previous.blue = 255
        return pixel, previous

    def decode(self, output,decoded_file):
        previous = Pixel(0, 0, 0)
        tmp = Pixel(128, 128, 128)
        image = self.__get_bitmap(output)
        self.decoded = copy.deepcopy(image)
        for i in range(self.height):
            for j in range(self.width):
                self.decoded[i][j] = (image[i][j] - tmp) * 2 + previous
                previous = self.decoded[i][j]
                self.decoded[i][j], previous = self.check_pixel_range(self.decoded[i][j], previous)
        self.image_to_file(self.decoded,decoded_file)

    def __mse_difference(self, i, j):
        return (self.original_bitmap[i][j] - self.decoded[i][j]) ** 2

    def __snr_sum(self, i, j):
        return self.original_bitmap[i][j] ** 2

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
                mse = self.__mse_difference(i, j)
                red_mse += mse.red
                green_mse += mse.green
                blue_mse += mse.blue

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
                snr = self.__snr_sum(i, j)
                sum_red += snr.red
                sum_green += snr.green
                sum_blue += snr.blue
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


if __name__ == "__main__":
    filename = argv[1]
    output = argv[2]
    decoded_file = argv[3]
    k = int(argv[4])
    quantization = Encode(filename, k)
    encoded = quantization.quantize()
    quantization.image_to_file(encoded, output)
    quantization.decode(output,decoded_file)
    quantization.count_mse()
    quantization.count_snr()
    quantization.print_errors()
