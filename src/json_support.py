from dataclasses import dataclass, field
from datetime import datetime
from typing import Generator, List

import json_lines
from dataclasses_json import config, dataclass_json
from marshmallow import fields

metadata = config(
    encoder=datetime.isoformat,
    decoder=datetime.fromisoformat,
    mm_field=fields.DateTime(format="iso"),
)


@dataclass_json
@dataclass
class TME:
    """
    Captures each line in the given Json-Lines file.
    ("TME" for "ten-minute entry".)
    """

    path: str
    duration_secs: float
    start: datetime = field(metadata=metadata)
    end: datetime = field(metadata=metadata)

    # add when needed:
    # channels: int = 1
    # jitter: float = 0


def parse_json_lines_file(filename: str) -> Generator[TME, None, None]:
    with open(filename, "r", encoding="UTF-8") as f:
        for item in json_lines.reader(f):
            yield TME.from_dict(item)  # type: ignore [attr-defined]


@dataclass
class TMEIntersection:
    tme: TME

    # relative to the start of the TME
    start_secs: int
    duration_secs: int


def get_intersecting_entries(
    json_entries: List[TME],
    segment_size_in_mins: int,
    year: int,
    month: int,
    day: int,
    at_hour: int,
    at_minute: int,
) -> List[TMEIntersection]:
    dt = datetime(year, month, day, at_hour, at_minute)
    day_start_in_secs: int = int(dt.timestamp())
    day_end_in_secs: int = day_start_in_secs + segment_size_in_mins * 60

    result: List[TMEIntersection] = []
    tot_duration_secs = 0
    for tme in json_entries:
        tme_start_in_secs: int = int(tme.start.timestamp())
        tme_end_in_secs: int = int(tme.end.timestamp())
        if tme_start_in_secs <= day_end_in_secs and tme_end_in_secs >= day_start_in_secs:
            start_secs = max(tme_start_in_secs, day_start_in_secs) - tme_start_in_secs
            end_secs = min(tme_end_in_secs, day_end_in_secs) - tme_start_in_secs
            duration_secs = end_secs - start_secs
            result.append(TMEIntersection(tme, start_secs, duration_secs))
            tot_duration_secs += duration_secs

    assert tot_duration_secs == segment_size_in_mins * 60
    return result
