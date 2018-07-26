# -*- coding: utf-8 -*-
import os
import zipfile


class FileUtils:
    base_file_path = None

    def __init__(self, base_file_path):
        self.base_file_path = base_file_path

    def filter_file(self, *filter_key_items):
        filter_price_files = []
        for rt, dirs, files in os.walk(self.base_file_path):
            for search_file in files:
                find_flag = True
                for filter_key in filter_key_items:
                    if filter_key not in search_file:
                        find_flag = False

                if find_flag:
                    filter_price_files.append(search_file)
        filter_price_files.sort()
        # print filter_price_files
        return filter_price_files

    @staticmethod
    def zip_file(file_list, filename_zip):
        zf = zipfile.ZipFile(filename_zip, "w", zipfile.zlib.DEFLATED)
        for (file_path, file_name) in file_list:
            zf.write(file_path, file_name)
        zf.close()

    @staticmethod
    def unzip_file(filename_zip, unzip_dir):
        if not os.path.exists(unzip_dir):
            os.mkdir(unzip_dir, 0777)
        zfobj = zipfile.ZipFile(filename_zip)
        for name in zfobj.namelist():
            name = name.replace('\\', '/')
            if name.endswith('/'):
                os.mkdir(os.path.join(unzip_dir, name))
            else:
                ext_filename = os.path.join(unzip_dir, name)
                ext_dir = os.path.dirname(ext_filename)
                if not os.path.exists(ext_dir):
                    os.mkdir(ext_dir, 0777)
                outfile = open(ext_filename, 'wb')
                outfile.write(zfobj.read(name))
                outfile.close()

if __name__ == '__main__':
    data_path = '/nas/data_share/price_files/20180521'
    filter_date_str = '2018-05-21'
    FileUtils(data_path).filter_file('HUABAO_INSTRUMENT', filter_date_str)