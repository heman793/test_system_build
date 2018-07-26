# -*- coding: utf-8 -*-
import MySQLdb
import paramiko
from datetime import datetime
import sys
from tools.email_utils import EmailUtils
from tools.sqlalchemy_utils import SQLAlchemyUtils


class ServerModel:
    name = ''
    ip = ''
    port = 22
    userName = 'trader'
    passWord = 'admin@yansheng123'

    db_ip = ''
    db_user = 'admin'
    db_password = 'adminP@ssw0rd'
    db_port = 3306

    # derivatives_client所在目录
    derivatives_client_folder = ''

    server_python_folder = ''

    # datafetcher所在目录
    datafetcher_folder = ''

    # python文件执行目录
    python_eod_folder = ''

    # etf文件原始目录
    etf_folder = ''
    # etf文件上传目录
    etf_upload_folder = ''

    mktdtctr_cfg_service_path = ''

    # 行情中心文件相关属性
    mktcenter_file_template_list = []
    mktcenter_file_path = ''
    mktcenter_check_path = ''
    mktcenter_local_save_path = ''

    log_file_path = ''

    def __init__(self, name):
        self.name = name
        self.db_session_pool = dict()

    def get_db_session(self, db_name):
        if db_name in self.db_session_pool:
            db_session = self.db_session_pool[db_name]
        else:
            sqlalchemy_utils = SQLAlchemyUtils(self.db_ip)
            sqlalchemy_utils.db_user = self.db_user
            sqlalchemy_utils.db_password = self.db_password
            sqlalchemy_utils.db_port = self.db_port

            db_session = sqlalchemy_utils.db_session(db_name)
            self.db_session_pool[db_name] = db_session
        return db_session

    def get_db_connect(self, session_name='common'):
        try:
            conn = MySQLdb.connect( \
                host=self.ip, user=self.db_user, passwd=self.db_password, \
                db=session_name, charset='utf8')
        except Exception, e:
            print e
            sys.exit()
        return conn

    def run_cmd(self, cmd_str):
        cmd_result_list = []
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            for m in cmd_str:
                ssh.connect(self.ip, self.port, self.userName, self.passWord, timeout=30)
                stdin, stdout, stderr = ssh.exec_command(m)
                cmd_result = stderr.readlines()
                print '-----------stderr-----------'
                for item in cmd_result:
                    print item

                if len(cmd_result) > 0:
                    error_message = '[ERROR]%s:IP:%s, CMD:%s Return ' \
                                    'Error:%s!' % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self.ip, m , '\n'.join(cmd_result))
                    if 'Traceback' in error_message:
                        EmailUtils(EmailUtils.group2).send_email_group_all('[ERROR]Server:%s Cmd Run!' % self.name, error_message)

                cmd_result = stdout.read()
                print '-----------stdout-----------'
                for item in cmd_result.splitlines():
                    cmd_result_list.append(item)
                print '%s:IP:%s, CMD:%s Run Over!' % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self.ip, m)
            ssh.close()
        except Exception, e:
            print e
            error_message = '%s:ip:%s run cmd:%s Error!' % (
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self.ip, cmd_str)
            print error_message
            EmailUtils(EmailUtils.group2).send_email_group_all('[ERROR]Server:%s Cmd Run!' % self.name, error_message)
        return '\n'.join(cmd_result_list)


    def run_cmd2(self, cmd_str):
        cmd_result_list = []
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.ip, self.port, self.userName, self.passWord, timeout=30)
            for m in cmd_str:
                stdin, stdout, stderr = ssh.exec_command(m)
                cmd_result = stderr.readlines()
                print '-----------stderr-----------'
                for item in cmd_result:
                    print item

                if len(cmd_result) > 0:
                    error_message = '[ERROR]%s:IP:%s, CMD:%s Return ' \
                                    'Error:%s!' % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self.ip, m , '\n'.join(cmd_result))
                    if 'Traceback' in error_message:
                        EmailUtils(EmailUtils.group2).send_email_group_all('[ERROR]Server:%s Cmd Run!' % self.name, error_message)

                cmd_result = stdout.read()
                print '-----------stdout-----------'
                for item in cmd_result.splitlines():
                    cmd_result_list.append(item)
                print '%s:IP:%s, CMD:%s Run Over!' % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self.ip, m)
            ssh.close()
        except Exception, e:
            print e
            error_message = '%s:ip:%s run cmd:%s Error!' % (
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self.ip, cmd_str)
            print error_message
            EmailUtils(EmailUtils.group2).send_email_group_all('[ERROR]Server:%s Cmd Run!' % self.name, error_message)
        return cmd_result_list

    # 下载文件remote_path至dest_path
    def download_file(self, remote_path, dest_path):
        t = paramiko.Transport((self.ip, self.port))
        t.connect(username=self.userName, password=self.passWord, hostkey=None)
        sftp = paramiko.SFTPClient.from_transport(t)

        sftp.get(remote_path, dest_path.decode('gb2312'))  # 下载
        print 'Download file:%s success' % (remote_path,)
        t.close()

    #  获取远程目录下所有文件
    def get_server_file_list(self, server_file_folder):
        file_list = []
        t = paramiko.Transport((self.ip, self.port))
        t.connect(username=self.userName, password=self.passWord, hostkey=None)
        sftp = paramiko.SFTPClient.from_transport(t)
        files = sftp.listdir(server_file_folder)
        for file_name in files:
            file_list.append(file_name)
        t.close()
        return file_list

    def close(self):
        if len(self.db_session_pool) == 0:
            return
        for (key, db_session) in self.db_session_pool.items():
            db_session.close()
        self.db_session_pool = dict()


