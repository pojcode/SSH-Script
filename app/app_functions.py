import time
from app.network_functions import *
from app.system_functions import *
from app.app_templates import *
from netmiko import ConnectHandler, SSHDetect

def text_to_box(text:str, box_line:str='-'):
    boxed_text:str = (
        f'{box_line*(len(text)+2)}\n|{text}|\n{box_line*(len(text)+2)}'
    )

    return boxed_text

def get_template_data_file():
    return template_data_file

def create_data_table(values:dict, title:str, fix:int=4):
    max_lenght:int = 0
    data_list:list[str] = []
    for k, v in values.items():
        if type(v) == list:
            data:str = f'{k}: {", ".join(v)}'
        else:
            data = f'{k}: {v}'
        if len(data) > max_lenght:
            max_lenght = len(data)
        data_list.append(data)
    if len(title) > max_lenght:
        max_lenght = len(title)
    table:str = f'{"-"*(max_lenght + fix)}\n' \
                f'| {title.ljust(max_lenght)} |\n' \
                f'{"-"*(max_lenght + fix)}'
    for v in data_list:
        table += f'\n| {v.ljust(max_lenght)} |'
    table += f'\n{"-"*(max_lenght + fix)}'

    return table

def create_db(raw_file:list[str]):
    database:dict = {}
    is_command:bool = False
    command_list:list[str] = []
    for line in raw_file:
        line_upper = line.upper()
        if (
            line_upper.startswith('-USERNAME:') or
            line_upper.startswith('-PASSWORD:') or
            line_upper.startswith('-HOST:') or
            line_upper.startswith('-PING:') or
            line_upper.startswith('-FILES:') or
            line_upper.startswith('-MISC:')
        ):
            line = line.strip().split(':', maxsplit=1)
            database[line[0][1:].strip().upper()] = line[1].strip()
            if (
                line_upper.startswith('-FILES:') or 
                line_upper.startswith('-HOST:') or
                line_upper.startswith('-MISC:')
            ):
                values_list:list = [] 
                if line_upper.startswith('-HOST:'):
                    keyword:str = 'HOST'
                elif line_upper.startswith('-MISC:'):
                    keyword = 'MISC'
                else:
                    keyword = 'FILES'
                entry:str = database.get(keyword)
                if ',' in entry:
                    for v in entry.split(','):
                        if len(v.strip()) > 0:
                            values_list.append(v.strip())
                else:
                    if len(entry) > 0:
                        values_list.append(entry)
                database[keyword] = values_list
        elif line_upper.startswith('-COMMANDS:'):
            is_command = True
        elif is_command:
            if len(line.strip()) > 0:
                command_list.append(line.strip())
    database['COMMANDS'] = command_list

    return database

def check_db_mandatory_entries(database:dict):
    entry_error:list = []
    for k, v in database.items():
        if k in ('USERNAME', 'PASSWORD', 'HOST', 'PING'):
            if len(database.get(k)) == 0:
                error:str = f'-{k}: Field cannot be empty'
                entry_error.append(error)
            elif k == 'PING':
                if str(v).lower() not in ('y', 'ye', 'yes', 'n', 'no'):
                    error = f'-{k}: {v} -> PING value must be y or n'
                    entry_error.append(error)

    return entry_error

def validate_db_ip_info(value:str, misc=False):
    if misc:
        c:str = 'MISC'
    else:
        c:str = 'HOST'
    error_log:list[str] = []
    ip_data:list[str] = []
    if '-' in value:
        raw_value:str = value
        step:str = ''
        if '<step=' in value:
            step_index:int = value.index('<step=')
            for i in value[step_index+6:]:
                if i != '>':
                    step += i
                else:
                    break
            step = step.strip()
            if step.isdigit() == False or int(step) == 0:
                error_log.append(f'-{c}: "{raw_value}" -> ' \
                                 f'"<step={step}>" value must be ' \
                                 'an integer higher than "0"')
            value = value.replace(f'<step={step}>', '').strip()
        if value.count('-') > 1:
            value = value.replace('-', '', value.count('-')-1).strip()
        ip_int:list = []
        for ip in value.split('-'):
            ip = ip.strip()
            if ip:
                try:
                    validate_ip(ip)
                except ipaddress.AddressValueError:
                    error_log.append(f'-{c}: "{raw_value}" -> "{ip}" ' \
                                     'is not a valid ip')
                else:
                    ip_int.append(int(ipaddress.IPv4Address(ip)))
                    ip_data.append(ip)
        if step:
            ip_data.append(step)
        else:
            ip_data.append('1')
        if len(ip_int) == 2:
            if ip_int[0] >= ip_int[1]:
                error_log.append(f'-{c}: "{raw_value}" -> Range ip_start ' \
                                 f'"{ip_data[0]}" must be lower ' \
                                 f'than range ip_end "{ip_data[1]}"')
        if len(ip_int) in (0, 1):
            error_log.append(f'-{c}: "{raw_value}" -> It is not a ' \
                             'valid ip range (2 valid ip required ' \
                             'ip_start < ip_end)')
    else:
        try:
            validate_ip(value)
        except ipaddress.AddressValueError:
            error_log.append(f'-{c}: "{value}" is not a valid ip')
            if '<step=' in value:
                error_log.append(f'-{c}: "{value}" unique ip cannot ' \
                                 'contain "step" property')
        else:
            ip_data.append(value)

    return error_log, ip_data

