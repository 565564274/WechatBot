import logging

from utils.singleton import singleton
from utils.root_path import DEFAULT_PATH


@singleton
class LoggerManager:
    
    def __init__(self):
        self.logger = logging.getLogger(
            'Robot',
        )
        self.logger.setLevel(logging.DEBUG)

        # 创建控制台handler并设置级别为debug，用于输出到控制台
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        # 创建文件handler并设置级别为info，用于输出到文件
        self.log_file = DEFAULT_PATH / 'robot.log'
        self.logger.info(f"输出日志文件：{self.log_file}")
        fh = logging.FileHandler(self.log_file, encoding='utf-8')
        fh.setLevel(logging.DEBUG)

        # 定义handler的格式
        formatter = logging.Formatter('%(asctime)s[%(name)s] %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)
        
        # 将handler添加到logger中
        self.logger.addHandler(ch)
        self.logger.addHandler(fh)


logger_manager = LoggerManager()


