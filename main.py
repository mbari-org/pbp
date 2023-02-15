import json_lines

from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config

from datetime import datetime
from marshmallow import fields

datetime_field = field(
    metadata=config(
        encoder=datetime.isoformat,
        decoder=datetime.fromisoformat,
        mm_field=fields.DateTime(format='iso')
    )
)


@dataclass_json
@dataclass
class TenMinEntry:
    path: str
    duration_secs: float
    channels: int
    jitter: float
    start: datetime = datetime_field
    end: datetime = datetime_field


def main():
    with open('jsons/20220902.json') as f:
        for item in json_lines.reader(f):
            de = TenMinEntry.from_dict(item)
            print(de)


if __name__ == "__main__":
    main()
