#!/usr/bin/env python
"""Run this script when you upgrade pytz dependency and commit changes."""
import sys

sys.path.append('.')

from tztrout import td

if __name__ == '__main__':
    td.generate_tz_name_to_tz_id_map()
    td.generate_offset_to_tz_id_map()
