from bs4 import BeautifulSoup
from requests import request
from typing import TypedDict, List
from article import Article
from database import Database
from formatters import MarkdownFormatter

import xml.etree.ElementTree as ET

from classifier import classify_article
from summarizer import summarize

from logger import RSSLogger

class RSSDigester:
    def __init__(self, db:Database) -> None:
        self.db = db
        self.logger = RSSLogger()
        self.URIs = self.db.get_URIs()

    def fetch_articles(self):
        for URI in self.URIs:
            try:
                response = request('GET', URI, proxies={'http': 'http://127.0.0.1:7890'})
                self.logger.request(URI)
            except Exception as error:
                self.logger.request_failed(URI, error)
                continue

            root =  ET.fromstring(response.text)
            items = root.findall('.//item')

            for item in items:
                article : Article = {
                    'Title': item.find('title').text,
                    'Content': self.parse_text(item.find('description').text),
                    'Link': item.find('link').text,
                    'ArticleDate': item.find('pubDate').text,
                    'ArticleAuthor': item.find('author').text,
                    'Categorys': ",".join([category.text for category in item.findall('category')])
                }
                self.db.insert_article(article=article)

    def parse_text(self, text:str) -> str:
        Soup = BeautifulSoup(text, 'html.parser')
        return Soup.get_text()

    def summarize_articles(self):
        # fetch articles thar are not summarized
        articles = self.db.get_unsummarized_articles()
        # Summary article using LangChain
        for article in articles:
            try:
                summarized = summarize(article)
                self.logger.summarize(article['Title'])
                self.db.update_article(summarized)
            except Exception as error:
                self.logger.summarize_failed(article['Title'], error)


    def classify_articles(self):
        articles = self.db.get_all_articles()
        # Classify articles using LangChain
        classified_articles = [classify_article(article) for article in articles]
        # Update article in database
        self.db.update_article(classified_articles)

        pass

if __name__ == '__main__':
    db = Database()
    digester = RSSDigester(db)
    md_formmater = MarkdownFormatter(db)
    digester.fetch_articles()
    digester.summarize_articles()
    md_formmater.run()