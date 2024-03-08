import os

def check_OS():
    return os.name

def clear_console():
    host_OS:str = check_OS()
    if host_OS == 'nt':
        command = 'cls' 
    else:
        command = 'clear'

    return os.system(command)

def load_file(filename:str, path:str=None):
    if path:
        host_OS:str = check_OS()
        if host_OS == 'nt':
            sep = '\\'
        else:
            sep = '//'
        filename = f'{path}{sep}{filename}'
    with open(filename, 'r') as file_obj:
        file_content:list[str] = file_obj.readlines()
    
    return file_content

def save_file(filename:str, data, path:str=None):
    if path:
        host_OS:str = check_OS()
        if host_OS == 'nt':
            sep = '\\'
        else:
            sep = '//'
        filename = f'{path}{sep}{filename}'
    with open(filename, 'w') as file_obj:
        file_obj.write(data)

def create_dir(dir_name:str, path:str=None):
    if path:
        host_OS:str = check_OS()
        if host_OS == 'nt':
            sep = '\\'
        else:
            sep = '//'
        dir_name = f'{path}{sep}{dir_name}'
    os.mkdir(dir_name)