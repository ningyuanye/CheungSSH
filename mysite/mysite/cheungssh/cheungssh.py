#coding:utf-8
from django.http import  HttpResponse,HttpResponseRedirect
from django.shortcuts import render_to_response
from django.contrib.auth import authenticate,login,logout
from mysite.cheungssh.models import ServerConf
import FileTransfer,path_search,crond_record
import sys,os,json,random,commands,queue_task,time,threading
sys.path.append('/home/cheungssh/bin')
import IP,hwinfo,DataConf,ssh_check
import cheungssh_web,login_check
upload_dir="/home/cheungssh/upload"
keyfiledir="/home/cheungssh/keyfile"
scriptfiledir="/home/cheungssh/scriptfile"
reload(sys)
sys.setdefaultencoding('utf8')
from django.core.cache import cache
from django.views.generic.base import View 
import login_check
import db_to_redis_allconf
crond_file="/home/cheungssh/crond/crond_file"
cmdfile="/home/cheungssh/data/cmd/cmdfile"
def cheungssh_index(request):
	return render_to_response("cheungssh.html")
def cheungssh_login(request):
	info={"msgtype":"ERR","content":"","auth":"no"}
	client_ip=request.META['REMOTE_ADDR']
	print '登录:',client_ip
	try:
		print IP.find(client_ip)
	except Exception,e:
		print '不能解析IP'
	limit_ip='fail.limit.%s'%(client_ip)
	if cache.has_key(limit_ip):
		if cache.get(limit_ip)>4:
			print '该用户IP已经被锁定'
			info['content']="无效登陆"
			cache.incr(limit_ip)
			cache.expire(limit_ip,8640000)
			info=json.dumps(info)
			return HttpResponse(info)
	if request.method=="POST":
		username = request.POST.get("username", False)
		password = request.POST.get("password", False)
		print username,password,request.POST
		user=authenticate(username=username,password=password)
		if user is not None:
			if user.is_active:
				print "成功登陆"
				login(request,user)
				request.session["username"]=username
				info["msgtype"]="OK"
				info['auth']="yes"
				request.session.set_expiry(0)
				if cache.has_key(limit_ip):cache.delete(limit_ip)
				print request.COOKIES,request.session.keys(),request.session['_auth_user_id']
				info['sid']=str(request.session.session_key)
			else:
				
				info["content"]="用户状态无效"
				print info["content"]
		else:
			if cache.has_key(limit_ip):
				cache.incr(limit_ip)
			else:
				cache.set(limit_ip,1,3600)
			info["content"]="用户名或密码错误"
			print info["content"]
			
			
	else:
		try:
			info["content"]="No Get"
		except Exception,e:
			print '错误',e
	info=json.dumps(info)
	response=HttpResponse(info)
	response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "POST"
        response["Access-Control-Allow-Credentials"] = "true"
        return response
	info=json.dumps(info)
	print info
	return HttpResponse(info)
def cheungssh_logout(request):
	info={'msgtype':'OK'}
	if request.user.is_authenticated():
		logout(request)
	info=json.dumps(info)
	callback=request.GET.get('callback')
	if callback is None:
		backstr=info
	else:
		backstr="%s(%s)"  % (callback,info)
	return HttpResponse(backstr)
@login_check.login_check()
def download_file(request):
	info={"msgtype":"ERR","content":""}
	file=request.GET.get('file')
	callback=request.GET.get('callback')
	try:
		file=eval(file)
		if not  type([])==type(file):
			info['content']='传入的参数不是一个[]'
		else:
			info['msgtype']='OK'
	except Exception,e:
		info["content"]="传入的参数不是一个json格式"
	downfile="%s.tar.gz" %str(random.randint(90000000000000000000,99999999999999999999))
	cmd="tar zcf  /home/cheungssh/download/%s  " % downfile +  " ".join(file)
	print cmd
	T=commands.getstatusoutput(cmd)
	if not  T[0]==0:
		info['content']=T[1]
		info['msgtype']='ERR'
		os.system("/bin/rm %s" % downfile)
	else:
		info["msgtype"]='OK'
		server_head=request.META['HTTP_HOST']
		info["url"]="http://%s/cheungssh/download/file/%s" % (server_head,downfile)
		



	info=json.dumps(info,encoding='utf-8',ensure_ascii=False)
	if callback is None:
		backstr=info
	else:
		backstr="%s(%s)"  % (callback,info)
	return HttpResponse(backstr)

	
