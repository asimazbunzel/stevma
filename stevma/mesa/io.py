"""Utility functions and classes to handle MESA input files"""

from collections import OrderedDict
from pathlib import Path
import re
import sys
from typing import Union

import yaml


class NoSingleValueFoundException(Exception):
    """Class for handling exceptions"""

    pass


def load_yaml(fname: Union[str, Path]):
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

    with open(fname, "r") as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def parse_fortran_value_to_python(value):
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
                if (
                    value.startswith("'")
                    and value.endswith("'")
                    and value.count("'") == 2
                ):
                    parsed_value = value[1:-1]
                elif (
                    value.startswith('"')
                    and value.endswith('"')
                    and value.count('"') == 2
                ):
                    parsed_value = value[1:-1]
                else:
                    raise NoSingleValueFoundException(value)

    return parsed_value


def namelist_string_to_dict(buffer: str = ""):
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
    complex_re = re.compile(r"^\((\d+.?\d*),(\d+.?\d*)\)$")

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

        if group_name in self.groups.keys():

            if group_name not in group_cnt.keys():
                group_cnt[group_name] = 0
            else:
                group_cnt[group_name] += 1
            group_name = group_name + str(group_cnt[group_name])

        namelists[group_name] = group

        return namelists
