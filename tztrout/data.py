import datetime
import json
import os
from collections import defaultdict, namedtuple
from sys import stdout

import pytz

from tztrout.data_exceptions import data_exceptions

# paths to the data files
basepath = os.path.dirname(os.path.abspath(__file__))
US_ZIPS_TO_TZ_IDS_MAP_PATH = os.path.join(
    basepath, "data/us_zips_to_tz_ids.json"
)
TZ_NAME_TO_TZ_IDS_MAP_PATH = os.path.join(
    basepath, "data/tz_name_to_tz_ids.json"
)
OFFSET_TO_TZ_IDS_MAP_PATH = os.path.join(
    basepath, "data/offset_to_tz_ids.json"
)
STATES_PATH = os.path.join(basepath, "data/normalized_states.json")
ALIASES_PATH = os.path.join(basepath, "data/tz_name_to_tz_name_aliases.json")
CA_STATE_TO_TZ_IDS_MAP_PATH = os.path.join(
    basepath, "data/ca_state_to_tz_ids.json"
)
CA_AREA_CODE_TO_STATE_MAP_PATH = os.path.join(
    basepath, "data/ca_area_code_to_state.json"
)
AU_STATE_TO_TZ_IDS_MAP_PATH = os.path.join(
    basepath, "data/au_state_to_tz_ids.json"
)
AU_AREA_CODE_TO_STATE_MAP_PATH = os.path.join(
    basepath, "data/au_area_code_to_state.json"
)

# Australian TZ names are resolved as EST, WST, etc., which is ok for local
# usage, but conflicts with the more common US TZ names if we're thinking
# globally. We should use AWST, ACST, AEST, etc. instead.
AU_MAP = {
    "WST": "AWST",
    "CST": "ACST",
    "EST": "AEST",
    "CWST": "AWST",
    "LHST": "AEST",
    "WDT": "AWDT",
    "CDT": "ACDT",
    "EDT": "AEDT",
    "CWDT": "AWDT",
    "LHDT": "AEDT",
}

# Asia/Manila is resolved as PST (Philippine Standard Time), which is ok for
# local usage, but conflicts with the more common US PST (Pacific Standard
# Time). We use PHT instead.
ASIA_MAP = {
    "PST": "PHT",
}

# Deprecated timezone IDs that are still commonly used and should be included
# in the timezone name mapping (these are in pytz.all_timezones but not in
# pytz.common_timezones)
DEPRECATED_TIMEZONES_WHITELIST = [
    "Asia/Calcutta",  # Now Asia/Kolkata (India)
    "Asia/Istanbul",  # Now Europe/Istanbul (Turkey)
    "America/Montreal",  # Now America/Toronto (Canada)
]

# The path of our US Zipcode data generated from Geonames.org
US_ZIPCODE_DATA_PATH = os.path.join(basepath, "data/us_zipcode_data.json")

# The namedtuple structure that represents a US Zipcode
Zipcode = namedtuple(
    "Zipcode", ["zip", "city", "state", "latitude", "longitude"]
)


def deduplicator():
    """
    Deduplicate strings in memory using a canonical mapping.

    Works similarly to intern() but supports unicode as well.

    >>> a = chr(1) + chr(1)  # Create two strings
    >>> b = chr(1) + chr(1)

    >>> a == b  # These have the same contents
    True
    >>> id(a) == id(b)  # But they're different objects
    False

    >>> deduplicate = deduplicator()  # Deduplicating them returns the same object
    >>> id(deduplicate(a)) == id(deduplicate(b))
    True
    """
    memo = {}

    def deduplicate(item):
        if item in memo:
            return memo[item]
        memo[item] = item
        return item

    return deduplicate


def generate_us_zipcode_namedtuples():
    """
    Generate a list of namedtuples for US zipcodes from the list of
    dictionaries in data/us_zipcode_data.json
    """
    if not os.path.exists(US_ZIPCODE_DATA_PATH):
        raise ValueError(
            "US Zipcode data missing. Run regenerate_data.py first"
        )
    with open(US_ZIPCODE_DATA_PATH) as file:
        data = json.load(file)
    for zip in data:
        yield Zipcode(**zip)


