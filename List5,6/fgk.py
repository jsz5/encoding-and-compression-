import math
import os
import sys


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

    def count_compress_ratio(self, initial, compressed):
        return os.stat(initial).st_size / os.stat(compressed).st_size

    def average_length(self, code, initial):
        return len(code) / os.stat(initial).st_size


class Node:
    def __init__(self, parent=None, left=None, right=None, value=0, sign=''):
        super(Node, self).__init__()
        self.parent = parent
        self.left = left
        self.right = right
        self.value = value
        self.sign = sign

    def is_leaf(self):
        return self.left is None and self.right is None


class FGK:
    def __init__(self):
        self.NYT = Node(sign="NYT")
        self.root = self.NYT
        self.nodes = []
        self.tree_nodes = dict()

    def __swap_nodes(self, node1, node2):
        i, j = self.nodes.index(node1), self.nodes.index(node2)
        self.nodes[i], self.nodes[j] = self.nodes[j], self.nodes[i]
        node1.parent, node2.parent = node2.parent, node1.parent

        if node1.parent.left is node2:
            node1.parent.left = node1
        else:
            node1.parent.right = node1

        if node2.parent.left is node1:
            node2.parent.left = node2
        else:
            node2.parent.right = node2

    def __find_largest_node(self, value):
        for n in reversed(self.nodes):
            if n.value == value:
                return n

    def __update_tree(self, node):
        while node:
            largest = self.__find_largest_node(node.value)
            if node is not largest and node is not largest.parent and largest is not node.parent:
                self.__swap_nodes(node, largest)
            node.value = node.value + 1
            node = node.parent

    def add_new_value(self, s):
        if s in self.tree_nodes:
            node = self.tree_nodes[s]
        else:
            new = Node(sign=s, value=1)
            parent = Node(self.NYT.parent, self.NYT, new, 1, "")
            new.parent = parent
            self.NYT.parent = parent
            if parent.parent:
                parent.parent.left = parent
            else:
                self.root = parent
            self.nodes.insert(0, parent)
            self.nodes.insert(0, new)
            self.tree_nodes[s] = new
            node = parent.parent
        self.__update_tree(node)


class Encode(FGK):
    def encode(self, file_name, compressed_file):
        coded = open(compressed_file, 'w+b')
        with open(file_name, "rb") as f:
            file = f.read()
            code = ""
            for sign in file:
                if sign in self.tree_nodes:
                    code += self.__get_code(sign, self.root)
                else:
                    code += self.__get_code('NYT', self.root)
                    code += bin(sign)[2:].zfill(8)
                super().add_new_value(sign)
            code = self.__add_zeros(code)
            byte_list = [int(code[i:i + 8], 2) for i in range(0, len(code), 8)]
            coded.write(bytearray(byte_list))
            coded.close()

        return code

    def __add_zeros(self, code):
        zero_count = 8 - len(code) % 8
        zero_count_info = '1' + "{0:07b}".format(zero_count)
        return zero_count_info + code + ''.join(["0"] * zero_count)

    def __get_code(self, s, node1, code=''):
        if not (node1.left or node1.right):
            return code if node1.sign == s else ""
        node2 = ""
        if node1.left:
            node2 = self.__get_code(s, node1.left, code + '0')
        if not node2 and node1.right:
            node2 = self.__get_code(s, node1.right, code + '1')
        return node2


class Decode(FGK):
    def __traverse(self, bits):
        node = self.root
        for b in bits:
            if b == '0':
                node = node.left
            else:
                node = node.right
        return node

    def decode(self, file_name, decompressed_file):
        decoded_file = open(decompressed_file, 'wb')
        with open(file_name, "rb") as f:
            byte = f.read(1)
            code = ""
            while byte != b"":
                code += repr(bin(ord(byte)))[3:-1].zfill(8)
                byte = f.read(1)

            code = self.__remove_zeros(code)
            decoded = []
            sign = self.__get_sign_code(code[:8])
            decoded.append(sign)
            super().add_new_value(sign)
            node = self.root
            i = 8
            while i < len(code):
                if node:
                    node = node.left if code[i] == '0' else node.right
                    sign = node.sign if node else None
                else:
                    sign = None

                if sign or sign == 0:
                    if sign == 'NYT':
                        sign = self.__get_sign_code(code[i + 1:i + 9])
                        i += 8
                    decoded.append(sign)
                    super().add_new_value(sign)
                    node = self.root
                i += 1
        decoded_file.write(bytes(bytearray(decoded)))
        decoded_file.close()

    def __get_sign_code(self, binary):
        return int(binary, 2)

    def __remove_zeros(self, code):
        zeros_count_info = '0' + code[1:8]
        zero_count = int(zeros_count_info, 2)
        bits = code[8:]
        return bits[:-1 * zero_count]


def bad_parameters():
    print("Błędne parametry.")


if __name__ == '__main__':
    if len(sys.argv) == 4:
        flag = sys.argv[1]
        file_name = sys.argv[2]
        if flag == "-encode":
            compressed_file = sys.argv[3]
            code = Encode().encode(file_name, compressed_file)
            data = Data(file_name)
            data.count_symbols()
            print("Entropia: ", data.count_entropy())
            print("Średnia długość kodowania: ", data.average_length(code, file_name))
            print("Stopień kompresji: ", data.count_compress_ratio(file_name, compressed_file))
        elif flag == "-decode":
            decompressed_file = sys.argv[3]
            Decode().decode(file_name, decompressed_file)
        else:
            bad_parameters()
    else:
        bad_parameters()
