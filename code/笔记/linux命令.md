1.添加ftp用户:`useradd -m -d /home/test -s /bin/sh -g root test`,修改密码:`passwd test`
2.Linux 删除指定时间前的文件：
* 显示20分钟前的文件:
	`find 目录 -type f -mmin +20 -exec ls -l {} \;`
* 删除20分钟前的文件
	`find 目录 -type f -mmin +20 -exec rm {} \;`

* 显示20天前的文件
	`find 目录 -type f -mtime +20 -exec ls -l {} \;`

* 删除20天前的文件
	`find 目录 -type f -mtime +20 -exec rm {} \;`
* -mtime -n +n 按照文件的更改时间来查找文件， - n表示文件更改时间距现在n天以内，+ n表示文件更改时间距现在n天以前。
* -type 查找某一类型的文件，诸如：b - 块设备文件，d - 目录，c - 字符设备文件，p - 管道文件，l - 符号链接文件，f - 普通文件


3.Linux系统中`ll命令`显示内容日期格式:
* 临时修改:`ll -rt --time-style="+%Y-%m-%d %H:%M:%S"`,,`export TIME_STYLE='+%Y-%m-%d %H:%M:%S' `
* 永久生效:`sudo echo "export TIME_STYLE='+%Y-%m-%d %H:%M:%S'" >> /etc/profile && source /etc/profile`