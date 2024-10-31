##
##

import random


class FastRandom(object):

    def __init__(self, x=256, start=1):
        self.max_value = x
        self.bits = self.max_value.bit_length()
        self.start_value = start

    @property
    def value(self):
        ceiling = self.max_value - 1
        rand_number = random.getrandbits(self.bits) % ceiling
        return rand_number + 1