@login_check.login_check()
def keyshow(request):
	info={"msgtype":"ERR","content":""}
	callback=request.GET.get('callback')
	show_type=request.GET.get('show_type')
	try:
		content=cache.get('keyfilelog')
		if content:
			content=content.values()
		else:
			content=[]
		print content,77777777777
		if show_type=='list':
			keyfile_list={}
			for a in content:
				keyfile_list[a['fid']]=a['filename']
			info['content']=keyfile_list
		else:
			info["content"]=content
		info['msgtype']="OK"
	except Exception,e:
		info["content"]=str(e)
		print e
	info=json.dumps(info)
	if callback is None:
		backstr=info
	else:
		backstr="%s(%s)"  % (callback,info)
	return HttpResponse(backstr)
@login_check.login_check()
def delkey(request):
	info={"msgtype":"ERR","content":"","path":""}
	callback=request.GET.get('callback')
	fid=request.GET.get('fid')
	try:
		alllogline=cache.get("keyfilelog")
		if alllogline:
			keyfile=os.path.join(keyfiledir,alllogline[fid]['filename'])
			try:
				os.remove(keyfile)
			except:
				pass
			del alllogline[fid]
			cache.set('keyfilelog',alllogline,3600000)
			info["msgtype"]="OK"
	except Exception,e:
		info["content"]=str(e)
	info=json.dumps(info,encoding='utf-8',ensure_ascii=False)
	if callback is None:
		backstr=info
	else:
		backstr="%s(%s)"  % (callback,info)
	return HttpResponse(backstr)
		
#@login_check.login_check()
def upload_file_test(request):
	fid=str(random.randint(90000000000000000000,99999999999999999999))
	info={"msgtype":"ERR","content":"","path":""}
	upload_type=request.GET.get('upload_type')
	username=request.user.username
	if request.method=="POST":
		filename=str(request.FILES.get("file"))
		filecontent=request.FILES.get('file').read()
		filesize=  "%sKB" % (float(request.FILES.get('file').size)/float(1024))
		alllogline=cache.get('keyfilelog')
		if not alllogline:
			alllogline={}
		logline={}
		if upload_type=='keyfile':
			logline['time']=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time()))
			logline['filename']=filename
			logline['username']=username
			logline['fid']=fid
			alllogline[fid]=logline
			cache.set('keyfilelog',alllogline,36000000000000)
			file_position="%s/%s" % (keyfiledir,filename)
		elif upload_type=='script':
			logline['time']=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time()))
			logline['filename']=filename
			logline['username']=username
			scriptlogline=cache.get('scriptlogline')   
			if scriptlogline is None:scriptlogline={}
			scriptlogline[filename]=logline
			cache.set('scriptlogline',scriptlogline,36000000000000)
			file_position="%s/%s" % (scriptfiledir,filename)
			info['content']=logline
		else:
			file_position="%s/%s" % (upload_dir,filename)
		try:
			t=open(file_position,"wb")
			t.write(filecontent)
			t.close()
			info["msgtype"]="OK"
			info["path"]=file_position
			if upload_type=="keyfile":info=logline
		except Exception,e:
			print e
			info["content"]=str(e)
	info=json.dumps(info)
	response=HttpResponse(info)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "POST"
        response["Access-Control-Allow-Credentials"] = "true"
	response["Access-Control-Allow-Headers"]="Content-Type"
	return response
	"""try:
		local_upload_all=cache.get('local_upload')
		client_ip=request.META['REMOTE_ADDR']
		if local_upload_all is None:local_upload_all={}
		local_upload={}
		local_upload['username']=username
		local_upload['time']=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time()))
		local_upload['ip']=client_ip
		local_upload['filename']=filename
		local_upload['filsize']=filesize
		local_upload['fid']=fid
		local_upload_all[fid]=local_upload
		cache.set('local_upload',local_upload_all,3600000000)
	except Exception,e:
		info['content']=str(e)
		print "发生错误",e"""
	print response
	return response
