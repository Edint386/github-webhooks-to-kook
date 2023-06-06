FROM python:3.11-alpine
ARG VERSION
ENV APP_VERSION=$VERSION
WORKDIR /app
RUN #pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "code/main.py"]