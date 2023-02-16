from dataclasses import dataclass, field

from datetime import datetime

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
    path: str
    duration_secs: float
    start: datetime = datetime_field
    end: datetime = datetime_field
    channels: int = 1
    jitter: float = 0


def main():
    with open("jsons/20220902.json", "r", encoding="UTF-8") as f:
        for item in json_lines.reader(f):
            tme = TenMinEntry.from_dict(item)
            print(tme)


if __name__ == "__main__":
    main()