@login_check.login_check()
def filetrans(request):
	fid=str(random.randint(90000000000000000000,99999999999999999999))
	info={"msgtype":"OK","fid":fid,"status":"running"}
	host=request.GET.get('host')
	action=request.GET.get('action')
	callback=request.GET.get('callback')
	lasttime=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
	redis_info={"msgtype":"OK","content":"","progres":"0",'status':"running","lasttime":lasttime}
	cache.set("info:%s" % (fid),redis_info,360)
	user=request.user.username
	if action and host:
		if action=="upload":
			FileTransfer.getconf(host,fid,user,"upload")
			print "上传"
		else:
			FileTransfer.getconf(host,fid,user,"download")
	else:
		info["msgtype"]="ERR"
		info["content"]="请求格式错误"
	info=json.dumps(info)
	if callback is None:
		info=info
	else:
		info="%s(%s)"  % (callback,info)
	response=HttpResponse(info)
	response["Access-Control-Allow-Origin"] = "*"
	response["Access-Control-Allow-Methods"] = "POST"
	response["Access-Control-Allow-Credentials"] = "true"
	return response
#@auth_check.auth_check #提到前面
def haha(request):
	return HttpResponse('haha')
@login_check.login_check()
def pathsearch(request):
	info={'msgtype':"OK","content":""}
	callback=request.GET.get('callback')
	path=request.GET.get('path')
	pathinfo=path_search.get_query_string(path)
	info['content']=pathinfo
	info=json.dumps(info)
	if callback is None:
		backstr=info
	else:
		backstr="%s(%s)"  % (callback,info)
	return HttpResponse(backstr)
	
@login_check.login_check()
def configmodify(request):
	modify_type=request.GET.get('type')
	callback=request.GET.get('callback')
	host=request.GET.get('host')
	info={"msgtype":"ERR","content":"","id":""}
	username=request.user.username
	if modify_type=='del':
		try:
			host=eval(host)
			if not type([])==type(host):info["content"]="参数应该是一个[]"
		except Exception,e:
			info["content"]="参数格式错误"
	else:
		try:
			host=eval(host)
		except Exception,e:
			info["content"]="参数格式错误"
	if type({})==type(host) or type([])==type(host):
		if modify_type=="modify":
			try:
				t_allgroupall=cache.get('allconf')
				id=host['id']
				if t_allgroupall:
					print '浏览器的参数',host
					for b in host.keys():
						if b=='id' or b=="owner" or not host[b]:
							print '跳过'
							continue
						else:
							t_allgroupall['content'][id][b]=host[b]
							info['msgtype']='OK'
							cache.set('allconf',t_allgroupall,36000000000000)
				else:
					info['content']='未装载配置'
			except KeyError:
				info['msgtype']='ERR'
				print '发生错误，配置不存在'
				info['content']="配置不存在"
			except Exception,e:
				info['msgtype']='ERR'
				print "错误",e
				
		elif modify_type=="add":
			id=int(random.randint(90000000000,99999999999))
			id=json.dumps(id)
			t_allgroupall=cache.get('allconf')
			host['id']=id
			host['owner']=username
			if not host.has_key('password'):host['password']=""
			if t_allgroupall:
				t_allgroupall['content'][id]=host
			else:
				t_allgroupall={"msgtype":"OK","content":{}}
				t_allgroupall['content'][id]=host
			info['msgtype']='OK'
			info['id']=id
			cache.set('allconf',t_allgroupall,8640000000)
		elif modify_type=='del':
			try:
				t_allgroupall=cache.get('allconf')
				if t_allgroupall:
					for id in host:
						id=str(id)
						if username==t_allgroupall['content'][id]['owner']:
							try:
								del t_allgroupall['content'][id]
							except KeyError:
								pass
							info['msgtype']='OK'
						else:
							info['content']="非法操作"
							break
				cache.set('allconf',t_allgroupall,360000000000)
			except KeyError:
				info['msgtype']='OK'

			except Exception,e:
				info['content']=str(e)
				print "错误",e,host,type(host),id,t_allgroupall
		else:
			info["content"]="指定类型不可用"
	else:
		info["content"]="参数格式错误,不是一个dict"
	info=json.dumps(info,encoding='utf-8',ensure_ascii=False)
	if callback is None:
		backstr=info
	else:
		backstr="%s(%s)"  % (callback,info)
	return HttpResponse(backstr)
