
	1.	安装virtualenv
		pip3 install virtualenv
	2. 创建目录
		mkdir myproject
		cd myproject

	3.创建虚拟环境：
		virtualenv -p python3 env_1

	4.进入虚拟环境：
		source env_1/bin/activate
	5.查看该虚拟环境下，安装了哪些Python包
		pip list
	6.退出当前的虚拟环境，
		使用deactivate命令：
	
 	7.查看当下有多少个虚拟环境：
		workon+空格+按两次Tab键