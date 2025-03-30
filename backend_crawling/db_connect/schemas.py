import datetime
import pydantic

class CrawledDataBase(pydantic.BaseModel):
    url: str
    contents: str
    analysis: bool
    is_analyzed: bool

class CrawledData(CrawledDataBase):
    id: int
    crawled_at: datetime