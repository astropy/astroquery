from collections import OrderedDict


dtype_dict = {'f': 'f', 's': 's', 'd': 'i', 'e': 'f', 'F': 'f', 'A': 's',
              'I': 'i'}
fmt_dict = {'f': float, 's': str, 'd': int, 'e': float, 'A': str, 'I': int,
            'F': float}


def parse_readme(filename, *, group_global=None, group_local=None):
    with open(filename, 'r') as f:
        lines = f.readlines()

    formats = OrderedDict()

    if group_local is not None and group_local is not None:
        qfl, qfg = quanta_formatter(group_local=group_local,
                                    group_global=group_global)
        use_qf = True
    else:
        use_qf = False

    for ii, line in enumerate(lines):
        if line[0] == '-':
            row_name = lines[ii-1].strip()
        if 'C-style format specifier:' in line:
            fmt = line[len('C-style format specifier:'):].strip()
            if '.' in fmt:
                length = int(fmt[1:fmt.find('.')])
            else:
                length = int(fmt[1:-1])
            dtype = dtype_dict[fmt[-1]] if fmt[-1] != 's' else 'S'+fmt[1:-1]

            if 'quanta' in row_name and use_qf:
                g = ('global' in row_name)
                ul = 'u' if 'upper' in row_name else 'l'
                # gl = 'g' if g else 'l'
                qf = qfg if g else qfl

                assert sum([x['length'] for x in qf.values()]) == length

                for rn in qf:
                    formats[rn+"_"+ul] = qf[rn]
            else:
                formats[row_name] = {'format_str': fmt,
                                     'length': length,
                                     'dtype': dtype,
                                     'formatter': fmt_dict[fmt[-1]]}

    assert sum([x['length'] for x in formats.values()]) == 160
    return formats


def quanta_formatter(*, group_global='class1', group_local='group1'):
    """
    Format based on the global/local formatters from the HITRAN04 paper
    """

    local_dict = {'group1':  # asymmetric
                  OrderedDict([('J', 'I3'),
                               ('Ka', 'I3'),
                               ('Kc', 'I3'),
                               ('F', 'A5'),
                               ('Sym', 'A1'),
                               ]
                              ),
                  'hc3n':  # special
                  OrderedDict([('J', 'I3'),
                               ('Ka', 'I3'),
                               ('Kc', 'I3'),
                               ('F', 'A5'),
                               ('Sym', 'A1'),
                               ]
                              ),
                  }

    global_dict = {'class9':  # non-linear tetratomic
                   OrderedDict([('v1', 'I5'),  # preceded by 3x space
                                ('v2', 'I2'),
                                ('v3', 'I2'),
                                ('v4', 'I2'),
                                ('v5', 'I2'),
                                ('v6', 'I2'),
                                ]
                               ),
                   'class10':
                   OrderedDict([('v1', 'I5'),  # preceded by 3x space
                                ('v2', 'I2'),
                                ('v3', 'I2'),
                                ('v4', 'I2'),
                                ('n', 'A2'),
                                ('C', 'A2'),
                                ]
                               ),
                   'hc3n':
                   OrderedDict([('v1', 'I3'),  # preceded by 2x space
                                ('v2', 'I1'),
                                ('v3', 'I1'),
                                ('v4', 'I1'),
                                ('v5', 'I1'),
                                ('v6', 'I1'),
                                ('v7', 'I1'),
                                ('l5', 'I2'),
                                ('l6', 'I2'),
                                ('l7', 'I2'),
                                ]
                               ),
                   }

    loc = OrderedDict()
    for key, value in local_dict[group_local].items():
        loc[key] = {'format_str': value, 'length': int(value[1:]),
                    'dtype': 'S'+value[1:] if dtype_dict[value[0]] == 's' else
                    dtype_dict[value[0]],
                    'formatter': fmt_dict[value[0]]}

    glob = OrderedDict()
    for key, value in global_dict[group_global].items():
        glob[key] = {'format_str': value, 'length': int(value[1:]),
                     'dtype': 'S'+value[1:] if dtype_dict[value[0]] == 's' else
                     dtype_dict[value[0]],
                     'formatter': fmt_dict[value[0]]}

    return loc, glob
