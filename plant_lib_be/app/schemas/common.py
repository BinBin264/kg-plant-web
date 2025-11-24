from pydantic import BaseModel

class PageMeta(BaseModel):
    total: int      # tổng số bản ghi
    page: int       # trang hiện tại (>=1)
    size: int       # số bản ghi / trang
    pages: int      # tổng số trang
    has_next: bool
    has_prev: bool
