#!/usr/bin/env python
import sys

sys.path.append('.')

from tztrout import td

if __name__ == '__main__':
    td.generate_tz_name_to_tz_id_map()
