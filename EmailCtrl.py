import email
import poplib
import time
from email.parser import Parser
from email.header import decode_header
from email.utils import parseaddr

class EmailCtrl:

    def __init__(self, email="995450215@qq.com", password="qshkxonirqjsbcef", pop3_server="pop.qq.com"):
        self.email = email
        self.password = password
        self.pop3_server = pop3_server
        self.sender = ''
        self.recver = ''
        self.subject = ''
        self.emailserver = poplib.POP3_SSL(self.pop3_server)
        # self.msgcount = 0

    def _decode_str(self, s):
        value, charset = decode_header(s)[0]
        if charset:
            value = value.decode(charset)
        return value

    def _guess_charset(self, msg):
        charset = msg.get_charset()
        if charset is None:
            content_type = msg.get('Content-Type', '').lower()
            pos = content_type.find('charset=')
            if pos >= 0:
                charset = content_type[pos + 8:].strip()
        return charset

    def _get_header(self, msg, indent=0):            # 获取邮件关键信息
        info = []
        for header in ['From', 'Subject']:
            value = msg.get(header, '')
            if value:
                if header == 'Subject':
                    # 需要解码Subject字符串：
                    value = self._decode_str(value)
                else:
                    # 需要解码Email地址：
                    hdr, addr = parseaddr(value)
                    name = self._decode_str(hdr)
                    value = (name, addr)
            info.append(value)
        return info


    # indent用于缩进显示:
    def _print_info(self, msg, indent=0):            # 打印邮件内容
        if indent == 0:
            # 邮件的From, To, Subject存在于根对象上:
            for header in ['From', 'To', 'Subject']:
                value = msg.get(header, '')
                if value:
                    if header == 'Subject':
                        # 需要解码Subject字符串：
                        value = self._decode_str(value)
                    else:
                        # 需要解码Email地址：
                        hdr, addr = parseaddr(value)
                        name = self._decode_str(hdr)
                        value = u'%s <%s>' % (name, addr)
                print('%s%s: %s' % ('  ' * indent, header, value))
        if (msg.is_multipart()):
            # 如果邮件对象是一个MIMEMultipart,
            # get_payload()返回list，包含所有的子对象:
            parts = msg.get_payload()
            for n, part in enumerate(parts):
                print('%spart %s' % ('  ' * indent, n))
                print('%s--------------------' % ('  ' * indent))
                # 递归打印每一个子对象
                self.print_info(part, indent + 1)
        else:
            # 邮件对象不是一个MIMEMultipart，
            # 就根据content_type判断：
            content_type = msg.get_content_type()
            if content_type == 'text/plain' or content_type == 'text/html':
                content = msg.get_payload(decode=True)
                charset = self._guess_charset(msg)
                if charset:
                    content = content.decode(charset)
                print('%sText: %s' % ('  ' * indent, content + '...'))
            else:
                print('%sAttachment: %s' % ('  ' * indent, content_type))

    def emailServerConnect(self):
        self.emailserver.user(self.email)
        self.emailserver.pass_(self.password)
        print("Email socket opened.")

    def getcmd(self):
        resp, mails, octets = self.emailserver.list()
        # self.emailserver.stat()  # 返回邮件数量和占用空间: 返回值为一个ｔｕｒｐｌｅ

        # 获取最新一封邮件, 注意索引号从1开始:
        index = len(mails)
        resp, lines, octets = self.emailserver.retr(index)
        # lines存储了邮件的原始文本的每一行,它是个列表

        # 可以获得整个邮件的原始文本:
        msg_content = b'\r\n'.join(lines)
        # 解析出邮件:这里输出msg是个乱的，还没有真正的解析
        msg = Parser().parsestr(msg_content.decode('utf8'))
        # print(msg)
        info = self._get_header(msg)
        return info


    def emailServerDisconnect(self):
        self.emailserver.quit()
        print("Email socket closed.")