from article import Article
from logger import DatabaseLogger
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
import json
import sqlite3

class Database:
    def __init__(self) -> None:
        # 连接到数据库
        self.conn = sqlite3.connect('database.sqlite')
        self.logger = DatabaseLogger()
        # 初始化数据表
        self.conn.execute('''CREATE TABLE IF NOT EXISTS articles
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                            title TEXT NOT NULL,
                            content TEXT NOT NULL,
                            article_date DATE NOT NULL,
                            link TEXT NOT NULL,
                            categorys TEXT,
                            product TEXT,
                            product_author TEXT,
                            core_summary TEXT,
                            detailed_summary TEXT,
                            token INTEGER,
                            prompt_token INTEGER,
                            completion_token INTEGER,
                            tag TEXT,
                            drop_article TEXT);''')
        
    def get_URIs(self) -> list[str]:
        # 查询数据
        with open('rss.json', 'r', encoding='utf-8') as f:
            rss = json.load(f)
        return [item['URI'] for item in rss]

    def insert_article(self, article: Article) -> None:
        # 判断文章是否存在
        cursor = self.conn.execute("SELECT * FROM articles WHERE title=?", (article['Title'],))
        if cursor.fetchone() is not None:
            return
    
        try:
            # 插入数据
            self.conn.execute("INSERT INTO articles (title, content, article_date, link, categorys) VALUES (?, ?, ?, ?, ?)", (article['Title'], article['Content'], article['ArticleDate'], article['Link'], article['Categorys']))
            self.logger.insert_article(article['Title'])
        except:
            print(article)

        self.conn.commit()
    
    def struct_article(self, row: sqlite3.Cursor) -> Article:
        article = {
            'ID': row[0],
            'Title': row[1],
            'Content': row[2],
            'ArticleDate': row[3],
            'Link': row[4],
            'Categorys': row[5],
            'Product': row[6],
            'ProductAuthor': row[7],
            'CoreSummary': row[8],
            'DetailedSummary': row[9],
            'Tokens': row[10],
            'PromptTokens': row[11],
            'CompletionTokens': row[12]
        }
        return article

    def get_all_articles(self) -> list[Article]:
        # 查询数据
        cursor = self.conn.execute("SELECT * FROM articles")

        return [self.struct_article(row) for row in cursor]
    
    def get_unsummarized_articles(self) -> list[Article]:
        # 查询数据
        cursor = self.conn.execute("SELECT * FROM articles WHERE core_summary IS NULL")
        
        return [self.struct_article(row) for row in cursor]
    
    def get_article(self, id: int) -> Article:
        # 查询数据
        cursor = self.conn.execute("SELECT * FROM articles WHERE id=?", (id,))

        return self.struct_article(cursor.fetchone())
    
    def get_articles_past_week(self, drop=True) -> list[Article]:
        # 查询数据
        cursor = self.conn.execute("SELECT * FROM articles WHERE drop_article IS NULL")

        undrop_articles = [self.struct_article(row) for row in cursor]

        today = datetime.today()
        within_week = lambda x: datetime.strptime(x['ArticleDate'], '%Y-%m-%d').date() >= (today - timedelta(days=today.weekday())).date()
        # parsedate_to_datetime(x['ArticleDate']).date() >= (today - timedelta(days=today.weekday())).date()
        
        return [article for article in undrop_articles if within_week(article)]

    def update_article(self, article: Article) -> None:
        # 更新数据
        self.conn.execute("UPDATE articles SET product=?, product_author=?, core_summary=?, detailed_summary=?, token=?, prompt_token=?, completion_token=?, article_date=? WHERE id=?", (article['Product'], article['ProductAuthor'], article['CoreSummary'], article['DetailedSummary'] , article['Tokens'], article['PromptTokens'], article['CompletionTokens'], article['ArticleDate'], article['ID']))
        self.conn.commit()

    def delete_article(self, article: Article) -> None:
        # 删除数据
        self.conn.execute("DELETE FROM articles WHERE id=?", (article['ID'],))
        self.conn.commit()

    def close_connection(self) -> None:
        # 关闭数据库连接
        self.conn.close()
        