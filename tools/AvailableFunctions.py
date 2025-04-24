# ==================================================
# 导入依赖区域
# ==================================================

import inspect
import json

import openai
from openai import OpenAI

# ==================================================
# API配置区域
# ==================================================

# 设置OpenAI API密钥和基础URL
openai.api_key = "sk-XX"
openai.api_base = "https://chatapi.littlewheat.com/v1"

# 创建OpenAI客户端实例
client = OpenAI(api_key=openai.api_key, base_url=openai.api_base)


# ==================================================
# AvailableFunctions 类区域
# ==================================================

class AvailableFunctions():
    """
    外部函数管理类，用于管理和描述可被Chat模型调用的外部函数
    功能包括：管理函数列表、自动生成函数描述、添加新函数等
    """

    def __init__(self, functions_list=[], functions=[], function_call="auto"):
        """
        初始化外部函数管理器
        :param functions_list: 外部函数对象列表，默认为空列表
        :param functions: 外部函数描述列表，默认为空列表
        :param function_call: 函数调用方式，默认为"auto"
        """
        self.functions_list = functions_list
        self.functions = functions
        self.functions_dic = None
        self.function_call = None

        # 如果提供了函数列表但未提供函数描述，则自动生成函数描述
        if functions_list != []:
            self.functions_dic = {func.__name__: func for func in functions_list}
            self.function_call = function_call
            if functions == []:
                self.functions = auto_functions(functions_list)

    def add_function(self, new_function, function_description=None, function_call_update=None):
        """
        添加新的外部函数
        :param new_function: 要添加的新函数对象
        :param function_description: 新函数的描述，可选参数
        :param function_call_update: 更新函数调用方式，可选参数
        """
        self.functions_list.append(new_function)
        self.functions_dic[new_function.__name__] = new_function
        if function_description == None:
            new_function_description = auto_functions([new_function])
            self.functions.append(new_function_description)
        else:
            self.functions.append(function_description)
        if function_call_update != None:
            self.function_call = function_call_update


# ==================================================
# 辅助函数区域
# ==================================================

def auto_functions(functions_list):
    """
    自动生成Chat模型所需的functions参数描述
    :param functions_list: 包含一个或多个函数对象的列表
    :return: 符合Chat模型要求的functions参数描述列表
    """

    def functions_generate(functions_list):
        """
        内部函数，用于实际生成函数描述
        :param functions_list: 函数对象列表
        :return: 函数描述列表
        """
        functions = []
        for function in functions_list:
            # 获取函数文档字符串
            function_description = inspect.getdoc(function)
            # 获取函数名称
            function_name = function.__name__

            # 构造系统提示和用户提示
            system_prompt = '以下是某的函数说明：%s' % function_description
            user_prompt = '根据这个函数的函数说明，请帮我创建一个JSON格式的字典，这个字典有如下5点要求：\
                               1.字典总共有三个键值对；\
                               2.第一个键值对的Key是字符串name，value是该函数的名字：%s，也是字符串；\
                               3.第二个键值对的Key是字符串description，value是该函数的函数的功能说明，也是字符串；\
                               4.第三个键值对的Key是字符串parameters，value是一个JSON Schema对象，用于说明该函数的参数输入规范。\
                               5.输出结果必须是一个JSON格式的字典，只输出这个字典即可，前后不需要任何前后修饰或说明的语句' % function_name

            # 调用Chat API生成函数描述
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )

            # 处理API响应并解析JSON
            json_function_description = json.loads(
                response.choices[0].message.content.replace("```", "").replace("json", ""))
            json_str = {"type": "function", "function": json_function_description}
            functions.append(json_str)
        return functions

    # 设置最大尝试次数
    max_attempts = 4
    attempts = 0

    # 带重试机制的自动生成函数描述
    while attempts < max_attempts:
        try:
            functions = functions_generate(functions_list)
            break  # 成功则跳出循环
        except Exception as e:
            attempts += 1
            print("发生错误：", e)
            if attempts == max_attempts:
                print("已达到最大尝试次数，程序终止。")
                raise  # 达到最大尝试次数后抛出异常
            else:
                print("正在重新运行...")
    return functions
