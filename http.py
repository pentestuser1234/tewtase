import re
import sys

def extract_http_ports(nmap_file):
    """
    Извлекает все HTTP порты из Nmap txt файла
    
    Args:
        nmap_file: путь к Nmap txt файлу
    
    Returns:
        список строк в формате ip:port
    """
    try:
        with open(nmap_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        results = []
        
        # Разбиваем на блоки по хостам
        # Ищем паттерн "Nmap scan report for" или IP адреса
        lines = content.split('\n')
        
        current_ip = None
        
        for line in lines:
            # Ищем строку с IP адресом хоста
            # Формат: "Nmap scan report for hostname (ip)" или просто "ip"
            ip_match = re.search(r'Nmap scan report for.*?\((\d+\.\d+\.\d+\.\d+)\)', line)
            if not ip_match:
                # Альтернативный формат - просто IP в начале строки
                ip_match = re.match(r'^(\d+\.\d+\.\d+\.\d+)', line.strip())
            
            if ip_match:
                current_ip = ip_match.group(1)
                continue
            
            # Если нашли IP и строка содержит информацию о порте
            if current_ip:
                # Ищем строки с открытыми портами
                # Формат: "PORT     STATE SERVICE"
                #         "80/tcp   open  http"
                port_match = re.match(r'\s*(\d+)/tcp\s+open\s+(\S+)', line)
                
                if port_match:
                    port = port_match.group(1)
                    service = port_match.group(2).lower()
                    
                    # Проверяем, является ли это HTTP сервисом
                    http_services = ['http', 'https', 'http-proxy', 'http-alt']
                    
                    if service in http_services:
                        results.append(f"{current_ip}:{port}")
    
    except FileNotFoundError:
        print(f"Ошибка: файл '{nmap_file}' не найден")
        return []
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return []
    
    return results


def main():
    # Если передан аргумент командной строки - используем его
    if len(sys.argv) > 1:
        nmap_file = sys.argv[1]
    else:
        # По умолчанию ищем scan.txt
        nmap_file = "scan.txt"
        print(f"Файл не указан, используется по умолчанию: {nmap_file}")
    
    print(f"Обработка файла: {nmap_file}\n")
    
    http_ports = extract_http_ports(nmap_file)
    
    if http_ports:
        print("Найденные HTTP порты:")
        print("-" * 30)
        for port_info in http_ports:
            print(port_info)
        print("-" * 30)
        print(f"\nВсего найдено: {len(http_ports)} HTTP портов")
    else:
        print("HTTP порты не найдены")


if __name__ == "__main__":
    main()
