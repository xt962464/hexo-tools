#_*_coding:utf-8_*_
import os
import json
import time
import threading
from tkinter import *
from tkinter.filedialog import askdirectory
from tkinter import scrolledtext
import tkinter.messagebox
import tkinter.simpledialog
from tkinter import ttk
import requests
from bs4 import BeautifulSoup
from qiniu import Auth, put_file,BucketManager
import windnd

"""主界面"""
root = Tk()
root.resizable(width=0, height=0)
root.title('Hexo博客工具-原创作者:琅琊阁 https://www.xt-inn.com')

# 设置窗口大小
width = 1050
height = 550

# 按钮
btn_font = ('华文行楷', 16)

setting_path=os.getcwd()+"\\setting.ini"

global input_panel_entry

# 获取电脑屏幕尺寸
xscreen = root.winfo_screenwidth()
yscreen = root.winfo_screenheight()
# 获取窗口居中显示时起始坐标
xmiddle = (xscreen-width)/2
ymiddle = (yscreen-height)/2
root.geometry('%dx%d+%d+%d' % (width, height, xmiddle, ymiddle))


# 输入框
def getInput(title):
    def return_callback(event):
        print('quit...')
        input_root.quit()
    def close_callback():
        input_root.destroy()
        # tkinter.messagebox.showinfo('message', 'no click...')
    input_root = Tk(className="创建文章")
    input_root.wm_attributes('-topmost', 1)
    screenwidth, screenheight = input_root.maxsize()
    width = 500
    height = 100
    size = '%dx%d+%d+%d' % (width, height, (screenwidth - width)/2, (screenheight - height)/2)
    input_root.geometry(size)
    input_root.resizable(0, 0)
    input_panel_value = StringVar()
    input_panel_entry = Entry(input_root, font="Helvetica 18 bold", textvariable=input_panel_value)
    input_panel_entry.bind('<Return>', return_callback)
    if title:
        input_panel_entry.delete(0,END)
        input_panel_entry.insert("end", title)
        input_panel_entry.update()
    # entry.pack()
    input_panel_entry.place(relx=0.025, rely=0.3, relheight=0.4, relwidth=0.95)
    input_panel_entry.focus_set()
    input_root.protocol("WM_DELETE_WINDOW", close_callback)
    input_root.mainloop()
    str = input_panel_entry.get()
    input_root.destroy()
    return str

