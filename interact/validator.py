import prompt_toolkit.validation as validation


class NameValidator(validation.Validator):

    def __init__(self, available_names):
        """
        获取所有现有的能发送消息的普通的节点名称
        :param available_names:
        """
        self.available_names = available_names

    def validate(self, document):
        """
        进行验证
        :return:
        """
        if document.text in self.available_names:
            pass
        else:
            raise validation.ValidationError(message="Please enter a existing normal-node name",
                                             cursor_position=len(document.text))


class FloatValidator(validation.Validator):
    def validate(self, document):
        """
        验证是否是浮点数
        :param document: 用户输入的内容
        :exception 进行异常的抛出
        """
        try:
            float(document.text)
        except ValueError:
            raise validation.ValidationError(message="Please enter a number", cursor_position=len(document.text))


class IntegerValidator(validation.Validator):
    def validate(self, document):
        """
        验证是否是整数
        :param document: 用户输入的内容
        :return:
        """
        try:
            int(document.text)
        except ValueError:
            raise validation.ValidationError(message="Please input a integer", cursor_position=len(document.text))
