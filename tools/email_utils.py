# -*- coding: utf-8 -*-
# 实现邮件发送
import smtplib
from datetime import datetime
from email.mime.text import MIMEText

now = datetime.now()
todayStr = now.strftime('%Y_%m_%d')


class EmailUtils:
    sender = 'yseod@derivatives-china.com'
    receiver = ['liuqiuxia@derivatives-china.com']  # 接收者邮箱
    operation_receiver = ['liuqiuxia@derivatives-china.com']
    group1_receiver = ['liuqiuxia@derivatives-china.com']

    smtpserver = 'smtp.exmail.qq.com'
    username = 'yseod@derivatives-china.com'
    password = 'Yan1sheng'

    def __init__(self, receiver=''):
        if receiver != '':
            self.receiver = receiver

    def send_email_path(self, subject, file_path):
        fp = open(file_path)
        msg = MIMEText(datetime.now().strftime('%Y-%m-%d %H:%M:%S\n') + fp.read())
        msg['Subject'] = subject
        msg['From'] = "Daily Job"

        smtp = smtplib.SMTP_SSL(self.smtpserver, port=465)
        smtp.login(self.username, self.password)
        smtp.sendmail(self.sender, self.receiver, msg.as_string())
        smtp.quit()

    # 发送邮件给运维人员
    def send_email_operation(self, subject, content):
        msg = MIMEText(content)
        msg['Subject'] = subject
        msg['From'] = "Daily Job"

        smtp = smtplib.SMTP_SSL(self.smtpserver, port=465)
        smtp.login(self.username, self.password)
        smtp.sendmail(self.sender, self.operation_receiver, msg.as_string())
        smtp.quit()

    def send_email_group1(self, subject, content):
        msg = MIMEText(content)
        msg['Subject'] = subject
        msg['From'] = "Daily Job"

        smtp = smtplib.SMTP_SSL(self.smtpserver, port=465)
        smtp.login(self.username, self.password)
        smtp.sendmail(self.sender, self.group1_receiver, msg.as_string())
        smtp.quit()
