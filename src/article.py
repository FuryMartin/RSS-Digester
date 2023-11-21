from typing import TypedDict, List

class Article(TypedDict):
    ID: int
    Title: str
    Content: str
    ArticleDate: str
    Link: str
    ArticleAuthor: str
    Categorys: List[str]
    Product: str
    ProductAuthor: str
    CoreSummary: str 
    DetailedSummary: str