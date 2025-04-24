# iQuery-Agent
## 0.环境配置
```bash
git clone https://github.com/hughnwj/iQuery-Agent.git
cd iQuery-Agent
conda create -n iQuery python=3.10
conda activate iQuery
pip install -r requirements.txt
```
## 1.数据处理
数据预处理：将数据集转变为csv文件，将csv文件插入sqlite数据库
```bash
python data/dataset_handle.py
```
## 2.代码运行
```bash
python main.py
```