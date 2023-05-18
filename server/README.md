背诵助手
=========

### 后端部署

部署分为三个阶段：

- 搭建环境
- 导入数据
- 运行应用

#### 搭建环境

本背诵助手后台使用window系统搭建。

1、搭建环境分为两步

1. 在电脑上安装 mysql、redis。
2. 电脑上安装处理语音传输信息的ffmpeg.exe软件，并配置好环境变量。 

２、修改 ` .env.sample` 文件为 `.env ` 然后在其中按要求填写自己的 mysql、redis以及语音识别和语音合成api的信息(可使用百度开放平台app)。

３、下载简体版本中文诗词，使用 `git clone https://github.com/Provinm/chinese-poetry-simplified.git` , 将项目的chinese-poetry的文件夹下内容加到server/preparation/var/data/peotry文件夹中

#### 导入数据

环境搭建好之后，进入 `server/preparation` 文件夹中

1. 运行 `python db_create.py ` 建立数据库表
2. 运行  `python db_import.py` 导入数据

第二步导入数据（30万篇古诗词）预计10分钟。

#### 运行应用

导入数据完成之后，回到`server`目录中

运行 `pip3 install -r requirements.txt ` 安装环境依赖。

运行 `python server.py ` 启动后台。

启动前，确认MySQL是否在后台启动、redis是否在后台启动，防火墙是否已经关闭。

这时候打开浏览器访问 `http://localhost:8000/ebrose/pivot?pivot=花` 看到json格式结果，则成功启动。

### 前端启动

接下来为了搭起一个完整的应用，使用前端开发工具打开背诵助手前端frontend文件夹，更改 app.js 中的 host（可使用ipconfig命令行查看本机ip地址来修改），即可运行在模拟器中体验。推荐使用真机调试，语音识别结果更佳。

