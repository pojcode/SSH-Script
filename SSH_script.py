import os, concurrent.futures, time, datetime, sys
from app.app_functions import *

def main():
    MAIN_PATH:str = os.getcwd()
    THIS_FILE:str = os.path.basename(sys.argv[0])
    for i, v in enumerate(THIS_FILE):
        if v == '.':
            last_dot:int = i
    DATA_FILE:str = f'{THIS_FILE[:last_dot]}_data_file.txt'
    CFG_FILE:str = f'{THIS_FILE[:last_dot]}.cfg'
    DATABASE:dict = {}
    HOST_OS:str = check_OS()
    if HOST_OS == 'nt':  # Windows
        sep:str = '\\'
    else:
        sep = '//'
    banner_title:str = (f'>>|    {THIS_FILE} RUNNING -- You can exit script '
                        'pressing "Ctrl+C" or closing window at '
                        'any time    |<<')
    banner_title = text_to_box(banner_title, box_line='=')
    clear_console()
    print(f'{banner_title}\n')
    # Load data_file.txt -----------------------------------------------------
    try:
        data_file_raw = load_file(DATA_FILE, MAIN_PATH)
    except FileNotFoundError:
        while True:
            clear_console()
            print(banner_title)
            print(f'\n|ERROR| --- File [{DATA_FILE}] not found...\n')
            resp = input(f'>> Create blank [{DATA_FILE}]? (y/n) -> ').lower()
            if resp in ('y', 'ye', 'yes'):
                data_file_text:str = get_template_data_file()
                save_file(DATA_FILE, data_file_text, MAIN_PATH)
                print(f'\n[{DATA_FILE}] Created Successfully...')
                break
            elif resp in ('n', 'no'):
                break
            else:
                print('\n\tInvalid Option...')
                time.sleep(2)
        input('\nPress Enter to exit script...')
        exit()
    else:
       DATABASE = create_db(data_file_raw)
    # Print data_file.txt config ---------------------------------------------
    data_f_table:str = create_data_table(DATABASE, f'[{DATA_FILE}]')
    print(data_f_table)
    # Check mandatory DATABASE entries ---------------------------------------
    error_list:list[str] = check_db_mandatory_entries(DATABASE)
    # Check, validate and manage IP info -------------------------------------
    ip_info:list[str] = DATABASE.get('HOST')
    DATABASE['HOSTDATA'] = []
    for v in ip_info:
        error, ip_data = validate_db_ip_info(v)
        error_list.extend(error)
        DATABASE['HOSTDATA'].append(ip_data)
    ip_info:list[str] = DATABASE.get('MISC')
    DATABASE['MISCDATA'] = []
    for v in ip_info:
        error, ip_data = validate_db_ip_info(v, misc=True)
        error_list.extend(error)
        DATABASE['MISCDATA'].append(ip_data)
    # Check config files -----------------------------------------------------
    DATABASE['CONFIG_FILES'] = {}
    command_list:list[str] = DATABASE.get('COMMANDS')
    try:
        create_dir('config_files', MAIN_PATH)
    except FileExistsError:
        pass
    config_f_path:str = f'{MAIN_PATH}{sep}config_files'
    for c in command_list:
        if '<file=' in c:
            config_f_info:dict|list[str] = search_config_files(c, config_f_path)
            if type(config_f_info) == list:
                error_list.extend(config_f_info)
            else:
                config_f_db:dict = DATABASE.get('CONFIG_FILES')
                for k, v in config_f_info.items():
                    config_f_db[k] = v
                DATABASE['CONFIG_FILES'] = config_f_db
    # Print and manage errors or continue running script ---------------------
    if len(error_list) > 0:
        zeros:int = len(str(len(error_list)))
        print()
        for i, v in enumerate(error_list):
            print(f'|ERROR {str(i+1).zfill(zeros)}| [{DATA_FILE}] {v}')
        input('\nPress Enter to exit script...')
        exit()
    else:
        input(f'\nIf [{DATA_FILE}] data is OK, press Enter to continue...')
        time_start:float = time.time()
    # Load .cfg or .ini file -------------------------------------------------
    cfg_db:dict = {
        'n': 2,
        'w': 1000,
        'l': 32,
        'show_ping': False,
        'cpu_ping_threads': 250,
        'device_type': 'autodetect',
        'port': 22,
        'cpu_ssh_threads': 90
    }
    try:
        cgf_config:list[str] = load_file(CFG_FILE, MAIN_PATH)
    except FileNotFoundError:
        print(f'\n|WARNING| File [{CFG_FILE}] not found... creating file... ',
              end='')
        cfg_text:str = get_template_cfg_file()
        save_file(CFG_FILE, cfg_text, MAIN_PATH)
        time.sleep(2)
        print('|DONE|')
        print(f'\nUsing default values... {cfg_db}\n')
    except:
        print(f'\n|WARNING| There was an issue importing [{CFG_FILE}]')
        print(f'\nUsing default values... {cfg_db}\n')
        pass
    else:
        cfg_db_temp:dict = create_cfg_db(cgf_config)
        error, cfg_db_temp = validate_cfg_db(cfg_db_temp)
        if len(error) == 0:
            for k, v in cfg_db_temp.items():
                cfg_db[k] = v
            print(f'\nUsing [{CFG_FILE}] -> {cfg_db}\n')
        else:
            print(f'\n|WARNING| File [{CFG_FILE}] contains syntax errors')
            for v in error:
                print(f'  {v}')
            print(f'\nUsing default values... {cfg_db}\n')
    # Create a list with all ips ---------------------------------------------
    for i in range(2):  # i=0 -> HOST, i=1 -> MISC
        ip_list:list[str] = []
        if i == 1:
            keyword:str = 'MISC'
        else:
            keyword:str = 'HOST'
        for v in DATABASE.get(f'{keyword}DATA'):
            if len(v) == 1:
                ip_list.append(v[0])
            else:
                ip_range:list = create_ip_range(v[0], v[1], int(v[2]))
                for z in ip_range:
                    ip_list.append(z)
        if i == 1:
            total_misc_list:list[str] = ip_list 
        else:
            total_host_list:list[str] = ip_list
    total_host_list = sort_ip(set(total_host_list))
    total_misc_list = sort_ip(set(total_misc_list))
    # Initialize logs variables ----------------------------------------------
    log:str = ''
    log_global_summary:str = 'GLOBAL SUMMARY:\n\n'
    # Pings ------------------------------------------------------------------
    do_ping:str = DATABASE.get('PING')
    if do_ping.lower() in ('y', 'ye', 'yes'):
        for i in range(2):  # i=0 -> HOST, i=1 -> MISC
            with (concurrent.futures.ThreadPoolExecutor(
                max_workers=cfg_db.get('cpu_ping_threads')) as exec
            ):
                if i == 1:
                    keylist:list = total_misc_list
                    keyword:str = 'MISC'
                else:
                    keylist:list = total_host_list
                    keyword = 'HOST'
                    pingable_host_list:list[str] = []
                if len(keylist) > 0:
                    print(
                        '\n'
                        f'{text_to_box(f"## STARTING {keyword} IP PINGS ##")}'
                    )
                    log += f'\n\n{keyword} PING SUMMARY:\n'
                futures:list = []
                temp_list:list[tuple[str, str, int]] = []
                for ip in keylist:
                    futures.append(
                        exec.submit(
                            special_ping, ip, n=cfg_db.get('n'), 
                            w=cfg_db.get('w'), l=cfg_db.get('l')
                        )
                    )
            for future in concurrent.futures.as_completed(futures):
                temp_list.append(future.result())
            sorted_temp_list = []
            for v in temp_list:
                sorted_temp_list.append(v[0])
            sorted_temp_list = sort_ip(sorted_temp_list)
            final_temp_list:list[tuple[str, str, int]] = []
            for v in sorted_temp_list:
                for z in temp_list:
                    if v == z[0]:
                        final_temp_list.append(z)
                        break
            ping_banner:str = ''
            counter:int = 0
            for v in final_temp_list:
                if 'ttl' in v[1].lower() and v[2] == 0:
                    if keyword == 'HOST':
                        pingable_host_list.append(v[0])
                    status:str = 'Successful'
                    counter += 1
                else:
                    status = 'NOT Replying'
                if cfg_db.get('show_ping'):
                    print(f'{"-"*60}\n{v[1]}\n{"-"*60}')
                ping_banner += f'\n{keyword} {v[0]} -> {status}...'
                log += f'\n\t- {v[0]} -> {status}'
            if ping_banner:
                print(ping_banner)
            log_global_summary += (
                f'\t-TOTAL {keyword} PINGS -> {len(final_temp_list)}'
                f'{" "*4}-SUCCESSFUL {keyword} PINGS -> {counter}\n'
            )
        print(f'\n{text_to_box("## PINGS DONE ##")}')
    else:
        print(f'\n{text_to_box("## PING SKIPPED... ##")}')
        log += f'\n\n{text_to_box(" PING SKIPPED ")}'
    # SSH sessions -----------------------------------------------------------
    print(f'\n{text_to_box("## STARTING SSH SESSIONS ##")}\n')
    if do_ping.lower() in ('y', 'ye', 'yes'):
        ip_ssh_list:list[str] = pingable_host_list
    else:
        ip_ssh_list = total_host_list
    with (concurrent.futures.ThreadPoolExecutor(
        max_workers=cfg_db.get('cpu_ssh_threads')) as exec
    ):
        futures:list = []
        for ip in ip_ssh_list:
            device = {
            'device_type': cfg_db.get('device_type'),
            'host': ip,
            'username': DATABASE.get('USERNAME'),
            'password': DATABASE.get('PASSWORD'),
            'port': cfg_db.get('port')    # default to 22
            }
            futures.append(exec.submit(ssh_session, device, DATABASE))
    ip_ssh_info:list[dict] = []
    for future in concurrent.futures.as_completed(futures):
        ip_ssh_info.append(future.result())
    sorted_ip_ssh_info:list[str] = []
    for v in ip_ssh_info:
        sorted_ip_ssh_info.append(v.get('IP'))
    sorted_ip_ssh_info = sort_ip(sorted_ip_ssh_info)
    final_ip_ssh_info:list[dict] = []
    for v in sorted_ip_ssh_info:
        for i in ip_ssh_info:
            if v == i.get('IP'):
                final_ip_ssh_info.append(i)
                break
    log += f'\n\nSSH SESSION SUMMARY:\n'
    log_devices:str = ''
    counter = 0
    for data in final_ip_ssh_info:
        if 'ERR' in data.keys():
            status = f'NOT Established... {data.get('ERR')}'
        else:
            status = f'Established'
            counter += 1
            log_devices += f'{"="*155}'
            for k, v in data.items():
                log_devices += f'\n{k}: {v}'
            log_devices += f'\n{"="*155}\n\n'
        log += f'\n\t- {data.get('IP')} -> {status}'
    if log_devices:
        log += f'\n\nCOMMANDS SUMMARY:\n\n{log_devices.strip()}'
    log_global_summary += f'\t-TOTAL SSH SESSIONS -> {len(ip_ssh_list)}' \
                          f'{" "*4}-ESTABLISHED SSH SESSIONS -> {counter}'
    print(f'\n{text_to_box("## SSH SESSIONS DONE ##")}')
    # Save log in to a .txt file ---------------------------------------------
    date = log_file = datetime.datetime.now()
    date = date.strftime(f'--- Log created: %A %d %B %Y - %H:%M:%S  ||  ')
    log_file = f'{log_file.strftime(f"%d-%m-%Y_time_%H.%M.%S")}_' \
               f'{THIS_FILE[:last_dot]}_log.txt'
    time_end:float = time.time()
    time_total:float = time_end - time_start
    if time_total >= 60:
        time_total = time_total / 60
        time_unit = 'minutes'
    else:
        time_unit = 'seconds'
    run_time = f'Script running time -> {time_total:.2f} {time_unit} ---'
    log = f'{date}{run_time}\n\n{data_f_table}\n\n{log_global_summary}{log}'
    try:
        create_dir('logs', MAIN_PATH)
    except FileExistsError:
        pass
    except PermissionError:
        print(f'\n|WARNING| --- logs directory -> [{MAIN_PATH}{sep}logs] '
              'could NOT be created (Permission Error)')
    try:
        save_file(log_file, log.strip(), f'{MAIN_PATH}{sep}logs')
    except FileNotFoundError:
        print(f'\n|WARNING| --- logs directory -> [{MAIN_PATH}{sep}logs] '
              'not found. Log file not created...')
    except PermissionError:
        print(f'\n|WARNING| --- Log file -> '
              f'[{MAIN_PATH}{sep}logs{sep}{log_file}] '
              'could NOT be created (Permission Error)')
    else:
        print(f'\nLog file created -> [logs{sep}{log_file}]')
    print(f'\n--- {run_time}')
    input('\nPress Enter to exit script...')

if __name__ == '__main__':
    main()