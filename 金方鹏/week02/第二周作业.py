# coding:utf8

import torch
import torch.nn as nn
import numpy as np
import random
import json
import matplotlib.pyplot as plt

"""

基于pytorch框架编写模型训练
实现一个自行构造的找规律(机器学习)任务
# 规律：x是一个5维向量，如果第1个数>第5个数，则为正样本，反之为负样本
作业修改：交叉熵，5分类, 找出随机五个数中最大
"""


class TorchModel(nn.Module):
    def __init__(self, input_size):
        super(TorchModel, self).__init__()
        self.linear = nn.Linear(input_size, 5)  # 线性层
        self.loss = nn.CrossEntropyLoss()  # 交叉熵损失函数(内置softmax)
        # self.activation = torch.sigmoid  # sigmoid归一化函数
        # self.loss = nn.functional.mse_loss  # loss函数采用均方差损失

    # 当输入真实标签，返回loss值；无真实标签，返回预测值
    def forward(self, x, y=None):
        y_pred = self.linear(x)  # (batch_size, input_size) -> (batch_size, 1)
        # print(x)
        # return x
        # y_pred = self.activation(x)  # (batch_size, 1) -> (batch_size, 1)
        if y is not None:
            return self.loss(y_pred, y)  # 预测值和真实值计算损失
        else:
            # 对 logits 应用 softmax，转换为概率分布
            y_probabilities = softmax(y_pred)  # 按行进行 softmax
            return y_probabilities  # 输出预测结果


#手写softmax
def softmax(matrix):
    return torch.exp(matrix) / torch.sum(torch.exp(matrix), dim=1, keepdim=True)
# 生成一个样本, 样本的生成方法，代表了我们要学习的规律
# 随机生成一个5维向量，如果第一个值大于第五个值，认为是正样本，反之为负样本

# 修改
# 找出最大

def build_sample():
    x = np.random.random(5)
    label_index = np.argmax(x)  # 最大值索引
    one_hot_target = np.zeros(x.shape)  # one-hot编码[0,0,0,0,0]
    one_hot_target[label_index] = 1  # 真实标签位置 置为1
    # print(x, label_index, one_hot_target)
    return x, one_hot_target
    # if x[0] > x[4]:
    #     return x, 1
    # else:
    #     return x, 0


# 随机生成一批样本
# 正负样本均匀生成
def build_dataset(total_sample_num):
    X = []
    Y = []
    for i in range(total_sample_num):
        x, y = build_sample()
        X.append(x)
        Y.append(y)
    return torch.FloatTensor(X), torch.FloatTensor(Y)


# 测试代码
# 用来测试每轮模型的准确率
def evaluate(model):
    model.eval()
    test_sample_num = 100
    x, y = build_dataset(test_sample_num)
    # print("本次预测集中共有%d个正样本，%d个负样本" % (sum(y), test_sample_num - sum(y)))
    correct, wrong = 0, 0
    with torch.no_grad():  # 禁用梯度计算
        y_pred = model(x)  # 模型预测 model.forward(x)
        y_pred_label = torch.where(y_pred > 0.5, torch.tensor(1.0), torch.tensor(0.0))  # 条件：大于 0.5 为 1，否则为 0
        # y_pred_index = torch.argmax(y_pred, dim=1)  # 按行找出预测最大概率索引
        # print(y_pred, y_pred_index)
        # y_true_index = np.argmax(y)
        for y_p, y_t in zip(y_pred_label, y):  # 与真实标签进行对比
            # print(y_p, y_t)
            if torch.equal(y_p, y_t):  # 判断预测值和真实值是否相等
                correct += 1  # 样本判断正确
            else:
                wrong += 1
    print("正确预测个数：%d, 正确率：%f" % (correct, correct / (correct + wrong)))
    return correct / (correct + wrong)


def main():
    # 配置参数
    epoch_num = 20  # 训练轮数
    batch_size = 25  # 每次训练样本个数
    train_sample = 10000  # 每轮训练总共训练的样本总数
    input_size = 5  # 输入向量维度
    learning_rate = 0.005  # 学习率
    # 建立模型
    model = TorchModel(input_size)
    # 选择优化器
    optim = torch.optim.Adam(model.parameters(), lr=learning_rate)
    log = []
    # 创建训练集，正常任务是读取训练集
    train_x, train_y = build_dataset(train_sample)
    # 训练过程
    for epoch in range(epoch_num):
        model.train()
        watch_loss = []
        for batch_index in range(train_sample // batch_size):    
            x = train_x[batch_index * batch_size : (batch_index + 1) * batch_size] # 切片
            y = train_y[batch_index * batch_size : (batch_index + 1) * batch_size]
            loss = model(x, y)  # 计算loss  model.forward(x,y)
            loss.backward()  # 计算梯度
            optim.step()  # 更新权重
            optim.zero_grad()  # 梯度归零
            watch_loss.append(loss.item())
        print("=========\n第%d轮平均loss:%f" % (epoch + 1, np.mean(watch_loss)))
        acc = evaluate(model)  # 测试本轮模型结果
        log.append([acc, float(np.mean(watch_loss))])
    # 保存模型
    torch.save(model.state_dict(), "model_max.bin")
    # 画图
    print(log)
    plt.plot(range(len(log)), [l[0] for l in log], label="acc")  # 画acc曲线
    plt.plot(range(len(log)), [l[1] for l in log], label="loss")  # 画loss曲线
    plt.legend()
    plt.show()
    return


# 使用训练好的模型做预测
def predict(model_path, input_vec):
    input_size = 5
    model = TorchModel(input_size)
    model.load_state_dict(torch.load(model_path))  # 加载训练好的权重
    # print(model.state_dict())

    model.eval()  # 测试模式
    with torch.no_grad():  # 不计算梯度
        result = model.forward(torch.FloatTensor(input_vec))  # 模型预测
        # print(result)
    for vec, res in zip(input_vec, result):
        # label = torch.round(res).item()
        # print(vec, res)
        # print("输入：%s, 预测类别：%d, 概率值：%f" % (vec, torch.round(res), res))  # 打印结果 round：四舍五入
        pre_label = torch.where(res > 0.5, torch.tensor(1.0), torch.tensor(0.0)) # 条件：大于 0.5 为 1，否则为 0
        print(f"输入：{vec}, 预测类别：{pre_label}, 概率值：{res}")


if __name__ == "__main__":
    main()
    # test_vec = [[0.07889086,0.15229675,0.31082123,0.03504317,0.88920843],
    #             [0.84963533,0.5524256,0.95758807,0.94520434,0.84890681],
    #             [0.00797868,0.67482528,0.13625847,0.34675372,0.19871392],
    #             [0.09349776,0.59416669,0.92579291,0.41567412,0.1358894]]
    # predict("model_max.bin", test_vec)
    # model = TorchModel(5)
    # pre = model.forward(torch.FloatTensor(test_vec))
    # print(np.sum(pre, axis=1))
    # build_sample()
