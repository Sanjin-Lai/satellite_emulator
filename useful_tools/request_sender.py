import requests


class RequestSender:
    @classmethod
    def send_get_request(cls, url):
        """
        进行 GET 请求的发送
        :param url 发送的 url 的链接
        :return 进行响应的返回
        """
        response = requests.get(url=url)
        return response

    @classmethod
    def send_post_request(cls, ):
        """
        进行 POST 请求的发送
        """

