import math
from sys import argv
from collections import defaultdict


class Pixel:
    def __init__(self, red=0, green=0, blue=0):
        self.red = red
        self.green = green
        self.blue = blue

    def __add__(self, other):
        return Pixel(red=self.red + other.red, green=self.green + other.green, blue=self.blue + other.blue)

    def __sub__(self, other):
        return Pixel(red=self.red - other.red, green=self.green - other.green, blue=self.blue - other.blue)

    def __floordiv__(self, num):
        return Pixel(red=self.red // num, green=self.green // num, blue=self.blue // num)

    def __lt__(self, other):
        return (self.red + self.green + self.blue) < (other.red + other.green + other.blue)

    def __le__(self, other):
        return (self.red + self.green + self.blue) <= (other.red + other.green + other.blue)

    def __gt__(self, other):
        return (self.red + self.green + self.blue) > (other.red + other.green + other.blue)

    def __ge__(self, other):
        return (self.red + self.green + self.blue) >= (other.red + other.green + other.blue)

    def __mod__(self, modulo):
        return Pixel(
            red=self.red % modulo,
            green=self.green % modulo,
            blue=self.blue % modulo
        )


class JpegLsEncoder:
    def __init__(self, filename):
        self.width = None
        self.height = None
        self.bitmap = self.__get_bitmap(filename)
        self.predictions = [
            lambda n, w, nw: w,
            lambda n, w, nw: n,
            lambda n, w, nw: nw,
            lambda n, w, nw: n + w - nw,
            lambda n, w, nw: n + (w - nw) // 2,
            lambda n, w, nw: w + (n - nw) // 2,
            lambda n, w, nw: (n + w) // 2,
            lambda n, w, nw: max(w, n) if nw >= max(w, n) else min(w, n) if nw <= min(w, n) else w + n - nw
        ]
        self.best_all_entropy = {}
        self.best_red_entropy = {}
        self.best_green_entropy = {}
        self.best_blue_entropy = {}

    def __get_bitmap(self, filename):
        with open(filename, "rb") as f:
            image = f.read()
        self.width = image[13] * 256 + image[12]
        self.height = image[15] * 256 + image[14]
        image = image[18:]
        result = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                index = 3 * (i * self.width + j)
                row.append(Pixel(red=image[index + 2], green=image[index + 1], blue=image[index]))
            result.insert(0, row)
        return result

    def __jpeg_ls(self, prediction):
        frame_pixel = Pixel(0, 0, 0)
        encoded = []
        for i in range(self.height):
            encoded_row = []
            for j in range(self.width):
                if i == 0:
                    n = frame_pixel
                else:
                    n = self.bitmap[i - 1][j]
                if j == 0:
                    w = frame_pixel
                else:
                    w = self.bitmap[i][j - 1]

                if i == 0 or j == 0:
                    nw = frame_pixel
                else:
                    nw = self.bitmap[i - 1][j - 1]
                encoded_row.append((self.bitmap[i][j] - prediction(n, w, nw)) % 256)

            encoded.append(encoded_row)

        return encoded

    def encode(self):
        print('Image entropy:')
        self.print_entropies(self.bitmap)

        for i, schema in enumerate(self.predictions):
            print(f"Schema {i+1} entropy:")
            self.print_entropies(self.__jpeg_ls(schema), i+1)

    def print_entropies(self, bitmap, schema=None):
        all_entropy = Entropy().count_entropy(bitmap)
        red_entropy = Entropy("red").count_entropy(bitmap)
        blue_entropy = Entropy("blue").count_entropy(bitmap)
        green_entropy = Entropy("green").count_entropy(bitmap)
        if schema:
            self.best_all_entropy = self.__best_entropy(self.best_all_entropy, all_entropy, schema)
            self.best_red_entropy = self.__best_entropy(self.best_red_entropy, red_entropy, schema)
            self.best_green_entropy = self.__best_entropy(self.best_green_entropy, green_entropy, schema)
            self.best_blue_entropy = self.__best_entropy(self.best_blue_entropy, blue_entropy, schema)
        print(f"all: {all_entropy}")
        print(f"red: {red_entropy}")
        print(f"green: {green_entropy}")
        print(f"blue: {blue_entropy}")
        print()

    def __best_entropy(self, old_entropy, new_entropy, new_schema):
        if old_entropy == {} or old_entropy["entropy"] > new_entropy:
            return {"entropy": new_entropy, "schema": new_schema}
        return old_entropy

    def print_best_entropies(self):
        print(f"Best all entropy: {self.best_all_entropy['entropy']}, schema: {self.best_all_entropy['schema']}")
        print(f"Best red entropy: {self.best_red_entropy['entropy']}, schema: {self.best_red_entropy['schema']}")
        print(
            f"Best green entropy: {self.best_green_entropy['entropy']}, schema: {self.best_green_entropy['schema']}")
        print(f"Best blue entropy: {self.best_blue_entropy['entropy']}, schema: {self.best_blue_entropy['schema']}")


class Entropy:
    def __init__(self, color=None):
        self.color = color
        self.pixels_count = defaultdict(int)
        self.all_pixels = 0

    def count_entropy(self, bitmap):
        entropy = 0
        for r in bitmap:
            for pixel in r:
                if self.color:
                    value = getattr(pixel, self.color)
                    self.pixels_count[value] += 1
                    self.all_pixels += 1
                else:
                    self.pixels_count[pixel.red] += 1
                    self.pixels_count[pixel.green] += 1
                    self.pixels_count[pixel.blue] += 1
                    self.all_pixels += 3
        for s in self.pixels_count.values():
            entropy += (math.log2(s) - math.log2(self.all_pixels)) * (s / self.all_pixels)
        if entropy != 0:
            entropy *= -1
        return entropy


if __name__ == "__main__":
    filename = argv[1]
    encoder = JpegLsEncoder(filename)
    encoder.encode()
    encoder.print_best_entropies()
