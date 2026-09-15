import itertools

# Создаем список всех маленьких английских букв
letters = 'abcdefghijklmnopqrstuvwxyz'

# Генерируем все возможные комбинации из 3 букв (с повторениями)
combinations = itertools.product(letters, repeat=3)

# Преобразуем кортежи в строки и собираем в список
result = [''.join(combo) for combo in combinations]

# Выводим результат
print(f"Количество комбинаций: {len(result)}")
print("\nПервые 20 комбинаций:")
for i, combo in enumerate(result[:20]):
    print(f"{i+1}: {combo}")

# Если нужно сохранить в файл
with open('combinations.txt', 'w') as f:
    for combo in result:
        f.write(combo + '\n')

print("\nВсе комбинации сохранены в файл 'combinations.txt'")
