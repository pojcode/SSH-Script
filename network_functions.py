import ipaddress, subprocess

def validate_ip(ip:str):
    return ipaddress.IPv4Address(ip)

def create_ip_range(ip_start:str, ip_end:str, step:int=1):
    ip_list:list[str] = []
    ip_start = ipaddress.IPv4Address(ip_start)
    ip_end = ipaddress.IPv4Address(ip_end)
    for ip in range(int(ip_start), int(ip_end)+1, step):
        ip_list.append(str(ipaddress.IPv4Address(ip)))

    return ip_list

def sort_ip(values:list|tuple|set, reverse=False):
    sorted_ip_list:list[str] = []
    new_list:list = []
    for v in values:
        int_ip:int = int(ipaddress.ip_address(v))
        new_list.append(int_ip)
    new_list = sorted(new_list, reverse=reverse)
    for v in new_list:
        v = str(ipaddress.IPv4Address(v))
        sorted_ip_list.append(v)

    return sorted_ip_list

def ping(ip:str, t:bool=False, n:int=4, l:int=32, w:int=4000,
         capture_output=False):
    if t:
        ping = subprocess.run(f'ping {ip} -t -w {w} -l {l}', 
                              capture_output=capture_output, text=True)
    else:
        ping = subprocess.run(f'ping {ip} -n {n} -w {w} -l {l}', 
                              capture_output=capture_output, text=True)

    return ping