import re

def extract_only_ips(filename='nmap.txt'):
    """Извлекает ТОЛЬКО валидные IP-адреса, исключая домены"""
    
    with open(filename, 'r') as f:
        content = f.read()
    
    # Паттерн для строгой проверки IP-адресов
    # Проверяем что каждая октет в диапазоне 0-255
    ip_pattern = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
    
    matches = re.findall(ip_pattern, content)
    
    # Удаляем дубликаты
    unique_ips = list(dict.fromkeys(matches))
    
    return unique_ips

# Использование
ips = extract_only_ips('nmap.txt')
print(f"Найдено {len(ips)} уникальных IP-адресов:\n")
for ip in ips:
    print(ip)

# Сохраняем в файл
with open('live_ips.txt', 'w') as f:
    for ip in ips:
        f.write(ip + '\n')

print(f"\nРезультат сохранен в live_ips.txt")
