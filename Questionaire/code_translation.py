

""" This file contains code that processes codes to object id's and vice versa """


class CodeTranslationError(ValueError):
    pass


class IdEncoder:
    """ This class handles all code translations """

    # DO NOT ADJUST THE FOLLOWING PARAMETERS AFTER DEPLOYMENT!
    _length = 6
    _allowed_chars = 'QZXSWDCVFRTGBYHNMJKLP'
    _steps = 2766917
    # DO NOT ADJUST THE ABOVE PARAMETERS AFTER DEPLOYMENT!

    def __init__(self, length=None, allowed_chars=None, steps=None):
        # Set parameters
        self._length = length or self._length
        self._allowed_chars = allowed_chars or self._allowed_chars
        self._steps = steps or self._steps

        # Initate some common values
        self._max_combos = (len(self._allowed_chars) ** self._length)

    @property
    def _reverser(self):
        """ Computes the value the reversed value needs to be multiplied with in order to get the original id"""
        def egcd(a, b):
            """
            Extended Euclidean Algorithm
            :param a: Int number 1
            :param b: Int number 2
            :return: the greatest common division (gcd) and the x and y values according to ax +by = gcd
            """
            x,y, u,v = 0,1, 1,0
            while a != 0:
                q, r = b//a, b%a
                m, n = x-u*q, y-v*q
                b,a, x,y, u,v = a,r, u,v, m,n
            gcd = b
            return gcd, x, y

        gcd, x, y = egcd(self._steps, self._max_combos)
        return x

    def get_code_from_id(self, id_value):
        """
        Get the lettercode for this inquiry object
        :return: Returns the lettercode for the given inquiry object
        """
        # Check if

        # New value is the key multiplied by the steps mod the total number of possibilities
        id_value = (id_value * self._steps) % self._max_combos
        string = ''

        # Translate the reformed number to its letterform
        for i in range(self._length - 1, 0 - 1, -1):
            base = len(self._allowed_chars) ** i

            # Compute the position of the character (devide by base rounded down)
            char_pos = int(id_value / base)
            # Add the new character to the string
            string += self._allowed_chars[char_pos]
            # Remove the processed value from the string
            id_value -= (base * char_pos)

        return string

    def get_id_from_code(self, code):
        """
        Retrieves the inquiry model based on a given letter-code
        :param code: The 6-letter code
        :return: The id-value
        """

        def egcd(a, b):
            """
            Extended Euclidean Algorithm
            :param a: Int number 1
            :param b: Int number 2
            :return: the greatest common division (gcd) and the x and y values according to ax +by = gcd
            """
            x,y, u,v = 0,1, 1,0
            while a != 0:
                q, r = b//a, b%a
                m, n = x-u*q, y-v*q
                b,a, x,y, u,v = a,r, u,v, m,n
            gcd = b
            return gcd, x, y

        # Define base variables
        value = 0

        # Translate the code to the reformed number
        for i in range(0, len(code)):
            char_pos = self._allowed_chars.find(code[i])

            if char_pos == -1:
                raise ValueError("Character was not the possible characters")
            else:
                value += char_pos * (len(self._allowed_chars) ** (self._length - i - 1))

        # Recompute the reformed number to its original number
        id = (value * self._reverser) % self._max_combos

        # Return the result
        return id

    def check_reverse(self, ids=None):
        """ Checks whether the forward and backward functionality return the same results """
        # Set default ids for testing
        ids = ids or [1, 22, 43, 176]

        # Check all the ids in the list
        for value in ids:
            self.check_reverse_single(value)

        return True

    def check_reverse_single(self, value=None):
        """ Check a single id value if forward and backward functionality return the same results """
        # Set a default test value
        value = value or 2801

        code = self.get_code_from_id(value)
        res_value = self.get_id_from_code(code)

        if res_value != value:
            raise CodeTranslationError("{value} yielded {res_value}, but did not reverse to {code}".format(
                value=value, res_value=res_value, code=code
            ))
        return True


# Create the encoder for a 6 letter code for inquiry objects
inquiry_6encoder = IdEncoder(length=6, allowed_chars="QZXSWDCVFRTGBYHNMJKLP", steps=2766917)
