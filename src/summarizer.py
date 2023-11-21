from article import Article
from typing import List
from langchain.pydantic_v1 import BaseModel, Field, validator
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import ChatPromptTemplate
from langchain.schema import BaseOutputParser
from langchain.output_parsers import PydanticOutputParser
from langserve import add_routes
import os
import json

class ArticleJSONParser(BaseOutputParser[str]):
    def json_check(self, output: str) -> bool:
        try:
            json.loads(output)
            return True
        except:
            return False
        
    def zh_to_en(self, zh_dict: dict) -> Article:
        return {
            "Product": zh_dict['产品名称'],
            "ProductAuthor": zh_dict['单位'],
            "CoreSummary": zh_dict['成果'],
            "DetailedSummary": zh_dict['详情']
        }

    def parse(self, output: str) -> Article:
        if self.json_check(output):
            zh_dict = json.loads(output.replace("\n", ""))
            return self.zh_to_en(zh_dict)
            
        else:
            return self.parse(json_fixer_chain.invoke({'text':output}))
        
API_KEY = os.environ['OPENAI_API_KEY']
API_BASE = os.environ['OPENAI_API_BASE']

llm = ChatOpenAI(base_url=API_BASE, api_key=API_KEY, model='gpt-3.5-turbo')

digest_template = '''Role：你是一名人工智能领域的科学家
Task：用户即将输入一段文本，请你以最简洁的语言总结"产品名称"、"单位"、"成果"、"详情" 四项内容，分别以 JSON 形式输出
Format：JSON
Language：中文
Notice：1. 产品名称应是产品名词、事件名或研究名称，若文中没有产品，请以朴素的陈述句给出研究结论。2. 单位是应是企业、学校或政府机构。如没有找到，请写"未知" 3. 成果以一个短标题的形式总结 4. 详情用两句话描述，100字左右 '''

json_fixer_template = '你是一名软件工程师，用户输入的json文本因有误格式而无法序列化，请你协助改正'

human_template = "{text}"

digest_prompt = ChatPromptTemplate.from_messages([("system", digest_template), ("human",human_template)])
json_fixer_prompt = ChatPromptTemplate.from_messages([("system", json_fixer_template), ("human",human_template)])

# parsed_output = parse_result(output, output_parser.parse_json)

json_fixer_chain = json_fixer_prompt | llm 
digest_chain = digest_prompt | llm | ArticleJSONParser()

def summarize(article: Article) -> Article:
    result = digest_chain.invoke({"text":article['Content'][:3500]})
    article['Product'] = result['Product']
    article['ProductAuthor'] = result['ProductAuthor']
    article['CoreSummary'] = result['CoreSummary']
    article['DetailedSummary'] = result['DetailedSummary']
    return article