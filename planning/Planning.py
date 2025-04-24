# ==================================================
# 导入依赖区域
# ==================================================

import json
import time

import openai
from IPython.display import display, Markdown
from openai import OpenAI, AuthenticationError

# ==================================================
# API配置区域
# ==================================================

# 设置OpenAI API密钥和基础URL
openai.api_key = "sk-XX"
openai.api_base = "https://chatapi.littlewheat.com/v1"

# 创建OpenAI客户端实例
client = OpenAI(api_key=openai.api_key, base_url=openai.api_base)


# ==================================================
# 提示模板函数区域
# ==================================================

def add_task_decomposition_prompt(messages):
    """
    添加任务分解提示模板到消息中
    :param messages: MessageManager对象，包含当前对话消息
    :return: 添加了任务分解few-shot示例的新MessageManager对象
    """
    # 定义few-shot示例
    user_question1 = '请什么是机器学习？'
    user_message1_content = f"现有用户问题如下：{user_question1}。为了回答这个问题，总共需要分几步来执行呢？若无需拆分执行步骤，请直接回答原始问题。"
    assistant_message1_content = '机器学习是一种人工智能（AI）的形式...'

    user_question2 = '请帮我介绍下OpenAI。'
    user_message2_content = f"现有用户问题如下：{user_question2}。为了回答这个问题，总共需要分几步来执行呢？若无需拆分执行步骤，请直接回答原始问题。"
    assistant_message2_content = 'OpenAI是一家开发和应用友好人工智能的公司...'

    user_question3 = '围绕数据库中的user_payments表，我想要检查该表是否存在缺失值'
    user_message3_content = f"现有用户问题如下：{user_question3}。为了回答这个问题，总共需要分几步来执行呢？若无需拆分执行步骤，请直接回答原始问题。"
    assistant_message3_content = '为了检查user_payments数据集是否存在缺失值...'

    user_question4 = '我想寻找合适的缺失值填补方法，来填补user_payments数据集中的缺失值。'
    user_message4_content = f"现有用户问题如下：{user_question4}。为了回答这个问题，总共需要分几步来执行呢？若无需拆分执行步骤，请直接回答原始问题。"
    assistant_message4_content = '为了找到合适的缺失值填充方法...'

    # 创建包含few-shot示例的新消息对象
    task_decomp_few_shot = messages.copy()
    task_decomp_few_shot.messages_pop(manual=True, index=-1)

    # 添加few-shot示例
    examples = [
        {"role": "user", "content": user_message1_content},
        {"role": "assistant", "content": assistant_message1_content},
        {"role": "user", "content": user_message2_content},
        {"role": "assistant", "content": assistant_message2_content},
        {"role": "user", "content": user_message3_content},
        {"role": "assistant", "content": assistant_message3_content},
        {"role": "user", "content": user_message4_content},
        {"role": "assistant", "content": assistant_message4_content}
    ]

    for example in examples:
        task_decomp_few_shot.messages_append(example)

    # 添加当前用户问题
    user_question = messages.history_messages[-1]["content"]
    new_question = f"现有用户问题如下：{user_question}。为了回答这个问题，总共需要分几步来执行呢？若无需拆分执行步骤，请直接回答原始问题。"
    question_message = messages.history_messages[-1].copy()
    question_message["content"] = new_question
    task_decomp_few_shot.messages_append(question_message)

    return task_decomp_few_shot


