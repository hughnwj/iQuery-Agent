from action.iQueryAgent import *
from tools.Tools import *
from tools.AvailableFunctions import *
from memory.CloudFile import *

with open('data/md/iquery数据字典.md', 'r', encoding='utf-8') as f:
    data_dictionary = f.read()

af = AvailableFunctions(functions_list=[sql_inter, extract_data, python_inter])
pj=CloudFile(project_name="测试案例",part_name="测试分析")
iquery = iQueryAgent(api_key="gpt-3.5-turbo",
                     system_content_list=[data_dictionary],
                       available_functions=af,project=pj)
iquery.chat()
iquery.upload_messages()