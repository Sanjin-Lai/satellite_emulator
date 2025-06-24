import signal


def signal_decorator(func):
    """
    装饰器：作用是代表
    :param func:
    :return:
    """

    def signal_decorated(*args):
        signal.signal(signal.SIGTERM, lambda: exit())
        func(*args)

    return signal_decorated