def modify_prompt(messages, action='add', enable_md_output=True, enable_COT=True):
    """
    修改消息中的提示模板
    :param messages: MessageManager对象，包含当前对话消息
    :param action: 'add'或'remove'，决定是添加还是移除提示
    :param enable_md_output: 是否启用markdown格式输出
    :param enable_COT: 是否启用COT提示
    :return: 修改后的MessageManager对象
    """
    # 定义提示模板
    cot_prompt = "请一步步思考并得出结论。"
    md_prompt = "任何回答都请以markdown格式进行输出。"

    if action == 'add':
        if enable_COT:
            if type(messages.messages[-1]) is openai.types.chat.chat_completion_message.ChatCompletionMessage:
                messages.messages[-1].content += cot_prompt
                messages.history_messages[-1].content += cot_prompt
            else:
                messages.messages[-1]["content"] += cot_prompt
                messages.history_messages[-1]["content"] += cot_prompt

        if enable_md_output:
            if type(messages.messages[-1]) is openai.types.chat.chat_completion_message.ChatCompletionMessage:
                messages.messages[-1].content += md_prompt
                messages.history_messages[-1].content += md_prompt
            else:
                messages.messages[-1]["content"] += md_prompt
                messages.history_messages[-1]["content"] += md_prompt

    elif action == 'remove':
        if enable_md_output:
            if type(messages.messages[-1]) is openai.types.chat.chat_completion_message.ChatCompletionMessage:
                messages.messages[-1].content = messages.messages[-1].content.replace(md_prompt, "")
                messages.history_messages[-1].content = messages.history_messages[-1].content.replace(md_prompt, "")
            else:
                messages.messages[-1]["content"] = messages.messages[-1]["content"].replace(md_prompt, "")
                messages.history_messages[-1]["content"] = messages.history_messages[-1]["content"].replace(md_prompt,
                                                                                                            "")

        if enable_COT:
            if type(messages.messages[-1]) is openai.types.chat.chat_completion_message.ChatCompletionMessage:
                messages.messages[-1].content = messages.messages[-1].content.replace(cot_prompt, "")
                messages.history_messages[-1].content = messages.history_messages[-1].content.replace(cot_prompt, "")
            else:
                messages.messages[-1]["content"] = messages.messages[-1]["content"].replace(cot_prompt, "")
                messages.history_messages[-1]["content"] = messages.history_messages[-1]["content"].replace(cot_prompt,
                                                                                                            "")

    return messages


# ==================================================
# 核心对话函数区域
# ==================================================

def get_first_response(model, messages, available_functions=None, is_developer_mode=False, is_expert_mode=False):
    """
    获取模型的初始响应
    :param model: 模型名称
    :param messages: MessageManager对象，包含当前对话消息
    :param available_functions: AvailableFunctions对象，包含可用函数信息
    :param is_developer_mode: 是否启用开发者模式
    :param is_expert_mode: 是否启用专家模式
    :return: 模型的响应消息
    """
    # 修改提示模板
    if is_developer_mode:
        messages = modify_prompt(messages, action='add')

    # 添加任务分解提示
    if is_expert_mode:
        messages = add_task_decomposition_prompt(messages)

    # 尝试获取模型响应
    while True:
        try:
            if available_functions is None:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages.messages)
            else:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages.messages,
                    tools=available_functions.functions,
                    tool_choice=available_functions.function_call)
            break

        except AuthenticationError as e:
            # 处理认证错误
            if is_expert_mode:
                msg_temp = messages.copy()
                question = msg_temp.messages[-1]["content"]
                new_prompt = f"以下是用户提问：{question}。该问题有些复杂，且用户意图并不清晰。请编写一段话，来引导用户重新提问。"

                try:
                    msg_temp.messages[-1]["content"] = new_prompt
                    response = client.chat.completions.create(
                        model=model,
                        messages=msg_temp.messages)

                    display(Markdown(response.choices[0].message.content))
                    print(response.choices[0].message.content)

                    user_input = input("请重新输入问题，输入'退出'可以退出当前对话")
                    if user_input == "退出":
                        print("当前模型无法返回结果，已经退出")
                        return None
                    else:
                        messages.history_messages[-1]["content"] = user_input
                        return get_first_response(model, messages, available_functions, is_developer_mode,
                                                  is_expert_mode)

                except AuthenticationError:
                    print(f"当前遇到了一个链接问题: {str(e)}")
                    print("由于Limit Rate限制，即将等待1分钟后继续运行...")
                    time.sleep(60)
                    print("已等待60秒，即将开始重新调用模型并进行回答...")

            else:
                print(f"当前遇到了一个链接问题: {str(e)}")
                if is_developer_mode:
                    user_input = input("请选择等待1分钟（1），或者更换模型（2），或者报错退出（3）")
                    if user_input == '1':
                        print("好的，将等待1分钟后继续运行...")
                        time.sleep(60)
                        print("已等待60秒，即将开始新的一轮问答...")
                    elif user_input == '2':
                        model = input("好的，请输出新模型名称")
                    else:
                        raise e
                else:
                    print("由于Limit Rate限制，即将等待1分钟后继续运行...")
                    time.sleep(60)
                    print("已等待60秒，即将开始重新调用模型并进行回答...")

    # 还原提示模板
    if is_developer_mode:
        messages = modify_prompt(messages, action='remove')

    return response.choices[0].message


def function_to_call(available_functions, function_call_message):
    """
    调用外部函数并返回结果
    :param available_functions: AvailableFunctions对象，包含可用函数信息
    :param function_call_message: 包含函数调用信息的消息
    :return: 函数调用结果的消息
    """
    tool_call = function_call_message.tool_calls[0]
    function_name = tool_call.function.name
    fuction_to_call = available_functions.functions_dic[function_name]
    function_args = json.loads(tool_call.function.arguments)

    try:
        function_args['g'] = globals()
        function_response = fuction_to_call(**function_args)
    except Exception as e:
        function_response = "函数运行报错如下:" + str(e)

    function_response_messages = {
        "tool_call_id": tool_call.id,
        "role": "tool",
        "name": function_name,
        "content": function_response,
    }

    return function_response_messages


