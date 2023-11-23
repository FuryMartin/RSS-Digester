import pathlib
from article import Article
from typing import List
from database import Database
from datetime import datetime, date
from logger import FormatterLogger


class Formatter:
    def __init__(self, db:Database) -> None:
        self.db = db
        self.logger = FormatterLogger()

    def fetch_articles(self):
        return self.db.get_articles_past_week()

    def sort_articles(self, articles: List[Article], sort_type: str, reverse=True) -> List[Article]:
        # 根据日期等内容进行排序
        if sort_type == 'DATE':
            articles.sort(key=lambda x: datetime.strptime(x['ArticleDate'], self.date_input()), reverse=reverse)
        return articles

    def save(self, lines: List[str]):
        year, week = date.today().isocalendar()[:2]
        filename = f'./archive/{year}-Week{week}.md'

        # mkdir if not exist
        pathlib.Path('./archive').mkdir(parents=True, exist_ok=True)

        with open(filename, 'w', encoding='utf-8') as md_file:
            md_file.writelines(lines)
            
        self.logger.save(filename)

    def format_article(self, article: Article) -> str:
        pass

    def date_input(self) -> str:
        pass
    
    def date_output(self) -> str:
        pass

    def run(self):
        articles = self.fetch_articles()
        articles = self.sort_articles(articles, 'DATE')
        lines = [self.format_article(article) for article in articles]
        self.save(lines)

class MarkdownFormatter(Formatter):
    def date_format(self, date: str) -> str:
        return datetime.strptime(date, self.date_input()).strftime(self.date_output())
    
    def date_input(self) -> str:
        return '%a, %d %b %Y %H:%M:%S %Z'
    
    def date_output(self) -> str:
        return '%Y-%m-%d'

    def format_article(self, article: Article) -> str:
        try:
            date = self.date_format(article['ArticleDate'])
        except:
            date = article['ArticleDate']
            
        return f"**[{article['Product']}]({article['Link']})：{article['CoreSummary']} | {article['ProductAuthor']}**\n\n【{date}】{article['DetailedSummary']}\n\n"
    