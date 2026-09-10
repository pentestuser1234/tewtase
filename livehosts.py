import re

def extract_live_hosts(filename='nmap.txt'):
    """Извлекает только активные хосты из nmap скана"""
    live_ips = []
    
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    current_ip = None
    
    for line in lines:
        # Ищем строку с IP-адресом
        ip_match = re.search(r'Nmap scan report for\s+.*?\((\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\)', line)
        
        if ip_match:
            current_ip = ip_match.group(1)
        
        # Проверяем статус хоста
        if current_ip and ('Host is up' in line or 'ports scanned' in line.lower()):
            live_ips.append(current_ip)
            current_ip = None
    
    # Удаляем дубликаты
    unique_ips = list(dict.fromkeys(live_ips))
    
    return unique_ips

# Использование
live_ips = extract_live_hosts('nmap.txt')
print(f"Активных хостов: {len(live_ips)}")
for ip in live_ips:
    print(ip)
