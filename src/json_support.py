import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Generator, List
from urllib.parse import urlparse

from dataclasses_json import config, dataclass_json
from marshmallow import fields

from src.misc_helper import debug, get_logger, warn

metadata = config(
    encoder=datetime.isoformat,
    decoder=datetime.fromisoformat,
    mm_field=fields.DateTime(format="iso"),
)


@dataclass_json
@dataclass
class JEntry:
    """
    Captures each object in the array contained in the given Json file.
    """

    uri: str
    duration_secs: float
    start: datetime = field(metadata=metadata)
    end: datetime = field(metadata=metadata)

    # add when needed:
    # channels: int = 1
    # jitter: float = 0

    @property
    def path(self) -> str:
        return urlparse(self.uri).path


def parse_json_contents(contents: str) -> Generator[JEntry, None, None]:
    for item in json.loads(contents):
        yield JEntry.from_dict(item)  # type: ignore [attr-defined]


def parse_json_file(filename: str) -> Generator[JEntry, None, None]:
    with open(filename, "r", encoding="UTF-8") as f:
        for item in json.load(f):
            yield JEntry.from_dict(item)  # type: ignore [attr-defined]


@dataclass
class JEntryIntersection:
    entry: JEntry

    # relative to the start of the JEntry
    start_secs: int
    duration_secs: int


def get_intersecting_entries(
    json_entries: List[JEntry],
    segment_size_in_mins: int,
    year: int,
    month: int,
    day: int,
    at_hour: int,
    at_minute: int,
) -> List[JEntryIntersection]:
    dt = datetime(year, month, day, at_hour, at_minute)
    day_start_in_secs: int = int(dt.timestamp())
    day_end_in_secs: int = day_start_in_secs + segment_size_in_mins * 60

    intersecting_entries: List[JEntryIntersection] = []
    tot_duration_secs = 0
    for entry in json_entries:
        entry_start_in_secs: int = int(entry.start.timestamp())
        # issue with `end` in some JSON files...
        # entry_end_in_secs: int = int(entry.end.timestamp())
        # ... so, let's use `duration_secs`
        entry_end_in_secs: int = entry_start_in_secs + int(entry.duration_secs)
        if (
            entry_start_in_secs <= day_end_in_secs
            and entry_end_in_secs >= day_start_in_secs
        ):
            start_secs = max(entry_start_in_secs, day_start_in_secs) - entry_start_in_secs
            end_secs = min(entry_end_in_secs, day_end_in_secs) - entry_start_in_secs
            duration_secs = end_secs - start_secs
            intersecting_entries.append(
                JEntryIntersection(entry, start_secs, duration_secs)
            )
            tot_duration_secs += duration_secs

    time_spec = (
        f"year={year} month={month} day={day} at_hour={at_hour} at_minute={at_minute}"
    )

    # verify expected duration:
    segment_size_in_secs = segment_size_in_mins * 60
    if tot_duration_secs != segment_size_in_secs:
        msg = f"tot_duration_secs={tot_duration_secs} != {segment_size_in_secs}"
        msg += f"  {time_spec}"
        msg += f"  intersecting_entries ({len(intersecting_entries)})"
        if len(intersecting_entries) > 0:
            msg += "".join(f"\n    {i}" for i in intersecting_entries)
        warn(msg)

    if get_logger().isEnabledFor(logging.DEBUG):
        uris = [i.entry.uri for i in intersecting_entries]
        uris_str = "\n  ".join([f"[{e}] {uri}" for e, uri in enumerate(uris)])
        debug(f"{time_spec}: intersection uris({len(uris)}):\n  {uris_str}")

    return intersecting_entries
