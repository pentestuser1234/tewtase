#!/usr/bin/env python3
"""SIP recon: собирает максимум информации о SIP-сервере.

Проверяет несколько транспортов (UDP/TCP/TLS), несколько методов
(OPTIONS/REGISTER/INVITE), извлекает digest-auth параметры (realm/nonce/algorithm),
фингерпринтит сервер и сканирует частые SIP-порты.

Использовать ТОЛЬКО против систем, на тестирование которых есть письменное разрешение.
"""

import argparse
import random
import re
import socket
import ssl
import string
import sys

COMMON_PORTS = [5060, 5061, 5062, 5080, 5090, 6050]
METHODS = ["OPTIONS", "REGISTER", "INVITE", "SUBSCRIBE"]

INTERESTING_HEADERS = [
    "server", "user-agent", "allow", "allow-events", "supported", "accept",
    "warning", "contact", "www-authenticate", "proxy-authenticate", "p-asserted-identity",
    "remote-party-id", "organization", "call-info", "unsupported", "require",
]


def rand_tag(n=10):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def build_request(method, target_ip, port, local_ip, local_port, transport, domain=None):
    domain = domain or target_ip
    branch = "z9hG4bK" + rand_tag(16)
    call_id = rand_tag(24)
    tag = rand_tag(8)
    proto = transport.upper()
    if proto == "TLS":
        proto = "TLS"  # via показывает TLS для sips
    lines = [
        f"{method} sip:{domain} SIP/2.0",
        f"Via: SIP/2.0/{proto} {local_ip}:{local_port};branch={branch};rport",
        "Max-Forwards: 70",
        f"From: <sip:100@{domain}>;tag={tag}",
        f"To: <sip:100@{domain}>",
        f"Call-ID: {call_id}@{local_ip}",
        f"CSeq: 1 {method}",
        f"Contact: <sip:100@{local_ip}:{local_port}>",
        "User-Agent: sip-recon/2.0",
        "Accept: application/sdp",
    ]
    if method == "REGISTER":
        lines[3] = f"From: <sip:100@{domain}>;tag={tag}"
        lines.append("Expires: 60")
    body = ""
    if method == "INVITE":
        body = (
            "v=0\r\n"
            f"o=recon 0 0 IN IP4 {local_ip}\r\n"
            "s=recon\r\n"
            f"c=IN IP4 {local_ip}\r\n"
            "t=0 0\r\n"
            "m=audio 10000 RTP/AVP 0\r\n"
            "a=rtpmap:0 PCMU/8000\r\n"
        )
        lines.append("Content-Type: application/sdp")
    lines.append(f"Content-Length: {len(body)}")
    return "\r\n".join(lines) + "\r\n\r\n" + body


def send_udp(target_ip, port, payload, timeout):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    try:
        s.connect((target_ip, port))
        local_ip, local_port = s.getsockname()
        s.send(payload.encode() if isinstance(payload, str) else payload)
        data, _ = s.recvfrom(65535)
        return data.decode(errors="replace"), local_ip, local_port
    except (socket.timeout, OSError):
        return None, None, None
    finally:
        s.close()


def send_tcp(target_ip, port, build_fn, timeout, use_tls=False):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((target_ip, port))
        local_ip, local_port = s.getsockname()
        sock = s
        if use_tls:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            sock = ctx.wrap_socket(s, server_hostname=target_ip)
        payload = build_fn(local_ip, local_port)
        sock.send(payload.encode())
        data = sock.recv(65535)
        cert_info = None
        if use_tls:
            cert = sock.getpeercert(binary_form=False)
            cert_info = cert or "present (no readable fields)"
        return data.decode(errors="replace"), cert_info
    except (socket.timeout, OSError, ssl.SSLError) as e:
        return None, f"err: {e}"
    finally:
        s.close()


def parse_response(raw):
    lines = raw.split("\r\n")
    status = lines[0] if lines else ""
    headers = {}
    for line in lines[1:]:
        if not line.strip():
            break
        if ":" in line:
            key, _, val = line.partition(":")
            headers[key.strip().lower()] = val.strip()
    return status, headers


def extract_auth(headers):
    auth = headers.get("www-authenticate") or headers.get("proxy-authenticate")
    if not auth:
        return None
    out = {}
    for field in ["realm", "nonce", "algorithm", "qop", "opaque", "domain"]:
        m = re.search(rf'{field}="?([^",]+)"?', auth, re.IGNORECASE)
        if m:
            out[field] = m.group(1)
    return out