# 请求头
def getHeader():
    header = {}
    header["Content-Type"]="application/x-www-form-urlencoded; charset=UTF-8"
    header["Host"] = "gitee.com"
    header["Origin"] = "https://gitee.com"
    header["Referer"] = "https://gitee.com"
    header["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"
    if "cookie" in userInfo.keys() and "token" in userInfo.keys():
        header["X-CSRF-Token"] = userInfo["token"]
        header["Cookie"] = userInfo["cookie"]
    return header

#新建文章
def createArticle():
    if "path" in userInfo.keys():
        title=getInput(None)
        # title = title.replace(" ","") # 去除标题中所有的空格
        #cmd命令创建
        # cmd = "cd "+userInfo["path"] + " && "+userInfo["path"][0:2]+" && hexo new \""+title+'" && cls'
        # print("执行:",cmd)
        # os.system(cmd)
        #IO操作创建
        page = userInfo["path"] + "\\source\\_posts\\" + title + ".md"
        if not os.path.exists(page):
            post = userInfo["path"]+"\\scaffolds\\post.md"
            fp = open(post,'r',encoding="utf8")
            template = fp.read()
            contents = template.replace("{{ title }}",title).replace("{{ date }}",time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
            with open(page,'w',encoding="utf8") as f:
                f.write(contents)
            f.close()
            fp.close()
            os.startfile(userInfo["path"]+"\\source\\_posts\\"+title+".md")
    else:
        tkinter.messagebox.showerror('警告', '请先选择项目路径！')

def submit():
    if "path" in userInfo.keys():
        path = userInfo["path"]
        cmd = "cd "+path+"&& "+path[0]+": && cls && hexo clean && hexo g && hexo d && pause"
        with open("push.bat", "w", encoding="utf8") as f:
            f.write(cmd)
        f.close()
        os.startfile("push.bat")

def getDowItem():
    def return_callback(event):
        print('quit...')
        down_root.quit()
    def close_callback():
        down_root.destroy()
        # tkinter.messagebox.showinfo('message', 'no click...')
    global nouser
    nouser = False
    down_root = Tk(className="更新")
    down_root.wm_attributes('-topmost', 1)
    screenwidth, screenheight = down_root.maxsize()
    width = 300
    height = 100
    size = '%dx%d+%d+%d' % (width, height, (screenwidth - width)/2, (screenheight - height)/2)
    down_root.geometry(size)
    down_root.resizable(0, 0)
    dow_value=StringVar()
    global down
    down = ttk.Combobox(down_root, textvariable=dow_value)  # #创建下拉菜单
    path = ""
    if "path" in userInfo.keys():
        path = userInfo["path"]+"\source\_posts"
    elif  file_entry.get():
        nouser = True
        path=file_entry.get()+"\source\_posts"
    if path:
        down["value"] = os.listdir(path)
    down.bind('<<ComboboxSelected>>', return_callback)
    down.place(relx=0, rely=0.4, relheight=0.3, relwidth=1)
    # entry.focus_set()
    down_root.protocol("WM_DELETE_WINDOW", close_callback)
    down_root.mainloop()
    str = down.get()
    down_root.destroy()
    return str

# 更新
def rebuild():
    print("------build-----")
    api = "https://gitee.com/setaria/setaria/pages/rebuild"
    html=getAPI(api)
    if html == -1:
        return False
    if "403 Forbidden" in html:
        print("403 Forbidden")
        return False
    elif "请勿频繁更新部署，稍等1分钟再试试看" in html:
        print("请勿频繁更新部署，稍等1分钟再试试看")
        return False
    else:
        status = html.find("span", id="pages_deploying").get_text()[1:-1]
        print(status)
        return True

# 请求API
def getAPI(api):
    params = {}
    params["branch"] = userInfo["branch"]
    params["build_directory"] = ""
    params["force_https"] = "false"
    params["auto_update"] = "false"
    try:
        html = requests.post(api,data= params,headers = getHeader(),timeout=5).text
        html=html.replace("\\","").replace("\n","")\
            .replace("$('.pages-pay-modal').remove()$('.pages_message').html(\"","")\
            .replace("$('.pages-pay-modal').remove()","")\
            .replace("\")$('.pages_message .ui.dropdown').dropdown();","")
        return BeautifulSoup(html,'html.parser')
    except:
        return -1

# 获取 更新状态
def getpages():
    api = "https://gitee.com/setaria/setaria/pages"
    html=getAPI(api)
    if html == -1:
        return -1
    if html.find("span", id="pages_deploying"):
        status = html.find("span", id="pages_deploying").get_text()[1:-1]
        print(status)
        return 0
    elif  html.find("p", class_="start-service-description"):
        status = html.find("p", class_="start-service-description").get_text()[2:-1]
        print(status)
        return 1

# 创建一条线程
def createShowInfo():
    '''创建一条线程去处理弹窗'''
    t = threading.Thread(target=showInfo)
    t.start()

def showInfo():
    tkinter.messagebox.showinfo('提示', '执行中！')

# 部署按钮点击事件
def updatePage():
    if "cookie" in userInfo.keys():
        falge = tkinter.messagebox.askokcancel("温馨提示", "确认要更新部署吗")
        if falge:
            build=rebuild()
            if build:
                while True:
                    time.sleep(2)
                    falg=getpages()
                    if falg==-1:
                        tkinter.messagebox.showerror('提示', '更新失败！')
                        break
                    elif falg == 1:
                        tkinter.messagebox.showinfo('提示', '更新完成！')
                        break
            else:
                tkinter.messagebox.showerror('提示', '更新失败！')
    else:
        tkinter.messagebox.showerror('警告', '请先填写信息！')

# 获取hexo 博客本地目录
def getHexoPath():
    dir_path = askdirectory()
    print("文件路径"+ dir_path)
    if dir_path:
        file_entry.delete(0, END)
        file_entry.insert("end",dir_path)
        file_entry.update()

# 保存信息到本地
def saveInfo():
    # 账号以及项目数据
    file_path = file_entry.get()
    cookie = cookie_Text.get()
    branch = branch_Text.get()
    token = token_Text.get()
    # 七牛云数据
    bucket = qiniu_bucket_Text.get()
    AK = qiniu_AK_Text.get()
    SK = qiniu_SK_Text.get()
    domain = qiniu_doMain_Text.get()
    if bucket:
        userInfo["bucket"] = bucket
    if AK:
        userInfo["AK"] = AK
    if SK:
        userInfo["SK"] = SK
    if domain:
        userInfo["domain"] = domain

    print("path: "+file_path)
    print("cookie: " + cookie)
    print("branch: " + branch)
    if file_path and cookie and branch and token:
        userInfo["path"] = file_path
        userInfo["cookie"] = cookie
        userInfo["branch"] = branch
        userInfo["token"]= token
        info = json.dumps(userInfo,ensure_ascii=False)
        with open(setting_path, "w", encoding='utf8') as f:
            f.write(info)
        f.close()
        tkinter.messagebox.showinfo('提示', '保存成功！')
        getLocalInfo()
    else:
        tkinter.messagebox.showerror('警告', '数据不完整！')

# 读取本地数据
def getLocalInfo():
    global userInfo
    if os.path.isfile(setting_path):
        files=open(setting_path,'r',encoding='utf8')
        try:
            userInfo = json.load(files)
        except:
            files.close()
            userInfo={}
            # os.remove(setting_path)
        if files:
            files.close()
    else:
        userInfo={}

# 本地运行hexo
def deBugs():
    print("调试")
    cmd = "cd " + userInfo["path"] + " && " + userInfo["path"][0:2] + "&& cls && hexo clean && hexo g && hexo s && cls"
    with open("debug.bat","w",encoding="utf8") as f:
        f.write(cmd)
    f.close()
    os.startfile("debug.bat")

# 更新按钮
def updateArticle():
    item = getDowItem()
    path = ""
    opType=selectPanel()
    print("操作:",opType)
    if opType == 1:
        rename(item)
    elif opType == 2:
        if nouser:
            path = file_entry.get() + "\source\_posts\\"+item
        else:
            path = userInfo["path"] + "\source\_posts\\"+item
        if path:
            os.startfile(path)

def rename(item):
    # input_panel_entry.delete(0,END)
    # input_panel_entry.insert("end", item.replace(".md", ""))
    # input_panel_entry.update()
    newName=getInput(item.replace(".md", ""))+".md"
    if newName:
        oldpath=""
        newPalth=""
        if nouser:
            oldpath = file_entry.get() + "\source\_posts\\" + item
            newPalth = file_entry.get() + "\source\_posts\\" + newName
        else:
            oldpath = userInfo["path"] + "\source\_posts\\" + item
            newPalth = userInfo["path"] + "\source\_posts\\" + newName
        try:
            os.rename(oldpath,newPalth)
            tkinter.messagebox.showinfo('提示', '修改成功,记得重新部署')
        except:
            tkinter.messagebox.showerror('提示', '修改失败！')


# 选择面板
def selectPanel():
    opType = -1
    def return_rename_callback():
        nonlocal opType
        opType = 1
        panel_root.quit()
    def return_update_callback():
        nonlocal opType
        opType = 2
        panel_root.quit()
    def close_callback():
        panel_root.destroy()
        # tkinter.messagebox.showinfo('message', 'no click...')
    global panel_root
    panel_root = Tk(className="选择")
    panel_root.wm_attributes('-topmost', 1)
    screenwidth, screenheight = panel_root.maxsize()
    width = 220
    height = 50
    size = '%dx%d+%d+%d' % (width, height, (screenwidth - width)/2, (screenheight - height)/2)
    panel_root.geometry(size)
    panel_root.resizable(0, 0)

    # 重命名
    rename_btn = Button(panel_root, text='重命名', font=btn_font,command=return_rename_callback)
    # createArticle_btn.place(relx=0.1,rely=0.1)
    rename_btn.grid(row=2,column=2,padx=8,pady=8)
    # 更新文章
    update_btn = Button(panel_root, text='更新文章', font=btn_font,command=return_update_callback)
    # createArticle_btn.place(relx=0.1,rely=0.1)
    update_btn.grid(row=2,column=3,padx=8,pady=8)
    panel_root.protocol("WM_DELETE_WINDOW", close_callback)
    panel_root.mainloop()
    panel_root.destroy()
    return opType

# 删除文章md文件
def deleteArticle():
    item = getDowItem()
    path = ""
    if nouser:
        path = file_entry.get() + "\source\_posts\\"+item
    else:
        path = userInfo["path"] + "\source\_posts\\"+item
    if path:
        falge = tkinter.messagebox.askokcancel("温馨提示", "确认要删除吗")
        if falge:
            os.remove(path)
            tkinter.messagebox.showinfo("温馨提示", "删除成功,记得从新上传部署")

def copyImgUrl():
    url = result_img_Text.get()
    print("复制",url)
    root.clipboard_clear()
    root.clipboard_append(url)

def deleteImgUrl():
    if isQiniu():
        falge = tkinter.messagebox.askokcancel("温馨提示","确认要删除吗")
        if falge:
            file = result_img_Text.get()
            access_key = userInfo["AK"]
            secret_key = userInfo["SK"]
            # 初始化Auth状态
            q = Auth(access_key, secret_key)
            # 初始化BucketManager
            bucket = BucketManager(q)
            # 你要测试的空间， 并且这个key在你空间中存在
            bucket_name = userInfo["bucket"]
            key = file.replace(userInfo["domain"]+"/","")
            # 删除bucket_name 中的文件 key
            ret, info = bucket.delete(bucket_name, key)
            print(info)
            if info.status_code == 200:
                result_img_Text.delete(0, END)
                tkinter.messagebox.showinfo('温馨提示', "文件删除成功")
            else:
                tkinter.messagebox.showerror('温馨提示', "文件删除失败")

# 判断七牛数据完整
def isQiniu():
    try:
        AK = userInfo["AK"]
        SK = userInfo["SK"]
        domain = userInfo["domain"]
        bucket = userInfo["bucket"]
        if AK and SK and bucket and domain:
            return True
        else:
            return False
    except:
        return False

#上传文件到七牛云
def uploadFile(filePath):
    #  filePath要上传文件的本地路径
    if isQiniu():
        access_key = userInfo["AK"]
        secret_key = userInfo["SK"]
        # 构建鉴权对象
        q = Auth(access_key, secret_key)
        # 要上传的空间
        bucket_name = userInfo["bucket"]
        # 上传后保存的文件名
        key = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
        print("保存文件名",key)
        # 生成上传 Token，可以指定过期时间等
        token = q.upload_token(bucket_name, key)
        rest, info = put_file(token, key, filePath)
        print("ret",rest)
        print("info", info)
        if info.status_code == 200:
            # rest=json.loads(ret) # https://cdn.blog.xt-inn.com/2021-01-14%2014%3A41%3A51
            url=userInfo["domain"]+"/"+rest["key"]
            result_img_Text.delete(0, END)
            result_img_Text.insert("end", url)
            result_img_Text.update()
        else:
            tkinter.messagebox.showerror('温馨提示', "文件上传失败")
    else:
        tkinter.messagebox.showerror('温馨提示', "缺少七牛参数")


# 创建各种按钮
def createButton():
    print("读取本地数据")
    getLocalInfo()
    print("创建按钮")
    global button_frame
    button_frame = Frame(root)
    button_frame2 = Frame(root )
    button_frame3 = Frame(root, bg="black")
    # 创建文章
    createArticle_btn = Button(button_frame, text='创建', font=btn_font,command=createArticle)
    # createArticle_btn.place(relx=0.1,rely=0.1)
    createArticle_btn.grid(row=1,column=1,padx=8,pady=8)

    # 更新
    update_btn = Button(button_frame, text='更新', font=btn_font,command=updateArticle)
    # createArticle_btn.place(relx=0.1,rely=0.1)
    update_btn.grid(row=1,column=2,padx=8,pady=8)

    # 调试
    debug_btn = Button(button_frame, text='调试', font=btn_font,command=deBugs)
    # createArticle_btn.place(relx=0.1,rely=0.1)
    debug_btn.grid(row=1,column=3,padx=8,pady=8)

    # 删除
    debug_btn = Button(button_frame, text='删除', font=btn_font,command=deleteArticle)
    # createArticle_btn.place(relx=0.1,rely=0.1)
    debug_btn.grid(row=1,column=4,padx=8,pady=8)

    # 上传
    submit_btn = Button(button_frame, text='上传', font=btn_font,command=submit)
    # createArticle_btn.place(relx=0.1,rely=0.1)
    submit_btn.grid(row=1,column=5,padx=8,pady=8)

    # 部署
    submit_btn = Button(button_frame, text='部署', font=btn_font,command=updatePage)
    # createArticle_btn.place(relx=0.1,rely=0.1)
    submit_btn.grid(row=1,column=6,padx=8,pady=8)

    # 文件路径
    file_btn = Button(button_frame, text='博客', font=btn_font,command=getHexoPath)
    # createArticle_btn.place(relx=0.1,rely=0.1)
    file_btn.grid(row=1,column=7,padx=14,pady=8)
    # 文件路径文本框
    path_value = StringVar()
    if "path" in userInfo.keys():
        path_value.set(userInfo["path"])
    global file_entry
    file_entry = Entry(button_frame,width = 55,textvariable=path_value)
    file_entry.grid(row=1, column=8,padx=20,pady=8)

    # 保存
    submit_btn = Button(button_frame, text='保存', font=btn_font,command=saveInfo)
    # createArticle_btn.place(relx=0.1,rely=0.1)
    submit_btn.grid(row=1,column=9,padx=8,pady=8)

    #  cookie
    cookie_label = Label(button_frame2, text="Cookie:")
    cookie_label.grid(row=1, column=1,padx=8,pady=8)
    # global cookie_Text
    global cookie_Text
    cookie_value = StringVar()
    if "cookie" in userInfo.keys():
        cookie_value.set(userInfo["cookie"])
    cookie_Text = Entry(button_frame2, width=55,textvariable=cookie_value)
    cookie_Text.grid(row=1, column=2,padx=8,pady=8)

    # 分支
    branch_label = Label(button_frame2, text="分支:")
    branch_label.grid(row=1, column=3,padx=8,pady=8)
    global  branch_Text
    branch_value = StringVar()
    if "branch" in userInfo.keys():
        branch_value.set(userInfo["branch"])
    else:
        branch_value.set("master")
    branch_Text = Entry(button_frame2,textvariable=branch_value, width=55)
    branch_Text.grid(row=1, column=4,padx=8,pady=8)

    #  token
    token_label = Label(button_frame2, text="token:")
    token_label.grid(row=2, column=1,padx=8,pady=8)
    # global cookie_Text
    global token_Text
    token_value = StringVar()
    if "token" in userInfo.keys():
        token_value.set(userInfo["token"])
    token_Text = Entry(button_frame2, width=55,textvariable=token_value)
    token_Text.grid(row=2, column=2,padx=8,pady=8)

    #  七牛空间名
    qiniu_bucket_name_label = Label(button_frame2, text="空间名:")
    qiniu_bucket_name_label.grid(row=2, column=3,padx=8,pady=8)
    # global cookie_Text
    global qiniu_bucket_Text
    qiniu_bucket_Text_value = StringVar()
    if "bucket" in userInfo.keys():
        qiniu_bucket_Text_value.set(userInfo["bucket"])
    qiniu_bucket_Text = Entry(button_frame2, width=55,textvariable=qiniu_bucket_Text_value)
    qiniu_bucket_Text.grid(row=2, column=4,padx=8,pady=8)

    #  七牛AK
    qiniu_AK_label = Label(button_frame2, text="七牛AK:")
    qiniu_AK_label.grid(row=3, column=1,padx=8,pady=8)
    # global cookie_Text
    global qiniu_AK_Text
    qiniu_AK_value = StringVar()
    if "AK" in userInfo.keys():
        qiniu_AK_value.set(userInfo["AK"])
    qiniu_AK_Text = Entry(button_frame2, width=55,textvariable=qiniu_AK_value)
    qiniu_AK_Text.grid(row=3, column=2,padx=8,pady=8)

    #  七牛SK
    qiniu_SK_label = Label(button_frame2, text="七牛SK:")
    qiniu_SK_label.grid(row=3, column=3,padx=8,pady=8)
    # global cookie_Text
    global qiniu_SK_Text
    qiniu_SK_value = StringVar()
    if "SK" in userInfo.keys():
        qiniu_SK_value.set(userInfo["SK"])
    qiniu_SK_Text = Entry(button_frame2, width=55,textvariable=qiniu_SK_value)
    qiniu_SK_Text.grid(row=3, column=4,padx=8,pady=8)

    #  域名
    qiniu_doMain_label = Label(button_frame2, text="域名:")
    qiniu_doMain_label.grid(row=4, column=1,padx=8,pady=8)
    # global cookie_Text
    global qiniu_doMain_Text
    qiniu_doMain_value = StringVar()
    if "domain" in userInfo.keys():
        qiniu_doMain_value.set(userInfo["domain"])
    qiniu_doMain_Text = Entry(button_frame2, width=55,textvariable=qiniu_doMain_value)
    qiniu_doMain_Text.grid(row=4, column=2,padx=8,pady=8)

    #  署名
    master_label = Label(button_frame2, text="原创作者:")
    master_label.grid(row=4, column=3,padx=8,pady=8)
    master_info_label = Label(button_frame2, text="https://www.xt-inn.com",justify=LEFT)
    master_info_label.grid(row=4, column=4,padx=8,pady=8,sticky = W)
    # 日志打印
    # global log_Text
    # log_Text = scrolledtext.ScrolledText(button_frame3, width=65, height=30)  #
    # log_Text.place(relx=0, rely=0, relheight=1, relwidth=1)

    #  文件上传区域
    # 左侧 -选择文件上传
    global file_frame
    file_frame = Frame(button_frame3,bg = "#B2B2B2")
    file_frame.place(relx=0, rely=0, relheight=1, relwidth=0.5)
    #右侧 -文件上传结果操作
    file_btn_frame = Frame(button_frame3)
    file_btn_frame.place(relx=0.5, rely=0, relheight=1, relwidth=0.5)
    file_btn_top_frame = Frame(file_btn_frame,bg = "#77ED92")
    file_btn_top_frame.place(relx=0, rely=0, relheight=0.1, relwidth=1)
    file_btn_bottom_frame = Frame(file_btn_frame)
    file_btn_bottom_frame.place(relx=0, rely=0.1, relheight=1, relwidth=1)
    # 图片URL地址
    qiniu_img_label = Label(file_btn_top_frame, text="URL:")
    qiniu_img_label.grid(row=1, column=1,padx=8,pady=8)
    global result_img_Text
    img_value = StringVar()
    result_img_Text = Entry(file_btn_top_frame, width=45,textvariable=img_value)
    result_img_Text.grid(row=1, column=2,padx=8,pady=8)
    # 复制
    copy_btn = Button(file_btn_top_frame, text='复制', font=btn_font,command=copyImgUrl)
    # createArticle_btn.place(relx=0.1,rely=0.1)
    copy_btn.grid(row=1,column=3,padx=8,pady=8)

    # 删除
    copy_btn = Button(file_btn_top_frame, text='删除', font=btn_font,command=deleteImgUrl)
    # createArticle_btn.place(relx=0.1,rely=0.1)
    copy_btn.grid(row=1,column=4,padx=8,pady=8)
    # 文本框 - 选中的文件
    global translate_Text1
    translate_Text1 = scrolledtext.ScrolledText(file_btn_bottom_frame,bg = "#FFEDDA")
    translate_Text1.place(relx=0, rely=0, relheight=1, relwidth=1)


    button_frame.place(relx=0, rely=0, relheight=0.1, relwidth=1)  # 显示
    button_frame2.place(relx=0, rely=0.1, relheight=0.35, relwidth=1)
    button_frame3.place(relx=0, rely=0.4, relheight=1, relwidth=1)

# 选择文件
def selectFile(files):
    # 仅仅上传一个文件
    file=files[0].decode("gbk")
    tkinter.messagebox.showinfo('上传提示', file)
    translate_Text1.insert("end",file)
    translate_Text1.insert('end', '\n')
    translate_Text1.update()
    uploadFile(file)

if __name__ == '__main__':
    createButton()  #创建按钮
    # root.iconbitmap("logo.ico")
    windnd.hook_dropfiles(file_frame,func=selectFile)
    root.mainloop()
