1.`__len__()`方法，返回元素的个数，如`print("123456".__len__()):值为6`
2.读取`ini配置文件`：格式```
	[user]
	user_name = Mr,X
	password = 222
	[connect]
	ip = 127.0.0.1
	port = 4723`	可使用`configparser模块`进行读取。