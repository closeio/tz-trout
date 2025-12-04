#!/usr/bin/env python
"""Run this script when you upgrade dependencies.
Commit changes after the run.
"""

import sys

from generate_zipcode_data import generate_us_zipcode_data

sys.path.append(".")


if __name__ == "__main__":
    generate_us_zipcode_data()
    from tztrout import td

    td.generate_tz_name_to_tz_id_map()
    td.generate_offset_to_tz_id_map()
    td.generate_zip_to_tz_id_map()
