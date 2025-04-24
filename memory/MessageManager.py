# ==================================================
# 导入依赖区域
# ==================================================

import copy

import openai
import tiktoken


# ==================================================
# MessageManager 类区域
# ==================================================

class MessageManager():
    """
    消息管理器类，用于创建和管理Chat模型的消息对象
    功能包括：管理系统消息和历史对话消息、计算token数量、自动删减消息等
    """

    def __init__(self, system_content_list=[], question='你好。', tokens_thr=None, project=None):
        """
        初始化消息管理器
        :param system_content_list: 系统消息内容列表，默认为空列表
        :param question: 用户初始问题，默认为'你好。'
        :param tokens_thr: token数量阈值，超过时会自动删减消息，默认为None
        :param project: 关联项目，默认为None
        """
        self.system_content_list = system_content_list
        system_messages = []
        history_messages = []
        messages_all = []
        system_content = ''
        history_content = question
        content_all = ''
        num_of_system_messages = 0
        all_tokens_count = 0

        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

        if system_content_list != []:
            for content in system_content_list:
                system_messages.append({"role": "system", "content": content})
                system_content += content

            system_tokens_count = len(encoding.encode(system_content))
            messages_all += system_messages
            num_of_system_messages = len(system_content_list)

            if tokens_thr != None:
                if system_tokens_count >= tokens_thr:
                    print("system_messages的tokens数量超出限制，当前系统消息将不会被输入模型")
                    system_messages = []
                    messages_all = []
                    num_of_system_messages = 0
                    system_tokens_count = 0

            all_tokens_count += system_tokens_count

        history_messages = [{"role": "user", "content": question}]
        messages_all += history_messages

        user_tokens_count = len(encoding.encode(question))
        all_tokens_count += user_tokens_count

        if tokens_thr != None:
            if all_tokens_count >= tokens_thr:
                print("当前用户问题的tokens数量超出限制，该消息无法被输入到模型中")
                history_messages = []
                system_messages = []
                messages_all = []
                num_of_system_messages = 0
                all_tokens_count = 0

        self.messages = messages_all
        self.system_messages = system_messages
        self.history_messages = history_messages
        self.tokens_count = all_tokens_count
        self.num_of_system_messages = num_of_system_messages
        self.tokens_thr = tokens_thr
        self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        self.project = project

    def messages_pop(self, manual=False, index=None):
        """
        删除部分对话消息
        :param manual: 是否手动删除，默认为False
        :param index: 要删除的消息索引，默认为None
        """

        def reduce_tokens(index):
            drop_message = self.history_messages.pop(index)
            self.tokens_count -= len(self.encoding.encode(str(drop_message)))

        if self.tokens_thr is not None:
            while self.tokens_count >= self.tokens_thr:
                reduce_tokens(-1)

        if manual:
            if index is None:
                reduce_tokens(-1)
            elif 0 <= index < len(self.history_messages) or index == -1:
                reduce_tokens(index)
            else:
                raise ValueError("Invalid index value: {}".format(index))

        self.messages = self.system_messages + self.history_messages

    def messages_append(self, new_messages):
        """
        添加新消息
        :param new_messages: 要添加的新消息，可以是字典、ChatCompletionMessage或MessageManager对象
        """
        if type(new_messages) is dict or type(
                new_messages) is openai.types.chat.chat_completion_message.ChatCompletionMessage:
            self.messages.append(new_messages)
            self.tokens_count += len(self.encoding.encode(str(new_messages)))

        elif isinstance(new_messages, MessageManager):
            self.messages += new_messages.messages
            self.tokens_count += new_messages.tokens_count

        self.history_messages = self.messages[self.num_of_system_messages:]
        self.messages_pop()

    def copy(self):
        """
        复制当前消息管理器对象
        :return: 返回一个新的MessageManager对象
        """
        system_content_str_list = [message["content"] for message in self.system_messages]
        new_obj = MessageManager(
            system_content_list=copy.deepcopy(system_content_str_list),
            question=self.history_messages[0]["content"] if self.history_messages else '',
            tokens_thr=self.tokens_thr
        )
        new_obj.history_messages = copy.deepcopy(self.history_messages)
        new_obj.messages = copy.deepcopy(self.messages)
        new_obj.tokens_count = self.tokens_count
        new_obj.num_of_system_messages = self.num_of_system_messages

        return new_obj

    def add_system_messages(self, new_system_content):
        """
        添加系统消息
        :param new_system_content: 要添加的系统消息内容
        """
        system_content_list = self.system_content_list
        system_messages = []
        if type(new_system_content) == str:
            new_system_content = [new_system_content]

        system_content_list.extend(new_system_content)
        new_system_content_str = ''
        for content in new_system_content:
            new_system_content_str += content
        new_token_count = len(self.encoding.encode(str(new_system_content_str)))
        self.tokens_count += new_token_count
        self.system_content_list = system_content_list
        for message in system_content_list:
            system_messages.append({"role": "system", "content": message})
        self.system_messages = system_messages
        self.num_of_system_messages = len(system_content_list)
        self.messages = system_messages + self.history_messages

        self.messages_pop()

    def delete_system_messages(self):
        """
        删除所有系统消息
        """
        system_content_list = self.system_content_list
        if system_content_list != []:
            system_content_str = ''
            for content in system_content_list:
                system_content_str += content
            delete_token_count = len(self.encoding.encode(str(system_content_str)))
            self.tokens_count -= delete_token_count
            self.num_of_system_messages = 0
            self.system_content_list = []
            self.system_messages = []
            self.messages = self.history_messages

    def delete_function_messages(self):
        """
        删除所有函数消息
        """
        history_messages = self.history_messages
        for index in range(len(history_messages) - 1, -1, -1):
            message = history_messages[index]
            if message.get("function_call") or message.get("role") == "function":
                self.messages_pop(manual=True, index=index)
