from bs4 import BeautifulSoup
from requests import request
from typing import TypedDict, List
from article import Article
from database import Database
from formatters import MarkdownFormatter

import xml.etree.ElementTree as ET

from classifier import classify_article
from summarizer import summarize, batch_summarize

from logger import RSSLogger
import asyncio

class RSSDigester:
    def __init__(self) -> None:
        self.db = Database()
        self.logger = RSSLogger()
        self.md_formmater = MarkdownFormatter(self.db)

    def fetch_articles(self):
        self.URIs = self.db.get_URIs()
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
    
    def summarize(self, id: int):
        article = self.db.get_article(id)
        try:
            summarized_article, token_counter = summarize(article)
            self.db.update_article(summarized_article)
            self.logger.summarize(article['Title'])
            self.logger.token_usage(token_counter)
        except Exception as error:
            self.logger.summarize_failed(article['Title'], error)

    def batch_summarize(self):
        articles = self.db.get_unsummarized_articles()
        if len(articles) == 0:
            return None
        try:
            summarized_articles, token_counter = batch_summarize(articles)
            for article in summarized_articles:
                self.db.update_article(article)
                self.logger.summarize(article['Title'])
            self.logger.token_usage(token_counter)
        except Exception as error:
            self.logger.summarize_failed('', error)

    def classify_articles(self):
        articles = self.db.get_all_articles()
        # Classify articles using LangChain
        classified_articles = [classify_article(article) for article in articles]
        # Update article in database
        self.db.update_article(classified_articles)
    
    def format_output(self, format_type:str = 'md') -> None:
        if format_type == 'md':
            self.md_formmater.run()

    def process(self) -> None:
        self.fetch_articles()
        self.batch_summarize()
        self.format_output()

if __name__ == '__main__':
    digester = RSSDigester()
    # digester.process()
    digester.summarize(21)
    digester.format_output()
