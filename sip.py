#!/usr/bin/env python3
"""
SIP Information Collector - Базовый сбор информации о SIP-сервере
Использование: python sip_recon.py <target> [-p PORT] [--full]
"""

import socket
import sys
from datetime import datetime


class SIPInfoCollector:
    """Класс для сбора базовой информации о SIP-сервере"""
    
    def __init__(self, target):
        self.target = target
        self.results = {}
        
    def check_port(self, port, timeout=2):
        """Проверка доступности UDP порта с отправкой OPTIONS запроса"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            
            # Формируем SIP OPTIONS запрос
            options_msg = (
                f"OPTIONS sip:{self.target} SIP/2.0\r\n"
                f"Via: SIP/2.0/UDP {self.target}:5060;branch=z9hG4K\r\n"
                f"Max-Forwards: 70\r\n"
                f"To: <sip:{self.target}>\r\n"
                f"From: <sip:test@{self.target}>;tag=1234\r\n"
                f"Call-ID: test123\r\n"
                f"CSeq: 1 OPTIONS\r\n"
                f"Contact: <sip:test@{self.target}>\r\n"
                f"User-Agent: SIP-Recon-Tool/1.0\r\n"
                f"Content-Length: 0\r\n"
                f"\r\n"
            ).encode()
            
            sock.sendto(options_msg, (self.target, port))
            
            try:
                data, addr = sock.recvfrom(8192)
                sock.close()
                response = data.decode('utf-8', errors='ignore')
                return True, response
            except socket.timeout:
                sock.close()
                return True, None  # Порт открыт, но нет ответа
                
        except Exception as e:
            return False, str(e)
    
    def scan_common_ports(self):
        """Сканирование стандартных SIP портов"""
        common_ports = [5060, 5061, 5038, 4569, 5062, 5063]
        print(f"\n[*] Сканирование стандартных портов на {self.target}...")
        
        open_ports = []
        for port in common_ports:
            is_open, response = self.check_port(port)
            status = "OPEN" if is_open else "CLOSED"
            print(f"  Порт {port}: {status}")
            
            if is_open:
                open_ports.append(port)
                if response:
                    self.results[port] = response
        
        return open_ports
    
    def send_options_request(self, port=5060):
        """Отправка SIP OPTIONS запроса для получения информации"""
        print(f"\n[*] Отправка OPTIONS запроса на порт {port}...")
        
        is_open, response = self.check_port(port)
        
        if not is_open:
            print(f"[-] Порт {port} недоступен")
            return None
        
        if response:
            print(f"[+] Получен ответ:")
            print(response)
            
            # Парсим заголовки
            headers = self.parse_sip_headers(response)
            self.results['options_response'] = headers
            
            return response
        else:
            print("[-] Нет ответа от сервера")
            return None
    
    def parse_sip_headers(self, response):
        """Парсинг SIP заголовков"""
        headers = {}
        lines = response.split('\r\n')
        
        for line in lines:
            if ':' in line and not line.startswith('SIP/'):
                key, _, value = line.partition(':')
                headers[key.strip()] = value.strip()
        
        return headers
    
    def display_results(self):
        """Отображение результатов"""
        print("\n" + "="*60)
        print("РЕЗУЛЬТАТЫ СКАНИРОВАНИЯ")
        print("="*60)
        
        if self.results:
            for key, value in self.results.items():
                print(f"\n[{key.upper()}]:")
                if isinstance(value, dict):
                    for k, v in value.items():
                        print(f"  {k}: {v}")
                elif isinstance(value, str):
                    print(f"  {value[:300]}")
        else:
            print("Нет полученных данных")
        
        print("\n" + "="*60)


def main():
    if len(sys.argv) < 2:
        print("Использование: python sip_recon.py <target> [-p PORT]")
        print("Пример: python sip_recon.py 192.168.1.100")
        sys.exit(1)
    
    target = sys.argv[1]
    port = 5060
    
    # Проверяем наличие аргумента порта
    if '-p' in sys.argv:
        idx = sys.argv.index('-p')
        if idx + 1 < len(sys.argv):
            port = int(sys.argv[idx + 1])
    
    print("="*60)
    print("SIP INFORMATION COLLECTOR v1.0")
    print("="*60)
    print(f"Цель: {target}")
    print(f"Порт: {port}")
    print(f"Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    collector = SIPInfoCollector(target)
    
    # Шаг 1: Сканирование портов
    open_ports = collector.scan_common_ports()
    
    # Шаг 2: OPTIONS запрос
    collector.send_options_request(port)
    
    # Отображение результатов
    collector.display_results()
    
    print(f"\n[!] Завершено в {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
