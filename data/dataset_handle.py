# ==================================================
# 导入依赖区域
# ==================================================

import os
import sqlite3

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


# ==================================================
# 数据处理函数区域
# ==================================================

def process_data():
    """
    主数据处理函数，执行完整的数据处理流程
    包括：读取原始数据、划分训练测试集、特征提取、数据增强、保存处理结果
    无参数
    无返回值
    """
    # 读取原始数据集
    dataset = pd.read_csv('dataset/WA_Fn-UseC_-Telco-Customer-Churn.csv')
    pd.set_option('max_colwidth', 200)

    # 将数据集分割为训练集和测试集
    train_data, test_data = train_test_split(dataset, test_size=0.20, random_state=42)
    train_data = train_data.reset_index(drop=True)
    test_data = test_data.reset_index(drop=True)

    def extract_data(data, features):
        """
        从数据集中提取指定特征列
        :param data: 原始数据集
        :param features: 需要提取的特征列名列表
        :return: 包含customerID和指定特征列的DataFrame
        """
        return data[['customerID'] + features]

    # 提取训练集各维度特征
    user_demographics_train = extract_data(train_data, ['gender', 'SeniorCitizen', 'Partner', 'Dependents'])
    user_services_train = extract_data(train_data, ['PhoneService', 'MultipleLines', 'InternetService',
                                                    'OnlineSecurity', 'OnlineBackup', 'DeviceProtection',
                                                    'TechSupport', 'StreamingTV', 'StreamingMovies'])
    user_payments_train = extract_data(train_data, ['Contract', 'PaperlessBilling', 'PaymentMethod',
                                                    'MonthlyCharges', 'TotalCharges'])
    user_churn_train = extract_data(train_data, ['Churn'])

    # 提取测试集各维度特征
    user_demographics_test = extract_data(test_data, ['gender', 'SeniorCitizen', 'Partner', 'Dependents'])
    user_services_test = extract_data(test_data, ['PhoneService', 'MultipleLines', 'InternetService',
                                                  'OnlineSecurity', 'OnlineBackup', 'DeviceProtection',
                                                  'TechSupport', 'StreamingTV', 'StreamingMovies'])
    user_payments_test = extract_data(test_data, ['Contract', 'PaperlessBilling', 'PaymentMethod',
                                                  'MonthlyCharges', 'TotalCharges'])
    user_churn_test = extract_data(test_data, ['Churn'])

    # 对训练集进行数据增强处理
    np.random.seed(42)

    # 随机删除5%的人口统计数据
    drop_indices = np.random.choice(user_demographics_train.index,
                                    size=int(0.05 * len(user_demographics_train)),
                                    replace=False)
    user_demographics_train = user_demographics_train.drop(drop_indices)

    # 添加100个新用户服务记录
    new_ids = [f"NEW{i}" for i in range(100)]
    user_services_train = pd.concat([
        user_services_train,
        pd.DataFrame({'customerID': new_ids})
    ], ignore_index=True)

    # 在支付数据中随机添加100个缺失值
    for _ in range(100):
        row_idx = np.random.randint(user_payments_train.shape[0])
        col_idx = np.random.randint(1, user_payments_train.shape[1])
        user_payments_train.iat[row_idx, col_idx] = np.nan

    # 添加50个新用户流失记录
    new_ids_churn = [f"NEWCHURN{i}" for i in range(50)]
    user_churn_train = pd.concat([
        user_churn_train,
        pd.DataFrame({'customerID': new_ids_churn, 'Churn': ['Yes'] * 25 + ['No'] * 25})
    ], ignore_index=True)

    # 确保输出目录存在
    if not os.path.exists('csv'):
        os.makedirs('csv')

    # 保存处理后的训练集数据
    user_demographics_train.to_csv('csv/user_demographics_train.csv', index=False)
    user_services_train.to_csv('csv/user_services_train.csv', index=False)
    user_payments_train.to_csv('csv/user_payments_train.csv', index=False)
    user_churn_train.to_csv('csv/user_churn_train.csv', index=False)

    # 保存测试集数据
    user_demographics_test.to_csv('csv/user_demographics_test.csv', index=False)
    user_services_test.to_csv('csv/user_services_test.csv', index=False)
    user_payments_test.to_csv('csv/user_payments_test.csv', index=False)
    user_churn_test.to_csv('csv/user_churn_test.csv', index=False)

    # 将数据导入SQLite数据库
    import_to_sqlite()


# ==================================================
# 数据库操作函数区域
# ==================================================

