# ==================================================
# 导入依赖区域
# ==================================================

from memory.MessageManager import MessageManager
from planning.Planning import *


# ==================================================
# iQueryAgent类区域
# ==================================================

class iQueryAgent():
    def __init__(self,
                 api_key,
                 model='gpt-3.5-turbo-16k',
                 system_content_list=[],
                 project=None,
                 messages=None,
                 available_functions=None,
                 is_expert_mode=False,
                 is_developer_mode=False):
        """
        iQueryAgent类初始化方法
        :param api_key: OpenAI API密钥字符串
        :param model: 使用的模型名称，默认为'gpt-3.5-turbo-16k'
        :param system_content_list: 系统消息或外部文档列表，默认为空列表
        :param project: CloudFile类对象，用于本地存储对话，默认为None
        :param messages: 初始对话消息，MessageManager对象或字典列表，默认为None
        :param available_functions: 可用外部工具，AvailableFunction对象，默认为None
        :param is_expert_mode: 是否开启专家模式，默认为False
        :param is_developer_mode: 是否开启开发者模式，默认为False
        """
        self.api_key = api_key
        self.model = model
        self.project = project
        self.system_content_list = system_content_list
        tokens_thr = None

        # 根据模型类型设置token阈值
        if '1106' in model:
            tokens_thr = 110000
        elif '16k' in model:
            tokens_thr = 12000
        elif 'gpt-4-0613' in model:
            tokens_thr = 7000
        elif 'gpt-4-turbo-preview' in model:
            tokens_thr = 110000
        else:
            tokens_thr = 3000

        self.tokens_thr = tokens_thr

        # 初始化消息管理器
        self.messages = MessageManager(system_content_list=system_content_list,
                                       tokens_thr=tokens_thr)

        # 如果有初始消息，添加到消息管理器
        if messages != None:
            self.messages.messages_append(messages)

        self.available_functions = available_functions
        self.is_expert_mode = is_expert_mode
        self.is_developer_mode = is_developer_mode

        # 显示欢迎信息
        title = "【===================欢迎使用iQuery Agent 智能数据分析平台================================】"
        display(Markdown(title))

    def chat(self, question=None):
        """
        主对话方法，支持单轮和多轮对话
        :param question: 用户问题字符串，None表示多轮对话模式
        """
        head_str = "▌ Model set to %s" % self.model
        display(Markdown(head_str))

        if question != None:
            # 单轮对话模式
            self.messages.messages_append({"role": "user", "content": question})
            self.messages = one_chat_response(model=self.model,
                                              messages=self.messages,
                                              available_functions=self.available_functions,
                                              is_developer_mode=self.is_developer_mode,
                                              is_expert_mode=self.is_expert_mode)
        else:
            # 多轮对话模式
            while True:
                self.messages = one_chat_response(model=self.model,
                                                  messages=self.messages,
                                                  available_functions=self.available_functions,
                                                  is_developer_mode=self.is_developer_mode,
                                                  is_expert_mode=self.is_expert_mode)

                user_input = input("您还有其他问题吗？(输入退出以结束对话): ")
                if user_input == "退出":
                    break
                else:
                    self.messages.messages_append({"role": "user", "content": user_input})

    def reset(self):
        """
        重置对话消息
        """
        self.messages = MessageManager(system_content_list=self.system_content_list)

    def upload_messages(self):
        """
        上传当前对话消息到项目
        """
        if self.project == None:
            print("需要先输入project参数（需要是一个CloudFile对象），才可上传messages")
            return None
        else:
            self.project.append_doc_content(content=self.messages.history_messages)
