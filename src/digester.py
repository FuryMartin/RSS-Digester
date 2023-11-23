from bs4 import BeautifulSoup
from requests import request
import xml.etree.ElementTree as ET
from article import Article
from database import Database
from formatters import MarkdownFormatter
from summarizer import Summarizer
from classifier import classify_article
from logger import RSSLogger

class RSSDigester:
    def __init__(self) -> None:
        self.db = Database()
        self.logger = RSSLogger()
        self.summarizer = Summarizer()
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
                article = self.parse_input(item)
                self.db.insert_article(article=article)
                
    def parse_input(self, input:ET.Element) -> Article:
        # Required fields
        title = input.find('title').text
        link = input.find('link').text
        description = self.parse_text(input.find('description').text)
        pubDate = input.find('pubDate').text
        
        # Optional fields
        author = input.find('author').text if input.find('author') else None
        categories = ",".join([category.text for category in input.findall('category')]) if input.find('category') else None
        
        return {
            'Title': title,
            'Link': link,
            'Content': description,
            'ArticleDate': pubDate,
            'ArticleAuthor': author,
            'Categorys': categories
        }

    def parse_text(self, text:str) -> str:
        Soup = BeautifulSoup(text, 'html.parser')
        return Soup.get_text()
    
    def summarize(self, id: int):
        article = self.db.get_article(id)
        summarized_article = self.summarizer.invoke(article)
        self.db.update_article(summarized_article)

    def batch_summarize(self):
        articles = self.db.get_unsummarized_articles()

        if len(articles) == 0:
            return None
        
        summarized_articles = self.summarizer.batch_invoke(articles)
        for article in summarized_articles:
            self.db.update_article(article)

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
    digester.process()
    # digester.summarize(1)
    # digester.format_output()
