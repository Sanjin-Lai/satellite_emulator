import time

from loguru import logger


def elapsed_time_decorator(func):
    """
    进行时间的度量
    :param func: 传入的参数
    :return: 经过装饰的函数
    """

    async def record_time_elapsed(*args):
        start_time = time.time()
        await func(*args)
        stop_time = time.time()
        logger.info(f"{func.__name__} elapsed {stop_time - start_time} seconds")

    return record_time_elapsed
