import string


def _find_origin(char):
    sources = [string.digits, string.ascii_uppercase, string.ascii_lowercase]

    for ascii_source in sources:
        index = ascii_source.find(char)
        if index != -1:
            return index, ascii_source


def shift_value(input_string, amount):
    outcome = ''

    for i in range(len(input_string)):
        cur_char = input_string[len(input_string) - i - 1]
        if amount == 0:
            # There is no need to compute that which will not change
            outcome = cur_char + outcome
            continue

        # Get the index of in the supercall e.g. 3 when ***c
        index, ascii_source = _find_origin(cur_char)

        # Compute the new location and the new value in the new range
        new_index = index + amount
        new_local_index = new_index % len(ascii_source)
        new_amount = new_index - new_index % len(ascii_source)

        # Create the new value at position i (e.g. **G*)
        outcome = ascii_source[int(new_local_index)] + outcome

        # Lower the shift value to correspond with the next tier (note that it uses int rounding)
        amount = new_amount / len(ascii_source)

    return outcome


def _select_from_ascii_sources(ascii_sources, index):
    result = ''
    for source in ascii_sources:
        result += source[index]
    return result


def get_lowest_value(ascii_sources):
    """ Returns the lowest possible value with the listed combination of ascii sources
    e.g. digits lowercase uppercase would yield 0aA
    """
    return _select_from_ascii_sources(ascii_sources, 0)


def get_highest_value(ascii_sources):
    """ Returns the highest possible value with the listed combination of ascii sources
    e.g. digits lowercase uppercase would yield 9zZ
    """
    return _select_from_ascii_sources(ascii_sources, -1)


def get_range_list(min_string, max_string, append='', output=None, ascii_sources=None):
    """ Returns a list with every intermediate value including the values itself.
    Takes into account the ascii source for each part e.g. 2049ZY - 2050BW will present all values in between.
    """
    output = output or []

    # It is the final depth loop. Return the full values
    if len(min_string) == 1:
        index, ascii_source = _find_origin(min_string)
        for i in range(index, len(ascii_source)):
            local_output = ascii_source[i]
            output.append(append+local_output)

            if local_output == max_string:
                return output
        return output

    # Determine all ascii sources, used when needing to go full ranges
    if ascii_sources is None:
        ascii_sources = []
        for i in range(len(min_string)):
            index, ascii_range = _find_origin(min_string[i])
            ascii_sources.append(ascii_range)

    # Set some common attributes
    current_char = min_string[0]
    pos_sub_min = get_lowest_value(ascii_sources[1:])
    pos_sub_max = get_highest_value(ascii_sources[1:])
    min_local = min_string[1:]
    max_local = pos_sub_max

    while True:
        if current_char == max_string[0]:
            max_local = max_string[1:]

        output += get_range_list(
            min_local,
            max_local,
            append=append+current_char,
            ascii_sources=ascii_sources[1:]
        )

        if current_char == max_string[0]:
            break
        else:
            # Set the minimum to the lowest possible value (as it will now loop e.g. 34-39 40-...)
            min_local = pos_sub_min
            # Increase the current character by 1 step and loop again
            current_char = shift_value(current_char, 1)

    return output


def get_range(input_string, range_value, min_value=None, max_value=None):
    min_string = shift_value(str(input_string), -range_value)
    if min_value:
        min_string = max(min_string, min_value)
    max_string = shift_value(str(input_string), range_value)
    if max_value:
        max_string = min(max_string, max_value)

    return get_range_list(min_string, max_string)