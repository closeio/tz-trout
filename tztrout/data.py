import datetime
import functools
import importlib.resources
import json
import os
from collections import defaultdict, namedtuple
from collections.abc import Iterator
from sys import stdout
from zoneinfo import ZoneInfo

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
COUNTRY_TO_TZ_IDS_MAP_PATH = os.path.join(
    basepath, "data/country_to_tz_ids.json"
)
TZ_ID_TO_NON_DST_OFFSET_MAP_PATH = os.path.join(
    basepath, "data/tz_id_to_non_dst_offset.json"
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

# Legacy timezone IDs that are part of the "common" timezones on top of the
# ones listed in zone.tab (this is the same list pytz.common_timezones used).
COMMON_EXTRA_TIMEZONES = [
    "Canada/Atlantic",
    "Canada/Central",
    "Canada/Eastern",
    "Canada/Mountain",
    "Canada/Newfoundland",
    "Canada/Pacific",
    "GMT",
    "US/Alaska",
    "US/Arizona",
    "US/Central",
    "US/Eastern",
    "US/Hawaii",
    "US/Mountain",
    "US/Pacific",
    "UTC",
]

# Deprecated timezone IDs that are still commonly used and should be included
# in the timezone name mapping (these are valid timezone IDs but they are not
# part of the common timezones)
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


def _tzdata_resource(name: str):
    """Return a file from the pinned `tzdata` package."""
    return importlib.resources.files("tzdata").joinpath(name)


@functools.cache
def _pinned_zone(tz_id: str) -> ZoneInfo:
    """
    Load a time zone from the pinned `tzdata` package, ignoring the OS time
    zone database.

    Used for data generation so that the generated files only depend on the
    `tzdata` version and not on the machine the generation runs on.
    """
    with _tzdata_resource(f"zoneinfo/{tz_id}").open("rb") as f:
        return ZoneInfo.from_file(f, key=tz_id)


def _pinned_available_timezones() -> list[str]:
    """
    All the time zone IDs in the pinned `tzdata` package, except for the
    "Factory" placeholder zone.
    """
    return sorted(
        tz_id
        for tz_id in _tzdata_resource("zones").read_text().split()
        if tz_id != "Factory"
    )


def _pinned_zone_tab() -> list[tuple[str, str]]:
    """(country code, time zone ID) rows of zone.tab from `tzdata`."""
    rows = []
    for line in _tzdata_resource("zoneinfo/zone.tab").read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        code, _coordinates, tz_id = line.split(None, 3)[:3]
        rows.append((code, tz_id))
    return rows


def _pinned_common_timezones() -> list[str]:
    """Return the common time zone IDs (what pytz.common_timezones was)."""
    available = set(_pinned_available_timezones())
    return sorted(
        (
            {tz_id for _, tz_id in _pinned_zone_tab()}
            | set(COMMON_EXTRA_TIMEZONES)
        )
        & available
    )


class TroutData:
    """Helper class that generates the JSON data used by TZTrout"""

    # We don't care about the historic data - we just want to know the recent
    # state of time zones, zip codes, etc. RECENT_YEARS_START describes how
    # far back we should go to check for DST changes, timezone names, etc.
    RECENT_YEARS = 10
    RECENT_YEARS_START = datetime.datetime.now().year - RECENT_YEARS

    # How far into the future we look for already scheduled time zone
    # changes (e.g. a region dropping DST next year).
    FUTURE_YEARS = 2
    FUTURE_YEARS_END = datetime.datetime.now().year + FUTURE_YEARS

    # Time zones don't expose their transitions, so we sample them. States
    # shorter than a step could be missed, which is fine for our purposes.
    SAMPLING_STEP = datetime.timedelta(days=1)

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
        self.country_to_tz_ids = self._load_data(COUNTRY_TO_TZ_IDS_MAP_PATH)
        self.tz_id_to_non_dst_offset = self._load_data(
            TZ_ID_TO_NON_DST_OFFSET_MAP_PATH
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

    def _iter_recent_transitions(
        self, tz: datetime.tzinfo
    ) -> Iterator[tuple[datetime.timedelta, datetime.timedelta, str]]:
        """
        Yield (utc_offset, dst_offset, abbr) tuples for all the distinct
        states of a time zone in the recent window, oldest first.

        The time zone is sampled every SAMPLING_STEP between Jan 1st of
        RECENT_YEARS_START and Jan 1st of FUTURE_YEARS_END (UTC), and a new
        tuple is yielded every time the state changes. The first tuple is the
        state active at the start of the window. Finally, a tuple for the
        current moment is yielded.
        """
        utc = datetime.UTC
        sample = datetime.datetime(self.RECENT_YEARS_START, 1, 1, tzinfo=utc)
        end = datetime.datetime(self.FUTURE_YEARS_END, 1, 1, tzinfo=utc)
        previous = None
        while sample < end:
            state = _tz_state(sample.astimezone(tz))
            if state is not None and state != previous:
                yield state
                previous = state
            sample += self.SAMPLING_STEP

        now_state = _tz_state(datetime.datetime.now(utc).astimezone(tz))
        if now_state is not None:
            yield now_state

    def _get_latest_non_dst_offset(
        self, tz: datetime.tzinfo
    ) -> datetime.timedelta | None:
        """
        Get the UTC offset for a given time zone identifier. Ignore the
        DST offsets.
        """
        result = None
        for utc_offset, dst_offset, _ in self._iter_recent_transitions(tz):
            if not dst_offset.total_seconds():
                result = utc_offset
        return result

    def _get_latest_offsets(self, tz: datetime.tzinfo) -> list[int]:
        """
        Get all the UTC offsets (in minutes) that a given time zone
        experienced in the recent years.
        """
        return list(
            {
                int(utc_offset.total_seconds() / 60)
                for utc_offset, _, _ in self._iter_recent_transitions(tz)
            }
        )

    def _get_latest_tz_names(self, tz: datetime.tzinfo) -> list[str]:
        """Get the recent time zone names for a given time zone identifier."""
        tz_names = []
        for _, _, abbr in self._iter_recent_transitions(tz):
            # Ignore TZ names that are really UTC offsets like "+01".
            if not abbr.startswith(("+", "-")) and abbr not in tz_names:
                tz_names.append(abbr)
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
            _pinned_common_timezones() + DEPRECATED_TIMEZONES_WHITELIST
        )

        for id in _progressbar(timezones_to_process):
            tz = _pinned_zone(id)
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
        for id in _progressbar(_pinned_common_timezones()):
            tz = _pinned_zone(id)
            offsets = self._get_latest_offsets(tz)
            for offset in offsets:
                offset_tz_ids[offset].append(id)

        _dump_json_data(OFFSET_TO_TZ_IDS_MAP_PATH, offset_tz_ids)

    def generate_country_to_tz_id_map(self):
        """
        Generate the map of ISO country codes to time zone identifiers, in
        zone.tab order.
        """
        available = set(_pinned_available_timezones())
        country_tz_ids = defaultdict(list)
        for code, tz_id in _pinned_zone_tab():
            if tz_id in available:
                country_tz_ids[code].append(tz_id)

        _dump_json_data(COUNTRY_TO_TZ_IDS_MAP_PATH, country_tz_ids)

    def generate_tz_id_to_non_dst_offset_map(self):
        """
        Generate the map of time zone identifiers to their latest non-DST
        UTC offset (in minutes).
        """
        non_dst_offsets = {}
        for id in _progressbar(_pinned_available_timezones()):
            offset = self._get_latest_non_dst_offset(_pinned_zone(id))
            if offset is not None:
                non_dst_offsets[id] = int(offset.total_seconds() / 60)

        _dump_json_data(TZ_ID_TO_NON_DST_OFFSET_MAP_PATH, non_dst_offsets)


def _tz_state(
    local: datetime.datetime,
) -> tuple[datetime.timedelta, datetime.timedelta, str] | None:
    """(utc_offset, dst_offset, abbr) for an aware datetime, if known."""
    utc_offset = local.utcoffset()
    dst_offset = local.dst()
    abbr = local.tzname()
    if utc_offset is None or dst_offset is None or abbr is None:
        return None
    return utc_offset, dst_offset, abbr


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
