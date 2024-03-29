'''
SSH_script - Templates
Templates for XXXX_data_file.txt and XXXX.cfg
'''

template_data_file:str = (
    f' {"-"*83}\n'
    ' |>>|    SCRIPT to perform SSH commands to multiple devices at the '
    'same time    |<<|\n'
    f' {"-"*83}\n\n'
    f'{"-"*152}\n'
    '### -USERNAME: Windfarm device username (Mandatory)\n'
    f'{"-"*152}\n'
    '### -PASSWORD: Windfarm device password (Mandatory)\n'
    f'{"-"*152}\n'
    '### -HOST: Host IP (Mandatory), All commands and pings will be '
    'performed. You can concatenate unique ip and '
    f'ranges(ip_start - ip_end) using ","\n'
    f'{" "*11}(e.g. -> 192.168.1.1 - 192.168.1.5 <step=2>, 192.168.1.8, '
    '192.168.1.10, 192.168.1.15 - 192.168.1.25)\n'
    f'{" "*11}(Step Property: You can add '
    'step to ranges e.g. -> 192.168.1.1 - 192.168.1.5 <step=2> -> '
    'only .1, .3, .5 will be used)\n'
    f'{"-"*152}\n'
    '### -MISC: Misc IP (Optional) No command will be performed, just pings.'
    ' You can concatenate as before.\n'
    f'{"-"*152}\n'
    '### -PING: (Optional, y/n), "y" to perform pings, "n" to do not. '
    'Used to filter ssh sessions just to reachable hosts instead of all.\n'
    f'{"-"*152}\n'
    '### -FILES: (Optional, only Cisco vendor) You can concatenate filenames '
    'using "," (e.g. -> any.txt, WF-TO-SW-05.cfg, ios-17.06.05-SPA.bin)\n'
	f'{" "*12}Script will check if file is already in device flash and if '
    'yes, it will skip the copy commands. Leave blank, will force copy.\n'
    f'{"-"*152}\n'
    '### -COMMANDS: (Optional) You will need to provide commands to enter '
    f'config mode or exit if needed.\n{" "*15}(Only Cisco vendor) reload, '
    'delete, wr erase and install remove inactive commands, '
    'no extra input is required\n'
    f'{" "*15}Typing enter and go will send return/enter to device\n{" "*15}'
    'Typing command to reboot + and go (e.g. reload and go) will wait to '
    'SSH session to be restablished and will continue performing commands\n'
    f'{" "*15}You can use external files located in '
    'config_files directory typing <file=any.txt> Script will take commands '
    'located in "any.txt"\n'
    f'{"-"*152}\n\n'
    '-USERNAME: \n'
    '-PASSWORD: \n'
    '-HOST: \n'
    '-MISC: \n'
    '-PING: y\n'
    '-FILES: \n\n'
    '-COMMANDS: Paste your commands below. One command per line. '
    'Do not delete this line.\n\n'
)

template_cfg_file:str = (
    '### PING OPTIONS ###\n'
    f'  {"-"*86}\n'
    f'  | "n" -> Number of pings to send{" "*53}|\n'
    f'  | "w" -> (Miliseconds) time to wait for ping replies{" "*33}|\n'
    f'  | "l" -> (Bytes) ping packets size{" "*51}|\n'
    '  | "show_pings" -> Show ping process and result (enable) '
    f'or just result (disable){" "*5}|\n'
    '  | "cpu_ping_threads" -> Number of threads cpu will use to perform '
    'asynchronous pings |\n'
    f'  {"-"*86}\n\n'
    'n=2\n'
    'w=1000\n'
    'l=32\n'
    'show_ping=disabled\n'
    'cpu_ping_threads=250\n\n\n'
    '### SSH OPTIONS ###\n'
    f'  {"-"*92}\n'
    '  | "device_type" -> Device vendor for ssh commands. '
    f'See attached files...{" "*19}|\n'
    f'  | "port" -> SSH port to perform SSH sessions{" "*47}|\n'
    '  | "reload_and_go_timeout" -> (Minutes) Time to restablish SSH '
    'session after reload command |\n'
    '  | "cpu_ssh_threads" -> Number of threads cpu will use to perform '
    'asynchronous SSH sessions |\n'
    f'  {"-"*92}\n\n'
    'device_type=autodetect\n'
    'port=22\n'
    'reload_and_go_timeout=10\n'
    'cpu_ssh_threads=90'
)