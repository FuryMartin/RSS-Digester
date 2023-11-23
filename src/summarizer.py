import concurrent.futures
from article import Article
from typing import List
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import ChatPromptTemplate
from langchain.callbacks import get_openai_callback, OpenAICallbackHandler
from logger import SummarizerLogger
import os
import json

class ArticleJSONParser:
    def __init__(self, json_fixer_chain, logger:SummarizerLogger):
        self.json_fixer_chain = json_fixer_chain
        self.logger = logger

    def json_check(self, output: str) -> bool:
        try:
            json.loads(output)
            return True
        except:
            return False
        
    def parse(self, output: str) -> Article:
        output = output.replace("\n", "")
        if self.json_check(output):
            return json.loads(output)
        else:
            self.logger.json_parse_error(output)
            fix = self.json_fixer_chain.invoke({'text':output})
            return self.parse(fix.content)
    
        
class Summarizer:
    def __init__ (self, base_url: str = None, api_key: str = None, model: str = 'gpt-3.5-turbo'):
        self.logger = SummarizerLogger()

        base_url = os.environ['OPENAI_API_BASE'] if base_url is None else base_url
        api_key = os.environ['OPENAI_API_KEY'] if api_key is None else api_key

        self.llm = ChatOpenAI(base_url=base_url, api_key=api_key, model=model)

        self.digester = self.get_digester()
        self.json_fixer = self.get_json_fixer()

        self.json_parser = ArticleJSONParser(self.json_fixer, self.logger)

    def get_digester(self):
        digest_template = '''Role：你是一名人工智能领域的科学家
Task：用户即将输入一段文本，请你以最简洁的语言总结"产品名称"、"单位"、"成果"、"详情" 四项内容，以 JSON 格式输出这四个 Key.
Format：JSON
Language：中文
Notice：1. 产品名称应是产品名词、事件名或研究名称，若文中没有产品，请以朴素的陈述句给出研究结论。2. 单位是应是企业、学校或政府机构。如没有找到，请写"未知" 3. 成果以一个短标题的形式总结 4. 详情用两句话描述，100字左右，需涵盖重点信息 '''
        human_template = "{text}"
        digest_prompt = ChatPromptTemplate.from_messages([("system", digest_template), ("human",human_template)])

        return digest_prompt | self.llm
    
    def get_json_fixer(self):
        json_fixer_template = '你是一名软件工程师，用户输入的json文本因有误格式而无法序列化，请你协助改正'
        human_template = "{text}"
        json_fixer_prompt = ChatPromptTemplate.from_messages([("system", json_fixer_template), ("human",human_template)])

        return json_fixer_prompt | self.llm
        
    def struct_token_counter(self, callback: OpenAICallbackHandler):
        return {
            "Tokens": callback.total_tokens,
            "PromptTokens": callback.prompt_tokens,
            "CompletionTokens": callback.completion_tokens
        }

    def zh_to_en(self, zh_dict: dict) -> Article:
        return {
            "Product": zh_dict['产品名称'],
            "ProductAuthor": zh_dict['单位'],
            "CoreSummary": zh_dict['成果'],
            "DetailedSummary": zh_dict['详情']
        }

    def invoke(self, article: Article, token_info:bool = True) -> Article:
        get_content = lambda x: (x['Title'] + x['Content'])[:3200]
        try:
            with get_openai_callback() as callback:
                raw_result = self.digester.invoke({"text": get_content(article)})
                zh_result = self.json_parser.parse(raw_result.content)
                result = self.zh_to_en(zh_result)
                token_info = self.struct_token_counter(callback)
        except Exception as error:
            self.logger.summarize_failed(article['Title'], error)
            return article

        article.update(result)

        if token_info:
            article.update(token_info)
        
        self.logger.summarize(article['Title'])
        
        return article

    def batch_invoke(self, articles: List[Article]) -> List[Article]:
        if len(articles) == 1:
            return [self.invoke(articles[0])]

        with concurrent.futures.ThreadPoolExecutor(max_workers = 4) as executor:
            # 提交任务到线程池
            results = [executor.submit(self.invoke, article = article) for article in articles]

            return [future.result() for future in concurrent.futures.as_completed(results)]

if __name__ == '__main__':
    pass