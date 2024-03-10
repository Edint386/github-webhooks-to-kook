#!/bin/bash

# 定义函数
function create_files() {
  # 创建 code/config 目录
  mkdir -p "code/config"

  # 创建 config.json 文件
  cat > "code/config/config.json" << EOF
{
    "token": "kook-bot-websocket-token"
}
EOF

  # 创建 code/log 目录
  mkdir -p "code/log"

  # 创建四个空的 json 文件
  for file in repo_setting.json guild_setting.json did_temp.json secret.json; do
    echo "{}" > "code/log/$file"
  done
}

# 调用函数
create_files

echo "Kook Bot 所需文件已创建完毕！"

