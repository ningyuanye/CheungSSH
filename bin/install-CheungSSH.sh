#!/bin/bash
#Author=Cheung Kei-Chuen
#QQ群=445342415
#coding:utf-8
V=2.0.1
#如果您在使用过程中，遇到了一点点的问题，我都真诚希望您能告诉我！为了改善这个软件， 方便您的工作#
export LANG=zh_CN.UTF-8
if [ `id -u` -ne 0 ]
then
	echo "Must be as root install!"
	exit 1
fi
echo  "Installing......"
setenforce 0
useradd cheungssh -d /home/cheungssh  -s /sbin/nologin 2>/dev/null #该目录是cheungssh的工作目录， 必须创建
echo "正在复制文件..."
if [ `dirname $0` == "." ]
then
	/bin/cp  -r ../* /home/cheungssh/
	if  [ $? -ne  0 ]
	then
		echo  "复制程序文件失败，请检查相关目录是否存在"
		exit 1
	else
		echo "复制程序文件完成"
	fi
		
else
	/bin/cp  -r `dirname  $(dirname  $0)`/* /home/cheungssh/
	if  [ $? -ne  0 ]
	then
		echo  "复制程序文件失败，请检查相关目录是否存在"
		exit 1
	else
		echo "复制程序文件完成"
	fi
fi
/bin/rm -fr  /home/cheungssh/web/cheungssh 2>/dev/null
cd /home/cheungssh/web/  &&
tar xvf cheungssh.html.bz2
if  [ $? -ne 0 ]
then
	echo  "解压失败"
	exit
fi
mkdir -p /home/cheungssh/keyfile
mkdir -p /home/cheungssh/scriptfile
mkdir -p /home/cheungssh/crond
mkdir -p /home/cheungssh/upload
mkdir -p /home/cheungssh/download
mkdir -p /home/cheungssh/conf
mkdir -p /home/cheungssh/version
mkdir -p /home/cheungssh/pid
mkdir -p /home/cheungssh/logs
mkdir -p /home/cheungssh/data
mkdir -p /home/cheungssh/data/cmd/
mkdir -p /home/cheungssh/web/cheungssh/download/
chmod a+x -R /home/cheungssh/bin/
cat <<EOFver|python
#coding:utf-8
import sys,time
ver=float(sys.version[:3])
if ver<=2.4:
	print "强烈警告! 您使用的python版本过低,建议升级python版本到2.4以上.\n可以使用yum update python更新"
	sys.exit(1)
EOFver
defaultip=`/sbin/ifconfig |grep -v 'inet6'|grep -E '([0-9]{1,3}\.){3}[0-9]{1,3}' -o|grep -vE '^(127|255)|255$'|head -1`
echo "您的服务器IP":
for a in `/sbin/ifconfig |grep -v 'inet6'|grep -E '([0-9]{1,3}\.){3}[0-9]{1,3}' -o|grep -vE '^(127|255)|255$'`
do
	echo  -e "$a"
done
read -p "请输入您的服务器IP地址作为CheungSSH的访问地址: (默认: $defaultip)" ip
ip=${ip:-$defaultip}
read -p  '您需要开启一个HTTP服务来运行CheungSSH的web功能，请您指定HTTP的端口号(默认80) ' port
read -p  "您需要开启一个websocket端口来实时交互命令执行结果，请指定一个端口号(默认1337)" wport
port=${port:-80}
wport=${wport:-1337}
###
IP="$ip:$port"
WIP="$ip:$wport"
echo "正在配置.."
sed -i  "s/112.74.205.171:800/$IP/g"   /home/cheungssh/web/cheungssh/cheungssh.html        &&
sed -i  "s/112.74.205.171:1337/$WIP/g" /home/cheungssh/web/cheungssh/cheungssh.html     &&
sed -i  "s/1337/$wport/g" /home/cheungssh/bin/cheungssh-service.sh                                   &&
sed -i  "s/1337/$wport/g" /home/cheungssh/bin/websocket_server_cheung.py                  
if  [ $? -ne 0 ]
then
	echo  "配置错误"
	exit 1
else
	echo  "完成配置"
fi

##
read -p  "强烈建议您使用yum安装,本地软件包安装极为繁琐 (Enter键继续) " haha
read -p  '是否通过Yum网络安装软件包？(y/n) ' netinstall
netinstall=${netinstall:-y}
echo $netinstall|grep -iE '^n' -q
if [ $? -ne 0 ]
then
	echo  "使用Yum安装..."
	yum install  -y gcc python-devel openssl-devel mysql-devel  swig httpd httpd-devel python-pip libevent-devel 
	if  [ $? -ne 0 ]
	then
		echo "安装失败,重试中...."
		echo  "更新Yum...."
		/bin/cp  -f /home/cheungssh/conf/*repo  /etc/yum.repos.d/
		yum clear all && yum makecache
		echo  "重装yum..."
		yum install  -y gcc python-devel openssl-devel mysql-devel  swig httpd httpd-devel python-pip libevent-devel  --skip-broken
		if  [ $? -ne 0 ]
		then
			echo  "Yum安装又失败了"
			exit 1
		fi
	fi
	if [ `rpm -qa|grep -Eo 'gcc|python-devel|openssl-devel|mysql-devel|swig|httpd|httpd-devel|libevent-devel'|sort|uniq|wc -l` -lt 8 ]
	then
		echo  "更新Yum...."
		/bin/cp  -f /home/cheungssh/conf/*repo  /etc/yum.repos.d/
		yum clear all && yum makecache
		echo  "重装yum..."
		yum install  -y gcc python-devel openssl-devel mysql-devel  swig httpd httpd-devel python-pip libevent-devel --skip-broken
		if [ `rpm -qa|grep -Eo 'gcc|python-devel|openssl-devel|mysql-devel|swig|httpd|httpd-devel|libevent-devel'|sort|uniq|wc -l` -lt 8 ]
		then
			echo "有些包不能安装上...如下:"
			a="gcc python-devel openssl-devel mysql-devel swig httpd httpd-devel libevent-devel"
			for b in $a
			do
				rpm -qa|grep $b
				if  [ $? -ne 0 ]
				then
					echo "$b 不存在"
					exit 1
				fi
			done
			exit
		fi
	fi
	
	which pip
	if [ $? -ne 0 ]
	then
		python /home/cheungssh/soft/get-pip.py
		if [ $? -ne 0 ]
		then
			echo "安装pip失败，尝试第二种方式..."
			pythonv=`echo  "import sys;print sys.version[:3]"|python`
			sh /home/cheungssh/bin/setuptools-0.6c11-py${pythonv}.egg
			if  [ $? -ne 0 ]
			then
				echo "安装setuptools失败"
				exit 1
			fi
			tar xvf  /home/cheungssh/soft/pip-1.3.1.tar.gz  -C  /home/cheungssh/soft/
			if  [ $? -ne 0 ]
			then
				echo "解压失败"
				exit 1
			fi
			cd /home/cheungssh/soft/pip-1.3.1/ && python setup.py install
			if  [ $? -ne 0 ]
			then
				echo "安装pip失败"
				exit 1
			fi
		fi
	fi
	echo "使用pip安装"
	pip install    MySQL-python paramiko hashlib django-redis django-redis-cache  redis   pycrypto-on-pypi  django-cors-headers
	if  [ $? -ne 0 ]
	then
		echo "安装失败,如果错误信息是 time out 可能是您的网络不好导致的，请重试安装即可"
		exit 1
	fi
	echo  "检查paramiko"
	cat<<EOFparamiko|python
import sys,os
try:
	import paramiko
except AttributeError:
	os.system("""sed  -i '/You should rebuild using libgmp/d;/HAVE_DECL_MPZ_POWM_SEC/d'  /usr/lib*/python*/site-packages/Crypto/Util/number.py   /usr/lib*/python*/site-packages/pycrypto*/Crypto/Util/number.py""")
except:
        sys.exit(1)
EOFparamiko
		###
	tar xvf /home/cheungssh/soft/Django-1.4.22.tar.gz -C  /home/cheungssh/soft/
	cd /home/cheungssh/soft/Django-1.4.22 && python setup.py install
	if [ $? -ne 0 ]
	then
		echo "安装Django失败了，请检查是否有GCC环境"
		exit 1
	fi
	###
	echo "开始安装IP库..."
	cd /home/cheungssh/soft/ && tar xvf IP.tgz  && cd IP && python setup.py install
	if [ $? -ne 0 ]
	then
		echo "安装IP库失败,请检查原因"
		exit 1
	fi
		###
		

		##############安装redis
	echo "正在安装redis服务器"
	tar xvf /home/cheungssh/soft/redis-3.0.4.tar.gz -C /home/cheungssh/
	cd /home/cheungssh/redis-3.0.4  &&  make
	if  [ $? -ne 0 ]
	then
		echo "安装redis服务器失败了，请检查原因"
		exit 1
	fi
		##############安装redis

	read -p  'CheungSSH需要数据库支持， 您是否有可用的Mysql服务器?  (yes/no) ' emysql
	emysql=${emysql:-y}
	echo $emysql|grep -iE '^n' -q
	if [ $? -ne 0 ]
	then
		read  -p  '请指定mysql服务器IP : (默认127.0.0.1)' mip
		read -p '请指定mysql登录账户名 (默认root)' musername
		read -p  "请您输入您的mysql登录密码 "  mpassword
		read -p  '请指定mysql端口 (默认3306)' mp
		echo  "测试登录..."
		mip=${mip:-localhost}
		musername=${musername:-root}
		mp=${mp:-3306}
		mcmd="mysql -h${mip} -u${musername}  -p${mpassword} -P${mp}"
		if [[ -z $mpassword ]]
		then
			mysql  -h${mip} -u${musername}  -P${mp}  <<EOF
show databases;
EOF
		else
			mysql  -h${mip} -u${musername}  -p${mpassword} -P${mp}  <<EOF
show databases;
EOF
		fi
		if  [ $? -ne 0 ]
		then
			echo  $mcmd
			echo "登录mysql失败，请检查原因， 比如用户名密码是否正确，服务器端口，IP是否正确"
			exit 1
		else
			echo "Mysql配置正确"
		fi
		sed -i  "s/'USER': 'root'/'USER': '$musername'/g"                /home/cheungssh/mysite//mysite/settings.py  &&
		sed -i  "s/'PASSWORD': 'zhang'/'PASSWORD': '$mpassword'/g"     /home/cheungssh/mysite//mysite/settings.py  &&
		sed -i  "s/'HOST': 'localhost'/'HOST': '$mip'/g"             /home/cheungssh/mysite//mysite/settings.py  &&
		sed -i  "s/'PORT': '3306'/'PORT': '$mp'/g"     /home/cheungssh/mysite//mysite/settings.py
		if  [ $? -ne 0 ]
		then
			echo "Django配置数据库错误，请检查配置"
			exit 1
		fi
	else
		echo "为您自动安装Mysql服务器..."
		yum install mysql-server -y --skip-broken
		if [ $? -ne 0 ]
		then
			echo "安装mysql失败,请检查原因"
			exit 1
		fi
		echo -e "Mysql服务器已经安装完毕\n正在尝试启动Mysql服务器..."
		if [ -f /etc/init.d/mysql ] && [! -f /etc/init.d/mysqld ]
		then
			/bin/mv /etc/init.d/mysql /etc/init.d/mysqld
		fi
		/etc/init.d/mysqld restart
		if  [ $? -ne 0 ]
		then
			echo "启动Mysql失败，请检查原因"
			exit 1
		else
			echo "已经启动Mysql服务器"
		fi
		echo  "修改mysql root的密码为zhang"
		if [ `mysqladmin -uroot password zhang` -ne 0 ]
		then
			echo "修改mysql数据库密码失败，请检查原因，比如初始密码是否不是空的."
			exit 1
		fi
		mip='localhost'
		musername="root"
		mpassword="zhang"
		mp=3306
	fi
	#创建cheungssh数据库
	mysql -uroot -h${mip} -u${musername} -p${mpassword} -P${mp} -e 'create database if not exists cheungssh  default charset utf8'
	if  [ $? -ne 0 ]
	then
		echo "连接数据库错误,请检查原因，端口， 密码， IP是否正确？您是否已经有Mysql服务器？"
		exit 1
	fi
	mysql -uroot -h${mip} -u${musername} -p${mpassword} -P${mp} cheungssh < /home/cheungssh/bin/cheungssh.sql
	if  [ $? -ne 0 ]
	then
		echo "初始化数据库失败，请检查原因"
		exit 1
	else
		echo "初始化数据库完成"
	fi
	########3
	APXS=`which apxs`
	APXS=${APXS:-/usr/sbin/apxs}
	if [ ! -f $APXS ]
	then
		echo  "没有apxs文件"
		exit 1
	fi
	PYTHON=`wich python`
	echo "开始安装mod_python"
	cd /home/cheungssh/soft &&
	tar xvf  mod_python-3.4.1.tgz  &&
	cd  mod_python-3.4.1        &&
	./configure    --with-apxs=$APXS    --with-python=$PYTHON   &&
	make && make install
	if  [ $? -ne 0 ]
	then
		echo "安装mod_python失败，请检查原因"
		exit 1
	fi
	##########
	/bin/cp /home/cheungssh/conf/version.py $(dirname `find   /usr/lib*/python*/site-packages/mod_python  -type f -name version.py`)
	if  [ $? -ne 0 ]
	then
		echo "修改mod_python失败，请检查原因"
		exit 1
	fi
	##########
	/bin/cp  /home/cheungssh/conf/httpd.conf /etc/httpd/conf/httpd.conf
	if  [ $? -ne 0 ]
	then
		echo "复制Apache配置文件失败，请检查原因"
		exit 1
	fi
	sed -i  "/^Listen/d" /etc/httpd/conf/httpd.conf  &&
	echo "Listen $port" >> /etc/httpd/conf/httpd.conf
	if  [ $? -ne 0 ]
	then
		echo "修改配置失败,请检查原因"
		exit 1
	fi
	########3
	chown -R  root.cheungssh /etc/httpd/ 2>/dev/null
	chown -R cheungssh.cheungssh /home/cheungssh
	if [ $? -ne 0 ]
	then
		echo "赋权失败 ，请检查目录是否正确"
		exit
	fi
	sh /home/cheungssh/bin/cheungssh-service.sh start
	if  [ $? -ne 0 ]
	then
		echo  -e "\n\n启动HTTP方式 /home/cheungssh/bin/cheungssh-service.sh start"
		echo "启动CheungSSH失败"
		exit 1
	fi
	clear
	echo  -e "\n\t\t\t强烈建议首选谷歌浏览器登陆! 其次360的极速模式 猎豹,否则不兼容"
	echo -e "\n\t安装CheungSSH完毕，请使用:\n\t用户名:\tcheungssh\n\t密码:\tcheungssh\n\t登录:\thttp://$IP/cheungssh/"
	echo  -e "\n\n启动CheungSSH服务命令:\n\t\t /home/cheungssh/bin/cheungssh-service.sh start"
	###
	exit 
	###############################################yum安装
else
	echo  "抱歉， 目前不支持本地安装，不过您可以查看CheungSSH yum所安装的包和pip安装的软件即可"
	exit 1
fi


##判断是否有paramiko
cat<<EOF|python
import sys
try:
        import paramiko
except AttributeError:
	 os.system("""sed  -i '/You should rebuild using libgmp/d;/HAVE_DECL_MPZ_POWM_SEC/d'  /usr/lib64/python*/site-packages/Crypto/Util/number.py       /usr/lib/python*/site-packages/pycrypto*/Crypto/Util/number.py""")
except:
        sys.exit(1)
EOF
if [ $? -ne 0 ]
then
	
	rpm  -qa|grep gcc -q
	if  [ $? -ne 0 ]
	then
        	echo  "您的系统当前没有gcc环境！,请执行: yum  install -y gcc  安装！"
		exit
	fi
	rpm  -qa|grep python-devel -q
	if [ $? -ne 0 ]
	then
		echo "您的系统没有python-devel包，请手动执行: yum install -y python-devel  安装！"
		read  -p "如果您的系统是编译安装的python-devel，那么无需理会，按下Enter继续,否则请退出安装" a
	fi
        echo "当前没有paramiko"
	cat<<EOFcrypto|python
import sys
try:
	import Crypto
except:
	sys.exit(1)
EOFcrypto
	if [ $? -ne 0 ]
	then
		echo "没有crypto，现在需要安装"
		cd ../soft
		tar xf pycrypto-2.6.1.tar.gz
		cd pycrypto-2.6.1
		python setup.py  install
		if  [ $? -ne 0 ]
		then
			echo "安装pycropto失败，请检查系统是否有GCC编译环境,如果没有gcc环境，请安装: yum  install -y gcc 或者联系Q群:456335218"
			exit
		else
			echo "安装pycropto完成"
			cd ../../bin
		fi
	fi
	echo "开始安装paramiko..."
	cd ../soft
	tar xf paramiko-1.9.0.tar.gz
	cd paramiko-1.9.0
	python setup.py install
	if [ $? -ne 0 ]
	then
		echo "安装paramiko失败，请检查系统是否有gcc环境和python-devel环境，或者联系Q群：456335218"
	else
		echo "安装paramiko完成"
		cd ../../bin
	fi
else
	echo "paramiko已经就绪"
fi
####
cat<<EOFjson|python
#coding:utf-8
import sys
try:
	import json
except:
	sys.exit(1)
EOFjson
if  [ $? -ne 0 ]
then
	echo -e "系统没有json模块，您需要安装json模块!如果您的服务器版本比较低，比如5.5版本以下，那么安装json很可能是困难的,建议您换一个高版本的服务器,如果可以您也可以尝试手动安装json模块\n或者您可以通过更新python版本解决 yum update python"
	echo -e  "警告:\n\t没有json模块的情况下，无法启动web系统!但您可以使用shell版本的CheungSSH\n\t如果您要使用web版本，必须安装json模块"
	read -p "按下Enter继续..." t_tmp
fi
####

cat<<EOFhashlib|python
import sys
try:
	import hashlib
except:
	sys.exit(1)
EOFhashlib
if [ $? -ne 0 ]
then
	echo "系统没有hashlib,正在安装"
	cd ../soft/
	unzip  hashlib-20081119.zip
	cd hashlib-20081119
	python setup.py install
	if [ $? -ne 0 ]
	then
		echo "安装hashlib失败，请检查系统环境"
		exit
	else
		echo "安装hashlib成功"
		cd ../../bin
	fi
fi
	


chmod -R  a+x /home/cheungssh/  
chmod -R  a+x /home/cheungssh/  
/bin/cp -fr ../* ~/cheung/ 2>/dev/null
echo 'PATH=$PATH:~/cheung/bin' >>/etc/profile
. /etc/profile
touch /home/cheungssh/flag/installed
#########################33
echo  "开始安装web组件"
#########################33
cd /home/cheungssh/soft/
tar xvf Django-1.4.22.tar.gz  
cd Django-1.4.22
python setup.py install
if  [ $? -ne 0 ]
then
	echo  "安装Django失败，请检查原因,或者联系CheungSSH"
	exit 1
else
	echo  "Django安装完毕"
fi
#yum install -y python-setuptools  openssl-devel  mysql-devel 
echo  "正在检查python-setuptools..."
rpm  -qa|grep python-setuptools -q
if  [ $? -ne 0 ]
then
	echo  "系统没有python-setuptools，需要安装"
	cd /home/cheungssh/soft
	tar xvf setuptools-18.4.tar.gz
	cd setuptools-18.4
	python setup.py install
	if  [ $? -ne 0 ]
	then
		echo  "安装失败，请检查原因， 或者联系CheungSSH"
		exit 1
	else:
		echo  "安装python-setuptools完毕"
	fi
fi
rpm  -qa|grep  openssl-devel
if  [ $? -ne 0 ]
then
	echo -e "错误!\n\t您的系统没有openssl-devel rpm包,请手动安装:\n\t第一种方式 : http://pkgs.org/download/openssl-devel\n第二种方式: yum install -y openssl-devel"
	exit 1
fi
echo  "正在检查mysql-devel..."
rpm  -qa|grep mysql-devel
if [ $? -ne 0 ]
then
	echo -e "错误!\n\t您的系统没有mysql-devel rpm包,请手动安装:\n\t第一种方式 : http://rpmfind.net/linux/rpm2html/search.php?query=mysql-devel\n\t第二种方式: yum install -y mysql-devel"
	exit 1
fi

echo  "安装mysql-python"
cd /home/cheungssh/soft
unzip  MySQL-python-1.2.5.zip 
cd MySQL-python-1.2.5
python setup.py  install
if  [ $? -ne 0 ]
then
	echo  "安装Mysql-python完毕"
else
	echo  "安装失败,请检查原因或者联系CheungSSH"
	exit 1
fi
echo  "检查mysql数据库"
read -p  "您是否有可以使用的Mysql数据库? (y/n)" mysql
if [ $mysql  == "y" ]
then
	read  -p  "请输入您的Mysql服务器IP " mip
	read -p  "请您输入您的Mysql登录账户名 "  musername
	read -p  "请您输入您的mysql登录密码"  mpassword
	read -p  "请您输入您的mysql端口 "  mp
	echo  "测试登录..."
	mip=${mip:-localhost}
	musername=${musername:-root}
	mp=${mp:-3306}
	mcmd="mysql  -h${mip} -u${musername} -p${mpassword} -P${mp} -e 'show databases;"
	$mcmd
	if [ $? -ne 0 ]
	then
		echo  "mysql登录失败"
		echo $mcmd
	else
		echo  "登录成功"
	fi
else
	echo  "请您手动安装Mysql数据库 后， 继续安装!"
	exit 1
	
fi
#########################33
#########################33
#########################33
