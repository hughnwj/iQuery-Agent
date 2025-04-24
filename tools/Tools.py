# ==================================================
# 导入依赖区域
# ==================================================

import json
import os
import sqlite3

import pandas as pd

# ==================================================
# 全局配置区域
# ==================================================

# 获取项目基础目录路径
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# 设置数据库文件路径
DB_PATH = os.path.join(BASE_DIR, "data", "db", "iquery.db")


# ==================================================
# 数据库操作函数区域
# ==================================================

def sql_inter(sql_query, g='globals()'):
    """
    执行SQL查询并返回结果
    :param sql_query: SQL查询语句字符串，用于查询iquery数据库
    :param g: 全局变量字典，默认为globals()
    :return: 返回JSON格式的查询结果
    """
    connection = sqlite3.connect(DB_PATH)
    try:
        cursor = connection.execute(sql_query)
        results = cursor.fetchall()
    finally:
        connection.close()
    return json.dumps(results)


def extract_data(sql_query, df_name, g='globals()'):
    """
    从数据库提取数据并保存为DataFrame
    :param sql_query: SQL查询语句字符串
    :param df_name: 要创建的DataFrame变量名
    :param g: 全局变量字典，默认为globals()
    :return: 返回操作结果字符串
    """
    connection = sqlite3.connect(DB_PATH)
    globals()[df_name] = pd.read_sql(sql_query, connection)
    return "已成功完成%s变量创建" % df_name


# ==================================================
# Python代码执行函数区域
# ==================================================

def python_inter(py_code, g='globals()'):
    """
    执行Python代码并返回结果
    :param py_code: 要执行的Python代码字符串
    :param g: 全局变量字典，默认为globals()
    :return: 返回执行结果字符串
    """
    # 添加图片对象处理
    py_code = insert_fig_object(py_code)
    global_vars_before = set(globals().keys())
    try:
        exec(py_code, globals())
    except Exception as e:
        return str(e)
    global_vars_after = set(globals().keys())
    new_vars = global_vars_after - global_vars_before
    if new_vars:
        result = {var: globals()[var] for var in new_vars}
        return str(result)
    else:
        try:
            return str(eval(py_code, globals()))
        except Exception as e:
            return "已经顺利执行代码"


# ==================================================
# 绘图辅助函数区域
# ==================================================

def insert_fig_object(code_str, g='globals()'):
    """
    在绘图代码前插入fig对象创建语句
    :param code_str: 原始代码字符串
    :param g: 全局变量字典，默认为globals()
    :return: 返回处理后的代码字符串
    """
    print("开始画图了")
    global fig
    # 检查是否已存在fig对象创建
    if 'fig = plt.figure' in code_str or 'fig, ax = plt.subplots()' in code_str:
        return code_str

    # 定义绘图库别名
    plot_aliases = ['plt.', 'matplotlib.pyplot.', 'plot']
    sns_aliases = ['sns.', 'seaborn.']

    # 查找第一个绘图代码出现位置
    first_plot_occurrence = min(
        (code_str.find(alias) for alias in plot_aliases + sns_aliases if code_str.find(alias) >= 0), default=-1)

    # 如果找到绘图代码则插入fig对象创建
    if first_plot_occurrence != -1:
        plt_figure_index = code_str.find('plt.figure')
        if plt_figure_index != -1:
            closing_bracket_index = code_str.find(')', plt_figure_index)
            modified_str = code_str[:plt_figure_index] + 'fig = ' + code_str[
                                                                    plt_figure_index:closing_bracket_index + 1] + code_str[
                                                                                                                  closing_bracket_index + 1:]
        else:
            modified_str = code_str[:first_plot_occurrence] + 'fig = plt.figure()\n' + code_str[first_plot_occurrence:]
        return modified_str
    else:
        return code_str
