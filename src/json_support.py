from dataclasses import dataclass, field
from datetime import datetime
from typing import Generator

import json_lines
from dataclasses_json import config, dataclass_json
from marshmallow import fields

datetime_field = field(
    metadata=config(
        encoder=datetime.isoformat,
        decoder=datetime.fromisoformat,
        mm_field=fields.DateTime(format="iso"),
    )
)


@dataclass_json
@dataclass
class TenMinEntry:
    """
    Captures each line in the given Json-Lines file.
    """

    path: str
    duration_secs: float
    start: datetime = datetime_field
    end: datetime = datetime_field
    channels: int = 1
    jitter: float = 0


def parse_json_lines_file(filename: str) -> Generator[TenMinEntry, None, None]:
    with open(filename, "r", encoding="UTF-8") as f:
        for item in json_lines.reader(f):
            yield TenMinEntry.from_dict(item)  # type: ignore [attr-defined]