def special_ping(ip:str, n:int=4, l:int=32, w:int=4000, capture_output=True):
    ping_result = ping(ip, n=n, l=l, w=w, capture_output=capture_output)
    
    return ip, ping_result.stdout.strip(), ping_result.returncode

def search_config_files(value:str, path:str, ssh=False):
    commands_in_file:list = []
    data_dict:dict = {}
    filename:str = ''
    pos:int = 0
    error:list[str] = []
    ssh_file_list:list[str] = []
    f_total:int = value.count('<file=')
    for i in range(f_total):
        f_index:int = value.index('<file=', pos)
        for z in value[f_index+6:]:
            if z != '>':
                filename += z
            else:
                break
        filename = filename.strip()
        if ssh:
            ssh_file_list.append(filename)
            filename = ''
            pos = f_index + 1
            continue
        try:
            content:list[str] = load_file(filename, path)
        except FileNotFoundError:
            error.append(f'-COMMANDS: "{value}" -> File [{filename}] ' \
                         'not found in config_files directory')
        else:
            for z in content:
                z = z.strip()
                if z:
                    if z.startswith('#'):
                        pass
                    else:
                        commands_in_file.append(z)
            data_dict[filename] = commands_in_file
        filename = ''
        commands_in_file = []
        pos = f_index + 1
    if ssh:
        return ssh_file_list
    elif len(error) > 0:
        return error
    else:
        return data_dict

def create_cfg_db(config:list[str]):
    cfg_dict:dict = {}
    for v in config:
        v = v.strip().lower()
        if (v.startswith('n=') or v.startswith('w=') or v.startswith('l=') or
            v.startswith('show_ping=') or v.startswith('cpu_ping_threads=') or
            v.startswith('port=') or v.startswith('device_type=') or
            v.startswith('cpu_ssh_threads=') or
            v.startswith('reload_and_go_timeout=')
        ):
            v = v.split('=', maxsplit=1)
            cfg_dict[v[0].strip()] = v[1].strip()

    return cfg_dict

def validate_cfg_db(cfg_db:dict[str, str|int]):
    error:list[str] = []
    for k, v in cfg_db.items():
        if k == 'show_ping':
            if v.startswith('ena') or v.startswith('disa'):
                if v.startswith('ena'):
                    cfg_db[k] = True
                else:
                    cfg_db[k] = False
            else:
                error.append(
                    f'Current value in .cfg file: "{k}={v}" -> '
                    f'Value "{k}" must be (enable/disable)'
                )
        elif k in ('n', 'w', 'l', 'cpu_ping_threads', 
                   'cpu_ssh_threads', 'port', 'reload_and_go_timeout'):
            if v.isdigit() and int(v) > 0:
                cfg_db[k] = int(v)
            else:
                error.append(
                    f'Current value in .cfg file: "{k}={v}" -> '
                    f'Value "{k}" must be an integer higher than "0"'
                )
    
    return error, cfg_db

def get_template_cfg_file():
    return template_cfg_file

