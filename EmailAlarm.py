# -*- coding: UTF-8 -*-
#  jhiwvfrodvffbbga
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

my_sender = '995450215@qq.com'       # 发送邮箱
my_pass = 'jhiwvfrodvffbbga'         # 授权码
my_user = '17683740622@163.com'      # 收件人邮箱账号，我这边发送给自己


def sendmail(messagesub, videonum, txtname):
    fail = False

    # 创建一个带附件的实例
    msg = MIMEMultipart()
    msg['From'] = formataddr(["MyServer", my_sender])  # 括号里的对应发件人邮箱昵称、发件人邮箱账号
    msg['To'] = formataddr(["myself", my_user])  # 括号里的对应收件人邮箱昵称、收件人邮箱账号
    if messagesub != None:
        msg['Subject'] = messagesub  # 邮件的主题，也可以说是标题
        # 邮件正文内容
        msg.attach(MIMEText('连接中断', 'plain', 'utf-8'))
    if txtname != None:
        # 构造附件1，传送当前目录下的 test.txt 文件
        att1 = MIMEText(open(txtname, 'rb').read(), 'base64', 'utf-8')
        att1["Content-Type"] = 'application/octet-stream'
        # 这里的filename可以任意写，写什么名字，邮件中显示什么名字
        att1["Content-Disposition"] = ('attachment; filename=' + txtname)
        msg.attach(att1)
    if videonum != None:
        # 构造附件2
        att2 = MIMEApplication(open(("saveVideo/" + videonum + ".avi"),'rb').read())
        att2.add_header('Content-Disposition', 'attachment', filename="LastVideo.avi")
        msg.attach(att2)

    try:
        server = smtplib.SMTP("smtp.qq.com", 25)  # 发件人邮箱中的SMTP服务器，端口是25
        server.login(my_sender, my_pass)  # 括号中对应的是发件人邮箱账号、邮箱密码
        server.sendmail(my_sender, [my_user, ], msg.as_string())  # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
        server.quit()  # 关闭连接
        print("Email send successful!")
    except Exception:  # 如果 try 中的语句没有执行，则会执行下面的 ret=False
        fail = True
        print("Email send failed!")
    return fail


# ret = mail()
# if ret:
#     print("邮件发送成功")
# else:
#     print("邮件发送失败")