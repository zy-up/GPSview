import logging
from datetime import datetime
import os

def setup_GPS_logger(name):
    """设置自定义日志记录器"""
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_directory = "./log"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    log_filename = f"{log_directory}/GPS_log_{current_time}.log"

    # 创建一个自定义的日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # 创建文件处理器
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    # 将处理器添加到日志记录器
    logger.addHandler(file_handler)

    return logger