def ssh_session(device:dict[str, str|int], database:dict, reload_timer:int):
    try:
        if device.get('device_type') == 'autodetect':
            device_vendor:str = SSHDetect(**device).autodetect()
            device['device_type'] = device_vendor
        ssh_connect = ConnectHandler(**device)
    except BaseException as err:
        err = err.__str__().strip().split('\n')[0]
        print(f'SSH {device["host"]} -> NOT Established... {err}')
        log_device:dict = {
            'IP': device['host'],
            'ERR': err
        }
    else:
        print(f'SSH {device["host"]} -> Established...')
        command_list:list[str] = database.get('COMMANDS')
        config_files:dict = database.get('CONFIG_FILES')
        files_to_check_list:list[str] = database.get('FILES')
        final_command_list:list[str] = []
        file_index_db:dict[int, str] = {}
        for c in command_list:
            if '<file=' in c:
                file_list:list[str] = search_config_files(c, '', ssh=True)
                for file in file_list:
                    file_index_db[len(final_command_list)] = f'{file} -> '
                    final_command_list.extend(config_files.get(file))
                    file_index_db[len(final_command_list)] = ''
            else:
                final_command_list.append(c)
        log_commands = fname = ''
        output_hostname:str = ssh_connect.find_prompt()
        error_connect:bool = False
        is_cisco:bool = False
        if 'cisco' in device.get('device_type').lower():
            output_dir:str = ssh_connect.send_command('dir')
            is_cisco = True
        for i, c in enumerate(final_command_list):
            if error_connect:
                break
            if i in file_index_db.keys():
                fname = file_index_db.get(i)
            send_commmand:bool = True
            reload_and_go = False
            enter_and_go = False
            if is_cisco:
                if (
                    c.lower().startswith('copy') or 
                    c.lower().startswith('do copy')
                ):
                    for v in files_to_check_list:
                        if v in output_dir and v in c:
                            print(f'SSH {device["host"]} -> '
                                  f'Performing command [{fname}{c}] |SKIPPED|'
                                  f', {v} already present in device')
                            file_dir:str = ssh_connect.send_command_timing(
                                f'dir | i {v}'
                            ).strip()
                            file_dir = f'| Current dir flash: | {file_dir} |'
                            file_dir = f'{"-"*len(file_dir)}\n{file_dir}\n' \
                                       f'{"-"*len(file_dir)}'
                            output_c = f'SKIPPED, {v} already present ' \
                                       f'in device\n{file_dir}'
                            send_commmand = False
                            break
            if send_commmand:
                print(f'SSH {device["host"]} -> Performing command '
                      f'[{fname}{c}]...')
                if c.lower() == 'enter and go':
                    original_c:str = c
                    c = '\n'
                    enter_and_go:bool = True
                elif 'and go' in c.lower() and 're' in c.lower():
                    original_c:str = c
                    and_go:int = c.lower().index('and go')
                    c = f'{c[:and_go]}{c[and_go+6:]}'.strip()
                    reload_and_go:bool = True
                output_c:str = (
                    ssh_connect.send_command_timing(c, read_timeout=0)
                )
                if is_cisco:
                    if (
                        c.lower().startswith('relo') or 
                        c.lower().startswith('do relo')
                    ):
                        if 'save' in output_c.lower():
                            ssh_connect.send_command_timing('no')
                            output_c += 'no\n'
                        try:   
                            ssh_connect.send_command('\n', read_timeout=3)
                            output_c += '\nReload NOT Performed Successfully'
                        except:
                            output_c += '\nReload Performed Successfully'
                    elif (
                        c.lower().startswith('del') or 
                        c.lower().startswith('do del')
                    ):
                        output_c += ssh_connect.send_command_timing('\n')
                        if 'error' not in output_c.lower():
                            output_c += '\nFile Deleted Successfully'
                    elif (
                        c.lower().startswith('wr') or
                        c.lower().startswith('do wr')
                    ):
                        if 'era' in c.lower():  # wr erase
                            output_c += (
                                f'\n{ssh_connect.send_command_timing("\n")}'
                            )
                        else:
                            output_c += f'[OK]'
                            ssh_connect.send_command_timing('\n') # Avoid [OK] output in next command
                    elif (
                        (c.lower().startswith('inst') or 
                         c.lower().startswith('do inst')) and 
                        'rem' in c.lower() and 'ina' in c.lower()
                    ):
                        buffer:str = (
                            ssh_connect.read_until_prompt_or_pattern(
                                pattern=r'y/n', 
                                read_timeout=0
                            )
                        )
                        if 'y/n' in buffer.lower():
                            ssh_connect.send_command_timing('y')
                            output_c = f'{buffer}] y\n'
                            output_c += ssh_connect.read_until_prompt(
                                read_timeout=0
                            )
                        else:
                            output_c = buffer
                        output_c = output_c.replace(
                            ssh_connect.base_prompt, 
                            ''
                        )
                        ssh_connect.send_command_timing('\n') # Avoid weird prompt
                if reload_and_go or enter_and_go:
                    c = original_c
                print(f'SSH {device["host"]} -> Performing command '
                      f'[{fname}{c}]... |DONE|')
                if reload_and_go:
                    for i in range(reload_timer*2):
                        print(f'SSH {device["host"]} -> |WAITING| '
                              f'[{fname}{c}] Attempt {str(i+1).zfill(2)}/20 '
                              'to restablish connection...')
                        try:
                            ssh_connect = ConnectHandler(**device)
                            break
                        except:
                            time.sleep(30)
                    if ssh_connect.is_alive():
                        print(f'SSH {device["host"]} -> |SUCCESS| '
                              f'[{fname}{c}] Connection restablished...')
                        ssh_connect.send_command_timing('\n')  # Avoid weird prompt
                    else:
                        print(f'SSH {device["host"]} -> |WAITING| '
                              f'[{fname}{c}] Connection NOT restablished...')
                        print(f'SSH {device["host"]} -> |ERROR| '
                              f'[{fname}{c}] Aborting SSH Session...')
                        output_c += '\nSSH session could NOT be ' \
                                    'restablished. REST of the SSH session ' \
                                    'ABORTED...'
                        error_connect = True
            log_commands += f'\n\n{"-"*150}\n' \
                            f'[{fname}{c}]\n{"#"*145}\n{output_c.strip()}' \
                            f'\n{"#"*145}\n{"-"*150}'
        ssh_connect.disconnect()
        print(f'SSH {device["host"]} -> Session Finished')
        log_device:dict = {
            'IP': device['host'],
            'HOSTNAME': output_hostname[:-1],
            'COMMAND HISTORY': log_commands
        }

    return log_device