class InMemoryZipData:
    """
    In-memory copy of Zipcode mappings by state, city, and state and city.

    This enables 20x speedup for city/state zip code lookup
    at a cost of more restricted / use-case-specific API,
    extra startup time of about 0.25-0.5s (depending on CPU),
    and holding the dataset in process memory (4-8MB).
    """

    def __init__(self):
        self.by_state = {}
        self.by_city = {}
        self.by_state_city = {}
        deduplicate = deduplicator()

        for zip in generate_us_zipcode_namedtuples():
            code = deduplicate(zip.zip)
            state = deduplicate(zip.state)
            city = deduplicate(zip.city)
            if state not in self.by_state:
                self.by_state[state] = code
            if city not in self.by_city:
                self.by_city[city] = code
            if (state, city) not in self.by_state_city:
                self.by_state_city[(state, city)] = code

    def find_zip(self, city=None, state=None):
        if city and state:
            return self.by_state_city.get((state, city))
        elif city:
            return self.by_city.get(city)
        elif state:
            return self.by_state.get(state)

        raise ValueError("Specify either city or state")


ZIP_DATA = InMemoryZipData()


class TroutData:
    """Helper class that generates the JSON data used by TZTrout"""

    # We don't care about the historic data - we just want to know the recent
    # state of time zones, zip codes, etc. RECENT_YEARS_START describes how
    # far back we should go to check for DST changes, timezone names, etc.
    RECENT_YEARS_START = 2005

    # Sometimes we need to go back a few steps to figure out DSTs, timezone
    # names, etc. This is a kwargs dict that is passed to datetime.timedelta
    # to determine the size of a single step
    TD_STEP = {"days": 40}

    def __init__(self):
        # load the data files, if they exist
        self.us_zip_to_tz_ids = self._load_us_zipcode_data(
            US_ZIPS_TO_TZ_IDS_MAP_PATH
        )
        self.tz_name_to_tz_ids = self._load_data(TZ_NAME_TO_TZ_IDS_MAP_PATH)
        self.offset_to_tz_ids = self._load_data(OFFSET_TO_TZ_IDS_MAP_PATH)
        self.normalized_states = self._load_data(STATES_PATH)
        self.tz_name_aliases = self._load_data(ALIASES_PATH)
        self.ca_state_to_tz_ids = self._load_data(CA_STATE_TO_TZ_IDS_MAP_PATH)
        self.ca_area_code_to_state = self._load_data(
            CA_AREA_CODE_TO_STATE_MAP_PATH
        )
        self.au_state_to_tz_ids = self._load_data(AU_STATE_TO_TZ_IDS_MAP_PATH)
        self.au_area_code_to_state = self._load_data(
            AU_AREA_CODE_TO_STATE_MAP_PATH
        )

        # convert string offsets into integers
        self.offset_to_tz_ids = {
            int(k): v for k, v in self.offset_to_tz_ids.items()
        }

        # flatten the values of all tz name aliases (needed to identify which
        # filters don't need to be exact in tztrout.tz_ids_for_tz_name
        self.aliases = {
            alias for v in self.tz_name_aliases.values() for alias in v
        }

    def _load_data(self, path):
        """Load data from a file. Helper method."""
        with open(path) as file:
            data = json.loads(file.read())
            return data

    def _load_us_zipcode_data(self, path):
        dedupe = deduplicator()
        with open(path) as file:
            data = json.load(file)
            return {
                dedupe(k): dedupe(tuple(dedupe(tz) for tz in v))
                for k, v in data.items()
            }

    def _get_latest_non_dst_offset(self, tz):
        """
        Get the UTC offset for a given time zone identifier. Ignore the
        DST offsets.
        """
        dt = datetime.datetime.utcnow()
        while dt.year > self.RECENT_YEARS_START:
            try:
                dst = tz.dst(dt).total_seconds()
                if not dst:
                    return tz.utcoffset(dt)
            except (pytz.NonExistentTimeError, pytz.AmbiguousTimeError):
                pass
            dt -= datetime.timedelta(**self.TD_STEP)

    def _get_latest_offsets(self, tz):
        """
        Get all the UTC offsets (in minutes) that a given time zone
        experienced in the recent years.
        """
        dt = datetime.datetime.utcnow()
        offsets = []
        while dt.year > self.RECENT_YEARS_START:
            try:
                offset = int(tz.utcoffset(dt).total_seconds() / 60)
                if offset not in offsets:
                    offsets.append(offset)
            except (pytz.NonExistentTimeError, pytz.AmbiguousTimeError):
                pass
            dt -= datetime.timedelta(**self.TD_STEP)
        return offsets

    def _get_latest_tz_names(self, tz):
        """Get the recent time zone names for a given time zone identifier."""
        dt = datetime.datetime.utcnow()
        tz_names = []
        while dt.year > self.RECENT_YEARS_START:
            try:
                tz_name = tz.tzname(dt)

                # Ignore TZ names that are really UTC offsets like "+01".
                is_offset = tz_name.startswith(("+", "-"))
                if not is_offset and tz_name not in tz_names:
                    tz_names.append(tz_name)
            except (pytz.NonExistentTimeError, pytz.AmbiguousTimeError):
                pass
            dt -= datetime.timedelta(**self.TD_STEP)
        return tz_names

    def generate_zip_to_tz_id_map(self):
        """
        Generate the map of US zipcodes to time zone identifiers. The
        method finds all the possible time zone identifiers for each zipcode
        using the latitude and longitude of each zipcode to search
        TimezoneFinder.
        """
        try:
            from timezonefinder import TimezoneFinder
        except ImportError as exc:
            raise ImportError(
                'Dependency "timezonefinder" is missing. '
                'Install with "tz-trout[dev]" in order to generate timezone data'
            ) from exc

        tf = TimezoneFinder()

        def _get_tz_identifiers_for_us_zipcode(zipcode):
            """Get all the possible identifiers for a given US zip code."""
            # Find the TZ identifier for a Zipcode given its latitude and longitude
            # using the TimezoneFinder library
            tz_id = tf.timezone_at(lng=zipcode.longitude, lat=zipcode.latitude)
            return [tz_id]

        tz_ids_to_zips = defaultdict(list)
        for cnt, zip in enumerate(generate_us_zipcode_namedtuples()):
            ids = tuple(_get_tz_identifiers_for_us_zipcode(zip))
            if cnt % 100 == 99:
                stdout.write(f"\r{cnt} zipcodes mapped to tz_ids")
                stdout.flush()

            # apply the data exceptions
            exceptions = (
                data_exceptions.get("zip:" + zip.zip)
                or data_exceptions.get("state:" + zip.state)
                or {}
            )
            exceptions["include"] = (
                exceptions.get("include", [])
                + data_exceptions["all"].get("include", [])
                if "all" in data_exceptions
                else []
            )
            exceptions["exclude"] = (
                exceptions.get("exclude", [])
                + data_exceptions["all"].get("exclude", [])
                if "all" in data_exceptions
                else []
            )
            if exceptions:
                ids = tuple(
                    (set(ids) - set(exceptions["exclude"]))
                    | set(exceptions["include"])
                )

            tz_ids_to_zips[ids].append(zip.zip)

        zips_to_tz_ids = {
            zip: sorted(ids)
            for ids, zips in tz_ids_to_zips.items()
            for zip in zips
        }

        _dump_json_data(US_ZIPS_TO_TZ_IDS_MAP_PATH, zips_to_tz_ids)

    def generate_tz_name_to_tz_id_map(self):
        """Generate the map of timezone names to time zone identifiers."""
        tz_name_ids = {}

        # Process common timezones plus whitelisted deprecated ones
        timezones_to_process = (
            list(pytz.common_timezones) + DEPRECATED_TIMEZONES_WHITELIST
        )

        for id in _progressbar(timezones_to_process):
            tz = pytz.timezone(id)
            tz_names = self._get_latest_tz_names(tz)
            if id.startswith("Australia"):
                tz_names = [
                    AU_MAP.get(tz_name, tz_name) for tz_name in tz_names
                ]
            if id.startswith("Asia"):
                tz_names = [
                    ASIA_MAP.get(tz_name, tz_name) for tz_name in tz_names
                ]

            # Include the aliases in the map, too
            for name in tz_names:
                tz_names.extend(self.tz_name_aliases.get(name, []))

            for name in tz_names:
                if name in tz_name_ids and id not in tz_name_ids[name]:
                    tz_name_ids[name].append(id)
                elif name not in tz_name_ids:
                    tz_name_ids[name] = [id]

        _dump_json_data(TZ_NAME_TO_TZ_IDS_MAP_PATH, tz_name_ids)

    def generate_offset_to_tz_id_map(self):
        """Generate the map of UTC offsets to time zone identifiers."""
        offset_tz_ids = defaultdict(list)
        for id in _progressbar(pytz.common_timezones):
            tz = pytz.timezone(id)
            offsets = self._get_latest_offsets(tz)
            for offset in offsets:
                offset_tz_ids[offset].append(id)

        _dump_json_data(OFFSET_TO_TZ_IDS_MAP_PATH, offset_tz_ids)


def _progressbar(lst):
    length_of_list = len(lst)
    for cnt, elem in enumerate(lst):
        yield elem
        if cnt % 10 == 9:
            stdout.write(f"\r{cnt + 1}/{length_of_list}")
            stdout.flush()


def _dump_json_data(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True, separators=(",", ": "))
