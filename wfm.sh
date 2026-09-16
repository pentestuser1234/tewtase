#!/bin/bash

# Скрипт установки WFM UI Launcher на Kali Linux
# Запускать с правами root или через sudo

set -e  # Остановка при ошибке

echo "=========================================="
echo "Установка WFM UI Launcher на Kali Linux"
echo "=========================================="
echo ""

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка прав root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Ошибка: Запустите скрипт с правами root (sudo)${NC}"
    exit 1
fi

# Шаг 1: Установка Java
echo -e "${YELLOW}[1/7] Установка Java...${NC}"
apt update -qq
apt install -y default-jdk default-jre unzip xdg-utils

# Проверка установки Java
if ! command -v java &> /dev/null; then
    echo -e "${RED}Ошибка: Java не установлена${NC}"
    exit 1
fi

JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2)
echo -e "${GREEN}✓ Java установлена: $JAVA_VERSION${NC}"
echo ""

# Шаг 2: Настройка переменных среды
echo -e "${YELLOW}[2/7] Настройка переменных среды Java...${NC}"

JAVA_HOME_PATH="/usr/lib/jvm/default-java"

# Добавление в /etc/environment для системных настроек
if ! grep -q "JAVA_HOME" /etc/environment; then
    echo "JAVA_HOME=$JAVA_HOME_PATH" >> /etc/environment
    echo "PATH=\$PATH:\$JAVA_HOME/bin" >> /etc/environment
fi

# Добавление в профиль пользователя текущего пользователя
CURRENT_USER=$(logname 2>/dev/null || echo $SUDO_USER)
USER_HOME="/home/$CURRENT_USER"

if [ -f "$USER_HOME/.bashrc" ]; then
    if ! grep -q "JAVA_HOME" "$USER_HOME/.bashrc"; then
        echo "" >> "$USER_HOME/.bashrc"
        echo "# WFM UI Launcher - Java settings" >> "$USER_HOME/.bashrc"
        echo "export JAVA_HOME=$JAVA_HOME_PATH" >> "$USER_HOME/.bashrc"
        echo "export PATH=\$PATH:\$JAVA_HOME/bin" >> "$USER_HOME/.bashrc"
    fi
fi

# Экспорт для текущей сессии
export JAVA_HOME=$JAVA_HOME_PATH
export PATH=$PATH:$JAVA_HOME/bin

echo -e "${GREEN}✓ Переменные среды настроены${NC}"
echo ""

# Шаг 3: Создание директории для лаунчера
echo -e "${YELLOW}[3/7] Создание директории для WFM UI Launcher...${NC}"

LAUNCHER_DIR="$USER_HOME/wfm-ui-launcher"
mkdir -p "$LAUNCHER_DIR"

echo -e "${GREEN}✓ Директория создана: $LAUNCHER_DIR${NC}"
echo ""

# Шаг 4: Создание скрипта запуска
echo -e "${YELLOW}[4/7] Создание скрипта запуска...${NC}"

cat > "$LAUNCHER_DIR/run-wfm.sh" << 'EOF'
#!/bin/bash

# Скрипт запуска WFM UI Launcher

LAUNCHER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JAVA_PATH=$(which java)

# Поиск JAR файла лаунчера
LAUNCHER_JAR=$(find "$LAUNCHER_DIR" -name "*.jar" -type f 2>/dev/null | head -n 1)

if [ -z "$LAUNCHER_JAR" ]; then
    echo "Ошибка: JAR файл лаунчера не найден!"
    echo "Убедитесь, что вы распаковали архив UI Launcher в директорию: $LAUNCHER_DIR"
    exit 1
fi

# Проверка аргументов
if [ -z "$1" ]; then
    echo "Использование: $0 <file.wfm>"
    echo "Пример: $0 start.wfm"
    exit 1
fi

WFM_FILE="$1"

if [ ! -f "$WFM_FILE" ]; then
    echo "Ошибка: Файл $WFM_FILE не найден!"
    exit 1
fi

echo "Запуск WFM UI Launcher..."
echo "JAR: $LAUNCHER_JAR"
echo "Файл: $WFM_FILE"
echo ""

# Запуск лаунчера
$JAVA_PATH -jar "$LAUNCHER_JAR" "$WFM_FILE"
EOF

chmod +x "$LAUNCHER_DIR/run-wfm.sh"

echo -e "${GREEN}✓ Скрипт запуска создан${NC}"
echo ""

# Шаг 5: Создание Desktop Entry
echo -e "${YELLOW}[5/7] Создание Desktop Entry...${NC}"

