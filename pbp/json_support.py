import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Generator, List
from urllib.parse import urlparse
from dataclasses_json import config, dataclass_json
from dateutil import parser as iso8601_parser


@dataclass_json
@dataclass
class JEntry:
    """
    Captures each object in the array contained in the given Json file.
    """

    uri: str
    duration_secs: float
    start: datetime = field(
        metadata=config(
            encoder=lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            decoder=iso8601_parser.parse,
        )
    )

    @property
    def path(self) -> str:
        return urlparse(self.uri).path


def parse_json_contents(contents: str) -> Generator[JEntry, None, None]:
    reported_uris = set()
    for item in json.loads(contents):
        entry = JEntry.from_dict(item)  # type: ignore [attr-defined]
        if entry.uri in reported_uris:
            print(f"warning: Skipping duplicate json entry: uri={entry.uri}")
            continue
        reported_uris.add(entry.uri)
        yield entry


def parse_json_file(filename: str) -> Generator[JEntry, None, None]:
    with open(filename, "r", encoding="UTF-8") as f:
        return parse_json_contents(f.read())


@dataclass_json
@dataclass
class JEntryIntersection:
    entry: JEntry

    # relative to the start of the JEntry
    start_secs: int
    duration_secs: int


def get_intersecting_entries(
    log,  # : loguru.Logger,
    json_entries: List[JEntry],
    year: int,
    month: int,
    day: int,
    at_hour: int,
    at_minute: int,
    segment_size_in_mins: int = 1,
) -> List[JEntryIntersection]:
    """
    Gets the list of intersecting entries for the UTC "start minute"
    given by (year, month, day, at_hour, at_minute).

    :param log:
        Logger
    :param json_entries:
        JSON entries for the day
    :param year:
        Year associated to the start minute
    :param month:
        Month associated to the start minute
    :param day:
        Day associated to the start minute
    :param at_hour:
        Hour associated to the start minute
    :param at_minute:
        Minute associated to the start minute
    :param segment_size_in_mins:
        The size of the segment in minutes, by default 1.

    :return:
        The list of intersecting entries
    """
    # for logging purposes:
    time_spec = (
        f"year={year} month={month} day={day} at_hour={at_hour} at_minute={at_minute}"
    )
    log.debug(f"get_intersecting_entries: {time_spec} {len(json_entries)=}")

    # the requested start minute as datetime:
    dt = datetime(year, month, day, at_hour, at_minute, tzinfo=timezone.utc)
    # the start of the requested start minute in seconds:
    minute_start_in_secs: int = int(dt.timestamp())
    # the end of the requested start minute in seconds:
    minute_end_in_secs: int = minute_start_in_secs + segment_size_in_mins * 60

    intersecting_entries: List[JEntryIntersection] = []
    tot_duration_secs = 0
    for entry in json_entries:
        entry_start_in_secs: int = int(entry.start.timestamp())
        entry_end_in_secs: int = entry_start_in_secs + int(entry.duration_secs)
        if (
            entry_start_in_secs <= minute_end_in_secs
            and entry_end_in_secs >= minute_start_in_secs
        ):
            start_secs = (
                max(entry_start_in_secs, minute_start_in_secs) - entry_start_in_secs
            )
            end_secs = min(entry_end_in_secs, minute_end_in_secs) - entry_start_in_secs
            duration_secs = end_secs - start_secs
            intersecting_entries.append(
                JEntryIntersection(entry, start_secs, duration_secs)
            )
            tot_duration_secs += duration_secs

    warning = 0 == len(intersecting_entries)

    def log_msg():
        uris = [i.entry.uri for i in intersecting_entries]
        uris_str = "\n  ".join([f"[{e}] {uri}" for e, uri in enumerate(uris)])
        return f"{time_spec}: intersection uris({len(uris)}):\n  {uris_str}"

    if warning:
        log.opt(lazy=True).warning("get_intersecting_entries: {}", log_msg)
    else:
        log.opt(lazy=True).debug("get_intersecting_entries: {}", log_msg)

    return intersecting_entries
