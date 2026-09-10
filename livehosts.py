import re

def extract_ips_from_nmap(filename='nmap.txt'):
    """Извлекает живые IP-адреса из файла результатов nmap"""
    ips = []
    
    with open(filename, 'r') as f:
        content = f.read()
    
    # Паттерн для поиска IP-адресов в выводе nmap
    # Ищет строки вида "Nmap scan report for hostname (IP)" или просто IP
    ip_pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    
    matches = re.findall(ip_pattern, content)
    
    # Убираем дубликаты, сохраняя порядок
    seen = set()
    unique_ips = []
    for ip in matches:
        if ip not in seen:
            seen.add(ip)
            unique_ips.append(ip)
    
    return unique_ips

# Использование
ips = extract_ips_from_nmap('nmap.txt')
print(f"Найдено {len(ips)} уникальных IP:")
for ip in ips:
    print(ip)

# Сохранить в файл для дальнейшего использования
with open('live_ips.txt', 'w') as f:
    for ip in ips:
        f.write(ip + '\n')