mkdir -p "$USER_HOME/.local/share/applications"

cat > "$USER_HOME/.local/share/applications/wfm-launcher.desktop" << EOF
[Desktop Entry]
Type=Application
Name=WFM UI Launcher
Comment=Genesys Workforce Management UI Launcher
Exec=$LAUNCHER_DIR/run-wfm.sh %f
Icon=application-x-executable
MimeType=application/x-wfm;
Terminal=false
Categories=Utility;
NoDisplay=false
EOF

# Установка прав
chown -R $CURRENT_USER:$CURRENT_USER "$USER_HOME/.local/share/applications/wfm-launcher.desktop"

echo -e "${GREEN}✓ Desktop Entry создан${NC}"
echo ""

# Шаг 6: Настройка MIME типа
echo -e "${YELLOW}[6/7] Настройка ассоциации файлов .wfm...${NC}"

# Создание MIME типа
mkdir -p "$USER_HOME/.local/share/mime/packages"

cat > "$USER_HOME/.local/share/mime/packages/application-x-wfm.xml" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
  <mime-type type="application/x-wfm">
    <comment>WFM UI Launcher File</comment>
    <glob pattern="*.wfm"/>
  </mime-type>
</mime-info>
EOF

chown -R $CURRENT_USER:$CURRENT_USER "$USER_HOME/.local/share/mime"

# Обновление базы MIME
su - $CURRENT_USER -c "update-mime-database ~/.local/share/mime" 2>/dev/null || true
su - $CURRENT_USER -c "xdg-mime default wfm-launcher.desktop application/x-wfm" 2>/dev/null || true

echo -e "${GREEN}✓ Ассоциация файлов настроена${NC}"
echo ""

# Шаг 7: Создание инструкции
echo -e "${YELLOW}[7/7] Создание инструкции по использованию...${NC}"

cat > "$LAUNCHER_DIR/README.txt" << EOF
========================================
WFM UI Launcher - Инструкция
========================================

1. СКАЧИВАНИЕ LAUNCHER:
   - Войдите в WFM Web for Supervisors
   - Нажмите About (в правом верхнем углу)
   - Нажмите "Download UI Launcher"
   - Сохраните ZIP архив

2. РАСПАКОВКА:
   cd $LAUNCHER_DIR
   unzip /путь/к/скачанному/архиву.zip
   
3. НАСТРОЙКА В WFM WEB:
   - В браузере перейдите в About > Settings
   - Найдите настройку RUN_JAVA_STANDALONE
   - Установите значение "UI Launcher"
   - Сохраните изменения

4. ИСПОЛЬЗОВАНИЕ:
   
   Способ 1 - Через скрипт:
   $LAUNCHER_DIR/run-wfm.sh start.wfm
   
   Способ 2 - Двойной клик:
   После скачивания файла start.wfm из WFM Web,
   просто откройте его двойным кликом
   
   Способ 3 - Через терминал:
   cd ~/Downloads
   $LAUNCHER_DIR/run-wfm.sh start.wfm

5. ВАЖНО:
   - Браузер с активной сессией WFM должен быть открыт
   - Не выходите из системы в браузере
   - Файл start.wfm работает только с активной сессией

6. УСТРАНЕНИЕ НЕПОЛАДОК:
   
   Проверка Java:
   java -version
   
   Проверка переменных:
   echo \$JAVA_HOME
   echo \$PATH
   
   Запуск с отладкой:
   java -jar $LAUNCHER_DIR/*.jar start.wfm

========================================
EOF

chown $CURRENT_USER:$CURRENT_USER "$LAUNCHER_DIR/README.txt"

echo -e "${GREEN}✓ Инструкция создана${NC}"
echo ""

# Финальные настройки прав
chown -R $CURRENT_USER:$CURRENT_USER "$LAUNCHER_DIR"

echo "=========================================="
echo -e "${GREEN}✓ Установка завершена успешно!${NC}"
echo "=========================================="
echo ""
echo "Директория лаунчера: $LAUNCHER_DIR"
echo ""
echo "Следующие шаги:"
echo "1. Перезагрузите систему или выполните: source ~/.bashrc"
echo "2. Скачайте UI Launcher из WFM Web (About > Download UI Launcher)"
echo "3. Распакуйте архив в: $LAUNCHER_DIR"
echo "4. Настройте RUN_JAVA_STANDALONE = UI Launcher в WFM Web"
echo "5. Используйте: $LAUNCHER_DIR/run-wfm.sh <file.wfm>"
echo ""
echo "Подробная инструкция: $LAUNCHER_DIR/README.txt"
echo ""
