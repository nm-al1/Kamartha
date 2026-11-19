from dataclasses import dataclass
from fastapi import Query


@dataclass(frozen=True)
class Page:
    limit: int = 20
    offset: int = 0

    def metadata(self, total: int):
        return {'limit': self.limit, 'offset': self.offset, 'total': total,
                'has_more': self.offset + self.limit < total}


def page_params(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    return Page(limit, offset)
