"""Input/output module"""

from typing import Union

import re
import sys
from collections import OrderedDict
from pathlib import Path

import yaml


def load_yaml(fname: Union[str, Path]) -> dict:
    """Load configuration file with YAML format

    Parameters
    ----------
    fname : `str / Path`
        YAML filename

    Returns
    -------
    `yaml.load`
    """

    if isinstance(fname, Path):
        fname = str(fname)

    with open(fname) as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def progress_bar(
    count: int,
    total: int,
    mark_count: int = 50,
    mark_char: str = "█",
    unmarked_char: str = ".",
    left_msg: str = "",
    right_msg: str = "",
) -> None:
    """Simple progress bar

    Obtained from:
    https://www.reddit.com/r/learnpython/comments/7hyyvr/python_progress_bar_used_in_conda/

    Parameters
    ----------
    count : `int`
       Iteration number

    total: `int`
       Total number of iterations to perform

    mark_count : `int`
       Length of bar

    mark_char : `misc`
       Character used for marking completion in bar

    unmarked_char : `misc`
       Same as above but for uncompleted part of bar

    left_msg : `string`
       Message of left of progress bar

    right_msg : `string`
       Message on right side of progress bar

    """

    # if msgs are longer than 15 characters, simply remove excess
    msg_left = left_msg if len(left_msg) <= 30 else left_msg[:30]
    msg_right = right_msg if len(right_msg) <= 30 else right_msg[:30]

    bar_filled = int(round(mark_count * count / float(total)))
    percent_str = str(round(100.0 * count / float(total), 1))
    marked_progress = mark_char * (bar_filled + 1)
    unmarked_progress = unmarked_char * (mark_count - bar_filled)
    progress = marked_progress + unmarked_progress

    sys.stdout.write(f"\r{msg_left:<21} |{progress}| {percent_str:>6}% {msg_right:21}")
    sys.stdout.flush()


class NoSingleValueFoundException(Exception):
    """Class for handling exceptions"""

    pass


def parse_fortran_value_to_python(value: str = ""):
    """Try to parse a single value, if no single value is matched it raises an exception

    Parameters
    ----------
    value : `str`

    Returns
    -------
    value converted to python format
    """
    complex_re = re.compile(r"^\((\d+.?\d*),(\d+.?\d*)\)$")
    try:
        parsed_value = int(value)
    except ValueError:
        try:
            tmp = value.replace("d", "E")
            parsed_value = float(tmp)
        except ValueError:
            # check for complex number
            complex_values = re.findall(complex_re, value)
            if len(complex_values) == 1:
                a, b = complex_values[0]
                parsed_value = complex(float(a), float(b))
            elif value in [".true.", "T"]:
                # check for a boolean
                parsed_value = True
            elif value in [".false.", "F"]:
                parsed_value = False
            else:
                # see if we have an escaped string
                if value.startswith("'") and value.endswith("'") and value.count("'") == 2:
                    parsed_value = value[1:-1]
                elif value.startswith('"') and value.endswith('"') and value.count('"') == 2:
                    parsed_value = value[1:-1]
                else:
                    raise NoSingleValueFoundException(value)

    return parsed_value


def parse_python_value_to_fortran(value):
    """Recieve a python friendly value and returns it into a fortran one"""

    is_python2 = sys.version_info < (3, 0, 0)

    if isinstance(value, bool):
        return value and ".true." or ".false."

    elif isinstance(value, int):
        return f"{value:d}"

    elif isinstance(value, float):
        return (f"{value:.10e}").replace("e", "d")

    elif isinstance(value, str):
        return f"'{value}'"

    elif is_python2 and isinstance(value):  # needed if unicode literals are used
        return f"'{value}'"

    elif isinstance(value, complex):
        return "({:.5f},{:.5f})".format(
            value.real,
            value.imag,
        )

    else:
        raise Exception(f"Variable type not understood: {type(value)}")

    return value