@login_check.login_check()
def delcrondlog(request):
	callback=request.GET.get('callback')
	fid=request.GET.get('fid')
	info={"msgtype":"ERR","content":""}
	delcrond_log=crond_record.crond_del(fid)
	if delcrond_log[0]:
		info['msgtype']='OK'
	else:
		info['content']=delcrond_log[1]
	info=json.dumps(info,encoding='utf-8')
	if callback is None:
		backstr=info
	else:
		backstr="%s(%s)"  % (callback,info)
	return HttpResponse(backstr)
@login_check.login_check()
def showcrondlog(request):
	callback=request.GET.get('callback')
	info={"msgtype":"OK","content":""}
	crondlog_log=crond_record.crond_show()[1]
	info['content']=crondlog_log
	info=json.dumps(info,encoding='utf-8')
	if callback is None:
		backstr=info
	else:
		backstr="%s(%s)"  % (callback,info)
	return HttpResponse(backstr)
	
@login_check.login_check()
def crontab(request):
	runmodel="/home/cheungssh/mysite/mysite/cheungssh/"
	callback=request.GET.get('callback')
	value=request.GET.get('value')
	runtime=request.GET.get('runtime')
	runtype=request.GET.get('type')
	info={"msgtype":"ERR","content":""}
	crond_status=commands.getstatusoutput('/etc/init.d/crond status')
	crondlog_value={}
	if not crond_status[0]==0:
		info['content']=crond_status[1]
		print 'crond没有启动'
	else:
		try:
			value=eval(value)
			if not type({})==type(value):
				info['content']="数据类型错误"
			else:
				fid=str(random.randint(90000000000000000000,99999999999999999999)) 
				lasttime=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
				value['fid']=fid
				value['user']=request.user.username
				value['status']='未启动'.decode('utf-8')
				value['runtime']=runtime
				value['cmd']=""
				value['lasttime']=lasttime
				value['runtype']=runtype
				value['createtime']=str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime()))	
				value_to_log={}
				value_tmp=json.dumps(value)
				if runtype=="upload" or runtype=="download":
					value_to_log[value['fid']]=value
					runmodel_program=os.path.join(runmodel,"daemon_FileTransfer.py")
					cmd="""%s  %s '%s' #%s""" % (runtime,runmodel_program,value_tmp,value['fid'])
					a=open(crond_file,'a')
					a.write(cmd+"\n")
					a.close()
					crond_write=commands.getstatusoutput("""/usr/bin/crontab %s""" % (crond_file))
					if int(crond_write[0])==0:
						info['msgtype']='OK'
						crond_record.crond_record(value_to_log)
					else:
						print "加入计划任务失败",crond_write[1],crond_write[0]
						info['content']=crond_write[1]
					print 'Runtime: ',runtime
				elif runtype=="cmd":
					hostinfo=request.GET.get('value')
					try:
						hostinfo=eval(hostinfo)
						value['cmd']=hostinfo['cmd']
						value_to_log[value['fid']]=value
						cmdcontent= "\n%s#%s#%s\n"  %(hostinfo['cmd'],hostinfo['id'],value['fid'])
						try:
							with open(cmdfile,'a') as f:
								f.write(cmdcontent) 
							crondcmd=""" %s %s %s\n"""  % (runtime,'/home/cheungssh/bin/cheungssh_web.py',fid)
							try:
								with open(crond_file,'a') as f:
									f.write(crondcmd)
							
								crond_write=commands.getstatusoutput("""/usr/bin/crontab %s""" % (crond_file))
								if int(crond_write[0])==0:
									info['msgtype']='OK'
									crond_record.crond_record(value_to_log) 
								else:
									print "加入计划任务失败",crond_write[1],crond_write[0]
									info['content']=crond_write[1]
							except Exception,e:
								info['content']=str(e)
						except Exception,e:
							print '写入错误',e
							info['content']=str(e)
					except Exception,e:
						print '发生错误',e
						info['content']=str(e)
				else:
					info['content']="请求任务未知"
					
				
		except Exception,e:
			print "发生错误",e
			info['content']=str(e)
	info=json.dumps(info)
	if callback is None:
		backstr=info
	else:
		backstr="%s(%s)"  % (callback,info)
	return HttpResponse(backstr)
