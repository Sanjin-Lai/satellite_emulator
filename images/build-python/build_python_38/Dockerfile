FROM ubuntu-modified:latest
## 将Python-3.6.9 拷贝解压缩
COPY ./resources/Python-3.8.0.tgz /


RUN tar xvf Python-3.8.0.tgz \
    && cd Python-3.8.0 && ./configure && make -j64 && make install \
    && cd .. \
    && rm -rf Python-3.8.0.tgz \
    && ln -s /usr/local/bin/python3 /usr/bin/python \
    && ln -s /usr/local/bin/pip3 /usr/bin/pip # 将pip3 替换为 pip

RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 拷贝配置文件
COPY ./resources/requirements.txt /

#ENV http_proxy "http://172.17.0.1:7890"
#ENV HTTP_PROXY "http://172.17.0.1:7890"
#ENV https_proxy "http://172.17.0.1:7890"
#ENV HTTPS_PROXY "http://172.17.0.1:7890"

RUN python -m pip install --upgrade pip \
    && pip install -r requirements.txt --verbose