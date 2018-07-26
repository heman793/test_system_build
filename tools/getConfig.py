import os
from public.main_config import project_path, eod_aps_config_filename
# path = os.path.dirname(__file__)
config_path = os.path.join(project_path, eod_aps_config_filename)


def getConfig():
    cfg_dict = dict()
    fr = open(config_path)
    for line in fr:
        l = line.strip()
        if (l=='') or (l[0]=='#'):
            continue
        if l=='<-mysql--':
            pass
        elif l=='--mysql->':
            pass
        else:
            [key,data] = l.split('=')
            cfg_dict[key]=data
    fr.close()
    return cfg_dict