@login_check.login_check()
def local_upload_show(request):
	info={'msgtype':'ERR','content':[]}
	callback=request.GET.get('callback')
	local_upload_all=cache.get('local_upload')
	if local_upload_all:
		info['content']=local_upload_all.values()
	info=json.dumps(info)
	if callback is None:
		backstr=info
	else:
		backstr="%s(%s)"  % (callback,info)
	return HttpResponse(backstr)
@login_check.login_check()
def excutecmd(request):
	info={'msgtype':'ERR','content':[]}
	callback=request.GET.get('callback')
	cmd=request.GET.get('cmd')
	rid=request.GET.get("rid")
	ie_key=rid
	excute_time=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time()))
	client_ip=request.META['REMOTE_ADDR']
	client_ip_locat=IP.find(client_ip)
	username=request.user.username
	try:
		server=eval(cmd)
		cmd=server['cmd']
		selectserver=server['selectserver']
		Data=DataConf.DataConf()
		a=threading.Thread(target=cheungssh_web.main,args=(cmd,ie_key,selectserver,Data))
		a.start()
		info['msgtype']="OK"
	except Exception,e:
		info['content']=str(e)
	try:
		allconf=cache.get('allconf')
		allconf_t=allconf['content']
		server_ip_all=[]
		for sid in selectserver.split(','):
			server_ip=allconf_t[sid]['ip']
			server_ip_all.append(server_ip)
		cmd_history=cache.get('cmd_history')
		if cmd_history is None:cmd_history={}
		tid=str(random.randint(90000000000000000000,99999999999999999999))
		cmd_history_t={
				"tid":tid,
				"excutetime":excute_time,
				"IP":client_ip,
				"IP-Locat":client_ip_locat,
				"user":username,
				"servers":server_ip_all,
				"cmd":cmd
			}
		cmd_history[tid]=cmd_history_t
		cache.set('cmd_history',cmd_history,8640000000)
	except Exception,e:
		print "发生错误",e
		info['msgtype']='ERR'
		info['content']=str(e)
	info=json.dumps(info)
	if callback is None:
		backstr=info
	else:
		backstr="%s(%s)"  % (callback,info)
	return HttpResponse(backstr)
@login_check.login_check()
def cmdhistory(request):
	info={'msgtype':'ERR','content':[]}
	callback=request.GET.get('callback')
	cmd_history=cache.get('cmd_history')
	if  cmd_history:
		info['content']=cmd_history.values()
	info['msgtype']='OK'
	info=json.dumps(info,encoding='utf-8')
	if callback is None:
		backstr=info
	else:
		backstr="%s(%s)"  % (callback,info)
	return HttpResponse(backstr)
@login_check.login_check()
def get_hwinfo(request):
	info={'msgtype':'ERR','content':[]}
	callback=request.GET.get('callback')
	info['content']=hwinfo.hwinfo(cache)
	info['msgtype']='OK'
	info=json.dumps(info,encoding='utf-8',ensure_ascii=False)
	if callback is None:
		backstr=info
	else:
		backstr="%s(%s)"  % (callback,info)
	return HttpResponse(backstr)
@login_check.login_check(False)
def operation_record(request):	
	info={'msgtype':'ERR','content':[]}
	callback=request.GET.get('callback')
	get_login_record=cache.get('login_record')
	if get_login_record:	
		info['content']=get_login_record
	info=json.dumps(info,encoding='utf-8',ensure_ascii=False)
	if callback is None:

		backstr=info
	else:
		backstr="%s(%s)"  % (callback,info)
	return HttpResponse(backstr)
