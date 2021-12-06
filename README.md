# yugioh-db-spider

本项目是游戏王官方卡片数据库的爬虫，爬取卡片信息和faq信息，在官方网页更新时会保留历史版本。

本项目运行前需要依赖：

mysql, docker, docker-compose

确认以上依赖都已满足，git clone本项目后，需要新建config.yml文件，把这个文件路径复制到docker-compose.yml文件内，替换掉volumes下冒号左侧的`./config.yml`部分，文件内容可以参照configs/config路径下的example-config.yml文件，MYSQL_URI需要设置为你自己的mysql路径。如果有代理，可以设置PROXIES为你的代理地址；如果没有，请改为空或者删去这一行，比如这样：

```
PROXIES: ''
```

然后运行：

```
docker build -t yugioh-db-spider .
```

接着运行：

```
docker-compose -f docker-compose.yml up
```
就会开始运行了。

程序启动时会检查你的数据库，如果没有对应的表，会自动创建需要的表。

如果需要后台常驻运行，Ctrl+C结束当前程序后，运行：

```
docker-compose -f docker-compose.yml down
```

接着运行：

```
docker-compose -f docker-compose.yml up -d
```

即可。
