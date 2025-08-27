import csv

# Пример данных пользователей
users = [
    {"Username": "alice", "Password": "Alice1234", "Role": "admin"},
    {"Username": "bob", "Password": "Bob12345", "Role": "guest"},
    {"Username": "carol", "Password": "Carol123", "Role": "maintainer"},
    {"Username": "dave", "Password": "Dave1234", "Role": "developer"},
]

# Имя CSV файла
csv_file = "harbor_users.csv"

# Создание CSV
with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=["Username", "Password", "Role"])
    writer.writeheader()
    for user in users:
        writer.writerow(user)

print(f"CSV файл '{csv_file}' успешно создан с {len(users)} пользователями.")