@login_check.login_check()
def excutes_script(request):
	info={'msgtype':'ERR','content':[]}
	callback=request.GET.get('callback')
	info=json.dumps(info,encoding='utf-8',ensure_ascii=False)
	if callback is None:
		backstr=info
	else:
		backstr="%s(%s)"  % (callback,info)
@login_check.login_check()
def get_script(request):
	fid=str(random.randint(90000000000000000000,99999999999999999999))  
	info={'msgtype':'ERR','content':[]}
	callback=request.GET.get('callback')
	edit_type=request.GET.get('edit_type')
	username=request.user.username
	uploadtime=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time())) 
	try:
		if edit_type=="show":
			try:
				filename=request.GET.get('filename')
				scriptfilepath=os.path.join(scriptfiledir,filename)
				with open(scriptfilepath) as f:
					scriptfilecontent=f.read().strip()
				info['msgtype']='OK'
				info['content']=scriptfilecontent
			except Exception,e:
				info['content']=str(e)
				print  '粗无',e
		elif edit_type=='list':
			scriptlogline=cache.get('scriptlogline')
			if scriptlogline:
				info['content']=scriptlogline.values()
			info['msgtype']='OK'
		elif edit_type=='add':
			try:
				scriptfilecontent=request.POST.get('filecontent')
				filename=request.POST.get('filename')
				scriptfilepath=os.path.join(scriptfiledir,filename)
				with open(scriptfilepath,'wb')  as f:
					f.write(scriptfilecontent)
				logline={}
				logline['time']=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time()))
				logline['filename']=filename
				logline['username']=username
				scriptlogline=cache.get('scriptlogline')  
				if scriptlogline is None:scriptlogline={}
                        	scriptlogline[filename]=logline
                        	cache.set('scriptlogline',scriptlogline,36000000000000)
				info['msgtype']='OK'
				info['content']=logline
			except Exception,e:
				info['content']=str(e)
		elif edit_type=='delete':
			filenames=request.GET.get('filenames') 
			scriptlogline=cache.get('scriptlogline')  
			if scriptlogline:
				for filename in  scriptlogline:
					try:
						del scriptlogline[filename]
					except KeyError:
						pass
					except Exception,e:
						print '错误',e
						info['content']=str(e)
						break
					info['msgtype']='OK'
			else:
					info['msgtype']='OK'
				
	except Exception,e:
		print e,'错误'
		info['content']=str(e)
	info=json.dumps(info,encoding='utf-8',ensure_ascii=False)
	if callback:
		try:
			backstr="%s(%s)" % (callback,info)
		except Exception,e:
			info['content']=str(e)
			print '错误',e
	else:
		backstr=info
	return HttpResponse(backstr)
def onelinenotice(request):
	info={'msgtype':'ERR','content':[]}
	callback=request.GET.get('callback')
	login_check_info=login_check.login_check()(request)
	if not login_check_info[0]:return HttpResponse(login_check_info[1])

'''from auth_check import auth_check
class  test(View,auth_check):
	def get(self,request):
		a=auth_check.__init__(self)
		print a
		return HttpResponse('这是get请求')'''
def t1(request):
	print type(request.user)
	return HttpResponse(request.user)
@login_check.login_check()
def sshcheck(request):
	info={"msgtype":"OK","content":"","status":"ERR"}
	callback=request.GET.get('callback')
	id=request.GET.get('id')
	try:
		conf=db_to_redis_allconf.allhostconf()['content'][id]
		print conf,5555555555555555555555555555555555
		sshcheck=ssh_check.ssh_check(conf)
		if sshcheck['msgtype']=="OK":
			info['status']="OK"
		else:
			info['status']="ERR"
			info['content']=sshcheck['content']
	except KeyError:
		info['msgtype']='ERR'
		info['content']="服务器不存在"
	info=json.dumps(info,encoding='utf-8',ensure_ascii=False)
	if callback is None:
		info=info
	else:
		info="%s(%s)"  % (callback,info)
	return HttpResponse(info)
def cheungssh_index_redirect(request):
	return HttpResponseRedirect('/cheungssh/')