# ==================================================
# 高级对话管理函数区域
# ==================================================

def one_chat_response(model, messages, available_functions=None, is_developer_mode=False,
                      is_expert_mode=False, delete_some_messages=False, is_task_decomposition=False):
    """
    处理单轮对话响应
    :param model: 模型名称
    :param messages: MessageManager对象，包含当前对话消息
    :param available_functions: AvailableFunctions对象，包含可用函数信息
    :param is_developer_mode: 是否启用开发者模式
    :param is_expert_mode: 是否启用专家模式
    :param delete_some_messages: 是否删除部分消息
    :param is_task_decomposition: 是否是任务分解
    :return: 更新后的MessageManager对象
    """
    if not is_task_decomposition:
        response_message = get_first_response(model, messages, available_functions,
                                              is_developer_mode, is_expert_mode)

    if is_task_decomposition or (is_expert_mode and response_message.tool_calls):
        is_task_decomposition = True
        task_decomp_few_shot = add_task_decomposition_prompt(messages)
        response_message = get_first_response(model, task_decomp_few_shot, available_functions,
                                              is_developer_mode, is_expert_mode)
        if response_message.tool_calls:
            print("当前任务无需拆解，可以直接运行。")

    if delete_some_messages:
        for i in range(delete_some_messages):
            messages.messages_pop(manual=True, index=-1)

    if not response_message.tool_calls:
        messages = handle_text_response(model, messages, response_message, available_functions,
                                        is_developer_mode, is_expert_mode, delete_some_messages,
                                        is_task_decomposition)
    elif response_message.tool_calls:
        messages = handle_code_response(model, messages, response_message, available_functions,
                                        is_developer_mode, is_expert_mode, delete_some_messages)

    return messages


def handle_code_response(model, messages, function_call_message, available_functions=None,
                         is_developer_mode=False, is_expert_mode=False, delete_some_messages=False):
    """
    处理代码响应
    :param model: 模型名称
    :param messages: MessageManager对象，包含当前对话消息
    :param function_call_message: 包含函数调用信息的消息
    :param available_functions: AvailableFunctions对象，包含可用函数信息
    :param is_developer_mode: 是否启用开发者模式
    :param is_expert_mode: 是否启用专家模式
    :param delete_some_messages: 是否删除部分消息
    :return: 更新后的MessageManager对象
    """

    def convert_to_markdown(code, language):
        return f"```{language}\n{code}\n```"

    try:
        code_dict = json.loads(function_call_message.tool_calls[0].function.arguments)
    except Exception as e:
        print("json字符解析错误，正在重新创建代码...")
        return one_chat_response(model, messages, available_functions, is_developer_mode,
                                 is_expert_mode, delete_some_messages)

    if code_dict.get('sql_query'):
        markdown_code = convert_to_markdown(code_dict['sql_query'], 'sql')
    elif code_dict.get('py_code'):
        markdown_code = convert_to_markdown(code_dict['py_code'], 'python')
    else:
        markdown_code = code_dict

    display(Markdown(markdown_code))
    print(markdown_code)

    if is_developer_mode:
        user_input = input("是直接运行代码（1），还是反馈修改意见，并让模型对代码进行修改后再运行（2）")
        if user_input != '1':
            modify_input = input("好的，请输入修改意见：")
            messages.messages_append(function_call_message)
            messages.messages_append({"role": "user", "content": modify_input})
            return one_chat_response(model, messages, available_functions, is_developer_mode,
                                     is_expert_mode, 2)

    function_response_message = function_to_call(available_functions, function_call_message)
    return check_function_response(model, messages, function_call_message, function_response_message,
                                   available_functions, is_developer_mode, is_expert_mode, delete_some_messages)


