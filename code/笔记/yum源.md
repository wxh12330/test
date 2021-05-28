1.离线yum源

	1建立yum中rpm存放的文件夹

	mkdir -p /root/data/yum
	2.下载需要的rpm包到第一步的文件夹中（所有需要的rpm包先下载）

	yum  install   createrepo --downloadonly --downloaddir=/root/data/yum
	3、确保防火墙关闭状态
	4、开始创建yum仓库，在rpm包存放的所在的目录下执行createrepo命令。
	
	createrepo /root/data/yum/
	
	5、在/etc/yum.repos.d目录下创建配置文件。将此目录下的repo包备份一下，创建自定义的repo包
	cat CentOS-Wxh.repo 
	[CentOS-Wxh]
	name=centos yum repo
	baseurl=file:///root/data/yum
	enabled=1
	gpgcheck=0
	
	执行 yum clean all
	     yum makecache
	我们还可以这样子检测是否使用了本地yum源 ：yum repolist


	注意：将本地制作的yum源放到另一台服务器上时，将/root/data/yum下的文件打包到另一台服务器，并解压到，如/home/tmp  ,重新配置/etc/yum.repo.d/下的目录为/home/tmp,执行yum clean all ,通过yun install XXX 安装所需的文件，，然后将备份的repo文件恢复，执行yum clean all



安装本地第三方库的命令

	*pip install --no-index --find-links=files:"安装包路径如./" "安装包名称"