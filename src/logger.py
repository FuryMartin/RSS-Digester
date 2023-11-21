import logging

class Logger:
    def __init__(self, name:str):
        self.name = name
        self.logger = self.create_logger()

    def create_logger(self):
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.DEBUG)

        # 创建一个文件处理器，将日志写入到文件中
        file_handler = logging.FileHandler('rss.log', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        # 创建一个控制台处理器，将日志输出到控制台
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        # 创建一个格式化器，定义日志的格式
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # 将处理器添加到logger对象中
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def debug(self, message: str):
        self.logger.debug(message)

    def info(self, message: str):
        self.logger.info(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def error(self, message: str):
        self.logger.error(message)
    
    def critical(self, message: str):
        self.logger.critical(message)

class DatabaseLogger(Logger):
    def __init__(self, name:str = 'database') -> None:
        super().__init__(name)

    def insert_article(self, title: str):
        self.info(f'[Insert] {title}')

    def delete_article(self, title: str):
        self.info(f'[Delete] {title}')
    
class SummarizerLogger(Logger):
    def __init__(self, name:str = 'summarizer') -> None:
        super().__init__(name)
    
    def summarize(self, title: str):
        self.info(f'[Summarize] {title}')
    
class RSSLogger(Logger):
    def __init__(self, name: str = 'rss'):
        super().__init__(name)

    def request(self, URI: str):
        self.info(f'[Request] {URI}')

    def summarize(self, title: str):
        self.info(f'[Summarize] {title}')

    def request_failed(self, URI: str, e: Exception):
        self.error(f'[Request Failed] {URI}. [Message] {e}')

    def summarize_failed(self, title: str, e: Exception):
        self.error(f'[Summarize Failed] {title}. [Message] {e}')

class FormatterLogger(Logger):
    def __init__(self, name:str = 'formatter') -> None:
        super().__init__(name)
    
    def save(self, path: str):
        self.info(f'[Save] {path}')