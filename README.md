linux系统专用。

可有效解决emby等tmdb域名污染问题

通过自动通过【http://api.ip33.com/dns/resolver】网站解析tmdb，fanart，github等域名对应的IP。

自动在本机/etc/hosts文件下追加解析新的ip，只修改追加的域名，原有的hosts文件内容不会修改。

在本机hosts文件追加同时可以自动追加本机的docker容器内的hosts文件，解决容器内hosts域名污染问题。（请自行替换 Docker容器ID列表）

可以自行设置定时任务，定时更新hosts文件。

执行方式：

1.将change_TMDB_HOST.py下载到本地。

2.安装python3.8

3.运行以下命令替换：

python3.8 change_TMDB_HOST.py