def probe_udp_method(target_ip, port, method, timeout, domain):
    dummy = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dummy.connect((target_ip, port))
    local_ip, local_port = dummy.getsockname()
    dummy.close()
    req = build_request(method, target_ip, port, local_ip, local_port, "UDP", domain)
    raw, _, _ = send_udp(target_ip, port, req, timeout)
    return raw


def print_headers(headers):
    for h in INTERESTING_HEADERS:
        if h in headers:
            print(f"      {h}: {headers[h]}")


def main():
    ap = argparse.ArgumentParser(description="SIP deep recon")
    ap.add_argument("target", help="IP или хост SIP-сервера")
    ap.add_argument("-p", "--port", type=int, help="один порт (иначе скан частых)")
    ap.add_argument("-t", "--timeout", type=float, default=3.0)
    ap.add_argument("-d", "--domain", help="SIP domain (по умолчанию = target)")
    ap.add_argument("--tls", action="store_true", help="пробовать TLS на 5061")
    args = ap.parse_args()

    try:
        target_ip = socket.gethostbyname(args.target)
    except socket.gaierror as e:
        print(f"[!] Не удалось разрешить {args.target}: {e}")
        sys.exit(1)

    domain = args.domain or args.target
    ports = [args.port] if args.port else COMMON_PORTS
    print(f"[*] Цель: {args.target} ({target_ip}), домен SIP: {domain}")
    print(f"[*] Порты: {ports}\n")

    fingerprint = {}

    for port in ports:
        print(f"=== Порт {port}/udp ===")
        # OPTIONS сначала — самый информативный
        raw = probe_udp_method(target_ip, port, "OPTIONS", args.timeout, domain)
        if raw is None:
            print("  [-] UDP: нет ответа\n")
        else:
            status, headers = parse_response(raw)
            print(f"  [+] OPTIONS -> {status}")
            print_headers(headers)
            for k in ("server", "user-agent"):
                if k in headers:
                    fingerprint[k] = headers[k]
            auth = extract_auth(headers)
            if auth:
                print(f"      [auth] digest: {auth}")

            # Перебор методов — разные ответы раскрывают конфигурацию
            for method in ("REGISTER", "INVITE", "SUBSCRIBE"):
                r = probe_udp_method(target_ip, port, method, args.timeout, domain)
                if r:
                    st, hd = parse_response(r)
                    print(f"  [+] {method} -> {st}")
                    a = extract_auth(hd)
                    if a:
                        print(f"      [auth] {method} digest realm={a.get('realm')} "
                              f"algo={a.get('algorithm')} qop={a.get('qop')}")
                    for h in ("www-authenticate", "proxy-authenticate", "allow", "warning"):
                        if h in hd and h not in ("www-authenticate", "proxy-authenticate"):
                            print(f"      {h}: {hd[h]}")
                else:
                    print(f"  [-] {method} -> нет ответа")
            print()

        # TCP
        def build_tcp(li, lp, _port=port):
            return build_request("OPTIONS", target_ip, _port, li, lp, "TCP", domain)

        traw, cert = send_tcp(target_ip, port, build_tcp, args.timeout, use_tls=False)
        if traw:
            st, hd = parse_response(traw)
            print(f"  [+] TCP OPTIONS -> {st}")
        else:
            print(f"  [-] TCP: {cert}")

        # TLS на явном флаге или на 5061
        if args.tls or port == 5061:
            def build_tls(li, lp, _port=port):
                return build_request("OPTIONS", target_ip, _port, li, lp, "TLS", domain)
            traw, cert = send_tcp(target_ip, port, build_tls, args.timeout, use_tls=True)
            if traw:
                st, hd = parse_response(traw)
                print(f"  [+] TLS OPTIONS -> {st}")
                if isinstance(cert, dict):
                    subj = cert.get("subject")
                    print(f"      cert subject: {subj}")
            else:
                print(f"  [-] TLS: {cert}")
        print()

    print("=== Фингерпринт ===")
    if fingerprint:
        for k, v in fingerprint.items():
            print(f"  {k}: {v}")
    else:
        print("  (баннер не раскрыт — сервер может скрывать Server/User-Agent)")


if __name__ == "__main__":
    main()
