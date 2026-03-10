# Changelog

## Version 1.2.0

- Add `non_dst_offset_for_tz_id` to the public interface

- Change the value of RECENT_YEARS_START to be now() -15 years

For some data that is time dependant like what ever a TZ ID has ever been one particular offset value
we consider a sliding window of 15 years.

We previously considered every value since 2005.

- Bump minimum python version to 3.10 from 3.9

We were inconsistently returning None for some of these.

- Return an empty list in all no tz/address responses
- Minor updates of ruff, mypyx and pytest
- Update dependabot settings to have cooldown.

## Version 1.1.2
- Support for a whitelist of deprecated timezones
- Regenerated data after pytz version update
- Updated ruff version
- Updated pytz version

## Version 1.1.1
- Improve TZ detection for non-geographical numbers
- Use libphonenumbers to get phone's timezone for US numbers
- Use ruff for formatting

## Version 1.1.0
- Drop support for python 3.8
- Use libphonenumbers to get phone's timezone for Canadian numbers

    This should fix issues with new area codes in Canada not being recognized

- Library CI now runs on GitHub actions

## Version 1.0.5
- Removed America/Yellowknife timezone

## Version 1.0.4
- description added to PyPI

## Version 1.0.3
- added eastern Kentucky exception
- updated data