def check_function_response(model, messages, function_call_message, function_response_message,
                            available_functions=None, is_developer_mode=False, is_expert_mode=False,
                            delete_some_messages=False):
    """
    检查函数响应
    :param model: 模型名称
    :param messages: MessageManager对象，包含当前对话消息
    :param function_call_message: 包含函数调用信息的消息
    :param function_response_message: 包含函数响应信息的消息
    :param available_functions: AvailableFunctions对象，包含可用函数信息
    :param is_developer_mode: 是否启用开发者模式
    :param is_expert_mode: 是否启用专家模式
    :param delete_some_messages: 是否删除部分消息
    :return: 更新后的MessageManager对象
    """
    fun_res_content = function_response_message["content"]

    if "报错" in fun_res_content:
        print(fun_res_content)

        if not is_expert_mode:
            display(Markdown("**即将执行高效debug，正在实例化Efficient Debug Agent...**"))
            print("**即将执行高效debug，正在实例化Efficient Debug Agent...**")
            debug_prompt_list = ['你编写的代码报错了，请根据报错信息修改代码并重新执行。']
        else:
            display(Markdown(
                "**即将执行深度debug，该debug过程将自动执行多轮对话，请耐心等待。正在实例化Deep Debug Agent...**"))
            print("**即将执行深度debug，该debug过程将自动执行多轮对话，请耐心等待。正在实例化Deep Debug Agent...**")
            display(Markdown("**正在实例化deep debug Agent...**"))
            print("**正在实例化deep debug Agent...**")
            debug_prompt_list = ["之前执行的代码报错了，你觉得代码哪里编写错了？",
                                 "好的。那么根据你的分析，为了解决这个错误，从理论上来说，应该如何操作呢？",
                                 "非常好，接下来请按照你的逻辑编写相应代码并运行。"]

        msg_debug = messages.copy()
        msg_debug.messages_append(function_call_message)
        msg_debug.messages_append(function_response_message)

        for debug_prompt in debug_prompt_list:
            msg_debug.messages_append({"role": "user", "content": debug_prompt})
            display(Markdown("**From Debug iQuery Agent:**"))
            print("**From Debug iQuery Agent:**")
            display(Markdown(debug_prompt))
            print(debug_prompt)

            msg_debug = one_chat_response(model, msg_debug, available_functions,
                                          is_developer_mode, False, delete_some_messages)

        return msg_debug
    else:
        print("外部函数已执行完毕，正在解析运行结果...")
        messages.messages_append(function_call_message)
        messages.messages_append(function_response_message)
        return one_chat_response(model, messages, available_functions, is_developer_mode,
                                 is_expert_mode, delete_some_messages)


def handle_text_response(model, messages, text_answer_message, available_functions=None,
                         is_developer_mode=False, is_expert_mode=False, delete_some_messages=False,
                         is_task_decomposition=False):
    """
    处理文本响应
    :param model: 模型名称
    :param messages: MessageManager对象，包含当前对话消息
    :param text_answer_message: 包含文本响应的消息
    :param available_functions: AvailableFunctions对象，包含可用函数信息
    :param is_developer_mode: 是否启用开发者模式
    :param is_expert_mode: 是否启用专家模式
    :param delete_some_messages: 是否删除部分消息
    :param is_task_decomposition: 是否是任务分解
    :return: 更新后的MessageManager对象
    """
    answer_content = text_answer_message.content
    print("模型回答：\n")
    display(Markdown(answer_content))
    print(answer_content)

    user_input = None

    if not is_task_decomposition and is_developer_mode:
        user_input = input(
            "请问是否记录回答结果（1），或者对当前结果提出修改意见（2），或者重新进行提问（3），或者直接退出对话（4）")
        if user_input == '1':
            messages.messages_append(text_answer_message)
            print("本次对话结果已保存")
    elif is_task_decomposition or is_expert_mode:
        user_input = input(
            "请问是否按照该流程执行任务（1），或者对当前执行流程提出修改意见（2），或者重新进行提问（3），或者直接退出对话（4）")
        if user_input == '1':
            messages.messages_append(text_answer_message)
            print("好的，即将逐步执行上述流程")
            messages.messages_append({"role": "user", "content": "非常好，请按照该流程逐步执行。"})
            return one_chat_response(model, messages, available_functions, is_developer_mode,
                                     False, delete_some_messages, False)

    if user_input is not None:
        if user_input == '2':
            new_user_content = input("好的，输入对模型结果的修改意见：")
            print("好的，正在进行修改。")
            messages.messages_append(text_answer_message)
            messages.messages_append({"role": "user", "content": new_user_content})
            return one_chat_response(model, messages, available_functions, is_developer_mode,
                                     is_expert_mode, 2, is_task_decomposition)
        elif user_input == '3':
            new_user_content = input("好的，请重新提出问题：")
            messages.messages[-1]["content"] = new_user_content
            return one_chat_response(model, messages, available_functions, is_developer_mode,
                                     is_expert_mode, delete_some_messages, is_task_decomposition)
        elif user_input == '4':
            print("好的，已退出当前对话")
    else:
        messages.messages_append(text_answer_message)

    return messages