def namelist_string_to_dict(buffer: str = "") -> dict:
    """From a string containing a fortran namelist, group elements of it into a dictionary

    Parameters
    ----------
    buffer : `str`
        String with the namelist

    Returns
    -------
    namelists : `dict`
        Ordered dictionary with namelists options. Each element of the dictionary is, in itself, another dictionary
    """

    # nothing in buffer, raise error flag
    if buffer == "":
        raise ValueError("`buffer` argument is empty")

    namelists = OrderedDict()

    # allow blocks to span multiple lines
    group_re = re.compile(r"&([^&]+)/")
    array_re = re.compile(r"(\w+)\((\d+)\)")
    string_re = re.compile(r"\'\s*\w[^']*\'")
    # complex_re = re.compile(r"^\((\d+.?\d*),(\d+.?\d*)\)$")

    # do not use lines with comments ("!")
    filtered_lines = []
    for line in buffer.split("\n"):
        if line.strip().startswith("!"):
            continue
        else:
            filtered_lines.append(line)

    group_blocks = re.findall(group_re, "\n".join(filtered_lines))
    group_cnt = dict()
    for group_block in group_blocks:
        block_lines_raw = group_block.split("\n")
        group_name = block_lines_raw.pop(0).strip()

        group = OrderedDict()
        block_lines = []
        for line in block_lines_raw:
            # cleanup string
            line = line.strip()
            if line == "":
                continue
            if line.startswith("!"):
                continue

            try:
                k, v = line.split("=")
                block_lines.append(line)
            except ValueError:
                # no = in current line, try to append to previous line
                if block_lines[-1].endswith(","):
                    block_lines[-1] += line
                else:
                    raise

        for line in block_lines:
            # commas at the end of lines seem to be optional
            if line.endswith(","):
                line = line[:-1]

            # inline comments are allowed, but we remove them for now
            if "!" in line:
                line = line.split("!")[0].strip()

            k, v = line.split("=")
            variable_name = k.strip()
            variable_value = v.strip()

            variable_name_groups = re.findall(array_re, k)

            variable_index = None
            if len(variable_name_groups) == 1:
                variable_name, variable_index = variable_name_groups[0]
                variable_index = int(variable_index) - 1  # python indexing starts at 0

            try:
                parsed_value = parse_fortran_value_to_python(value=variable_value)

                if variable_index is None:
                    group[variable_name] = parsed_value
                else:
                    if variable_name not in group:
                        group[variable_name] = {"_is_list": True}
                    group[variable_name][variable_index] = parsed_value

            except NoSingleValueFoundException:
                # see we have several values inlined
                if variable_value.count("'") in [0, 2]:
                    if variable_value.count("(") != 0:  # if list of complex values
                        variable_arr_entries = variable_value.split()
                    else:
                        # replacing ',' makes comma-separated arrays possible,
                        # see unit test test_inline_array_comma
                        # this fails if an array of complex numbers is comma-separated
                        variable_arr_entries = variable_value.replace(",", " ").split()
                else:
                    # we need to be more careful with lines with escaped
                    # strings, since they might contained spaces
                    matches = re.findall(string_re, variable_value)
                    variable_arr_entries = [s.strip() for s in matches]

                for variable_index, inline_value in enumerate(variable_arr_entries):
                    parsed_value = parse_fortran_value_to_python(value=inline_value)

                    if variable_index is None:
                        group[variable_name] = parsed_value
                    else:
                        if variable_name not in group:
                            group[variable_name] = {"_is_list": True}
                        group[variable_name][variable_index] = parsed_value

        if group_name in group.keys():

            if group_name not in group_cnt.keys():
                group_cnt[group_name] = 0
            else:
                group_cnt[group_name] += 1
            group_name = group_name + str(group_cnt[group_name])

        namelists[group_name] = group

        return namelists


def dump_dict_to_namelist_string(
    data: dict = {}, namelist: str = "", array_inline: bool = False
) -> str:
    """Dump python dictionary to a string of a fortran namelist

    Parameters
    ----------
    data : `dict`
        Dictionary to save as a namelist

    namelist : `str`
        String with the id of the namelist

    array_inline : `bool`
        Flag to store an array in a single line of the string

    Returns
    -------
    namelist_string : `str`
        String with the namelist
    """

    if namelist == "":
        raise ValueError("namelist cannot be an empty string")

    # store data into an array that will then be saved as a string
    lines = [f"&{namelist}"]

    # if there is no info in the dictionary, return the namelist string
    # either way
    if len(data) == 0:
        lines.append(f"/ ! end of {namelist} namelist")
        namelist_string = "\n".join(lines) + "\n"
        return namelist_string

    # loop over the dictionary and append to array
    for key, value in data.items():
        if isinstance(value, list):
            if array_inline:
                lines.append(
                    f"   {key} = {''.join([parse_python_value_to_fortran(value=v) for v in value])}"
                )
            else:
                for n, v in enumerate(value):
                    lines.append(f"   {key}({n+1}) = {parse_python_value_to_fortran(value=v)}")
        else:
            lines.append(f"   {key} = {parse_python_value_to_fortran(value=value)}")

    # change from array to string
    lines.append(f"/ ! end of {namelist} namelist")
    namelist_string = "\n".join(lines) + "\n"

    return namelist_string