def import_to_sqlite():
    """
    将CSV数据导入SQLite数据库
    创建数据库表结构并将处理后的数据导入对应表
    无参数
    无返回值
    """
    # 确保输出目录存在
    if not os.path.exists('db'):
        os.makedirs('db')

    # 连接数据库
    conn = sqlite3.connect('db/iquery.db')
    cursor = conn.cursor()

    # 创建所有数据表
    create_tables_sql = """
    CREATE TABLE IF NOT EXISTS user_demographics (
        customerID VARCHAR(255) PRIMARY KEY,
        gender VARCHAR(255),
        SeniorCitizen INT,
        Partner VARCHAR(255),
        Dependents VARCHAR(255)   
    );

    CREATE TABLE IF NOT EXISTS user_demographics_new (
        customerID VARCHAR(255) PRIMARY KEY,
        gender VARCHAR(255),
        SeniorCitizen INT,
        Partner VARCHAR(255),
        Dependents VARCHAR(255)   
    );

    CREATE TABLE IF NOT EXISTS user_services (
        customerID VARCHAR(255) PRIMARY KEY,
        PhoneService VARCHAR(255),
        MultipleLines VARCHAR(255),
        InternetService VARCHAR(255),
        OnlineSecurity VARCHAR(255),
        OnlineBackup VARCHAR(255),
        DeviceProtection VARCHAR(255),
        TechSupport VARCHAR(255),
        StreamingTV VARCHAR(255),
        StreamingMovies VARCHAR(255) 
    );

    CREATE TABLE IF NOT EXISTS user_services_new (
        customerID VARCHAR(255) PRIMARY KEY,
        PhoneService VARCHAR(255),
        MultipleLines VARCHAR(255),
        InternetService VARCHAR(255),
        OnlineSecurity VARCHAR(255),
        OnlineBackup VARCHAR(255),
        DeviceProtection VARCHAR(255),
        TechSupport VARCHAR(255),
        StreamingTV VARCHAR(255),
        StreamingMovies VARCHAR(255) 
    );

    CREATE TABLE IF NOT EXISTS user_payments (
        customerID VARCHAR(255) PRIMARY KEY,
        Contract VARCHAR(255),
        PaperlessBilling VARCHAR(255),
        PaymentMethod VARCHAR(255),
        MonthlyCharges FLOAT,
        TotalCharges VARCHAR(255)
    );

    CREATE TABLE IF NOT EXISTS user_payments_new (
        customerID VARCHAR(255) PRIMARY KEY,
        Contract VARCHAR(255),
        PaperlessBilling VARCHAR(255),
        PaymentMethod VARCHAR(255),
        MonthlyCharges FLOAT,
        TotalCharges VARCHAR(255)
    );

    CREATE TABLE IF NOT EXISTS user_churn (
        customerID VARCHAR(255) PRIMARY KEY,
        Churn VARCHAR(255)
    );

    CREATE TABLE IF NOT EXISTS user_churn_new (
        customerID VARCHAR(255) PRIMARY KEY,
        Churn VARCHAR(255)
    );
    """

    cursor.executescript(create_tables_sql)

    def import_csv_to_table(csv_file, table_name):
        """
        将CSV文件数据导入到指定数据库表
        :param csv_file: CSV文件路径
        :param table_name: 目标表名
        无返回值
        """
        df = pd.read_csv(csv_file)
        df.to_sql(table_name, conn, if_exists='append', index=False)

    # 导入训练集数据到主表
    import_csv_to_table('csv/user_demographics_train.csv', 'user_demographics')
    import_csv_to_table('csv/user_services_train.csv', 'user_services')
    import_csv_to_table('csv/user_payments_train.csv', 'user_payments')
    import_csv_to_table('csv/user_churn_train.csv', 'user_churn')

    # 导入测试集数据到新表
    import_csv_to_table('csv/user_demographics_test.csv', 'user_demographics_new')
    import_csv_to_table('csv/user_services_test.csv', 'user_services_new')
    import_csv_to_table('csv/user_payments_test.csv', 'user_payments_new')
    import_csv_to_table('csv/user_churn_test.csv', 'user_churn_new')

    # 提交事务并关闭连接
    conn.commit()
    conn.close()

    print("数据已成功导入SQLite数据库")


# ==================================================
# 主程序入口区域
# ==================================================

def main():
    """
    程序主入口
    调用process_data()函数执行数据处理流程
    无参数
    无返回值
    """
    process_data()


if __name__ == "__main__":
    main()
