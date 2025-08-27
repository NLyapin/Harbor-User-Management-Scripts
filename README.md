# Harbor User Management Scripts

Этот набор скриптов помогает автоматизировать управление пользователями в Harbor: массовое создание пользователей из CSV и смену пароля (для себя или админом).

---

## Prerequisites

Перед запуском скриптов необходимо установить зависимости Python.
Они перечислены в файле `requirements.txt`.

**Установка:**

```bash
pip install -r requirements.txt
```

**Пример содержимого `requirements.txt`:**

```text
git+https://github.com/container-registry/harbor-api-client.git
```

---

## 1. `create_users_from_csv.py`

**Назначение:**
Создает пользователей в Harbor из CSV-файла и (опционально) добавляет их в проекты с указанными ролями.

**CSV формат:**

* Обязательные колонки: `Username`, `Password`, `Role`

* Необязательная колонка: `Project`

* В колонке `Project` можно указывать несколько проектов через пробел или запятую, например: `project1 project2`.

**Пример CSV:**

```csv
Username,Password,Role,Project
alice,Secret123!,admin,project1 project2 project3
bob,Secret123!,developer,
```

**Запуск:**

```bash
python3 create_users_from_csv.py \
  --host https://example.com \
  --admin-user admin \
  --admin-pass 'SECRET' \
  --csv test_users.csv \
  --project project1,project2,project3 \
  --create-project-if-missing
```

**Флаги:**

* `--host` — адрес Harbor.

* `--admin-user` — пользователь с правами администратора.

* `--admin-pass` — пароль администратора.

* `--csv` — путь к CSV-файлу.

* `--project` — дефолтный проект для всех пользователей (можно указать несколько через запятую).

* `--create-project-if-missing` — если проекта не существует, создаёт его.

**Особенности:**

* Поддержка нескольких проектов как через CSV, так и через флаг `--project`.

* Роли из CSV (admin, developer, guest, maintainer и др.) сопоставляются с ID Harbor.

* Если проект не найден и `--create-project-if-missing` не указан, выводится предупреждение.

* Пользователи не создаются повторно, если уже существуют.

* Пользователь добавляется только в проекты, где его ещё нет.

**Пример локального запуска через HTTP:**

```bash
python3 create_users_from_csv.py \
  --host http://localhost \
  --admin-user admin \
  --admin-pass Harbor12345 \
  --csv test_users.csv
```

**Результат:**

```
(1, 'alice', 'SKIP', 'user "alice" already exists')
(1, 'alice', 'SKIP', 'user "alice" already in project project1')
(1, 'alice', 'SKIP', 'user "alice" already in project project2')
(1, 'alice', 'WARN', 'project "project3" not found - skipping project membership')
(2, 'bob', 'SKIP', 'user "bob" already exists')
```

Если включить создание проектов, которых нет:

```bash
python3 create_users_from_csv.py \
  --host http://localhost \
  --admin-user admin \
  --admin-pass Harbor12345 \
  --csv test_users.csv \
  --create-project-if-missing
```

**Результат:**

```
(1, 'alice', 'SKIP', 'user "alice" already exists')
(1, 'alice', 'SKIP', 'user "alice" already in project project1')
(1, 'alice', 'SKIP', 'user "alice" already in project project2')
(1, 'alice', 'OK', 'user_id=17 added to project project3 role=1')
(2, 'bob', 'SKIP', 'user "bob" already exists')
```

---

## 2. `change_password.py`

**Назначение:**
Интерактивная смена пароля в Harbor.

* Пользователь может сменить свой пароль.

* Админ может сменить пароль другого пользователя.

**Пример: смена собственного пароля**

```bash
python3 change_password.py --host http://localhost --user alice --pass secret
```

**Пример: админ меняет пароль другого пользователя**

```bash
python3 change_password.py \
  --host http://localhost \
  --user admin \
  --prompt-pass \
  --target bob
```

**Особенности:**

* Скрипт аккуратно обрабатывает ошибки: неправильный пароль, несоответствие требованиям к сложности, пользователь не найден и др.

* Поддерживает Harbor API v2.0.

---

## 3. Скрипт установки Harbor локально (`install_harbor.sh`)

**Назначение:**
Автоматически скачивает и разворачивает Harbor на локальной машине через HTTP (`localhost`).
Полезен для локального тестирования скриптов управления пользователями.

**Запуск:**

```bash
chmod +x install_harbor.sh
./install_harbor.sh
```

**Что делает скрипт:**

1. Проверяет наличие зависимостей: `curl`, `tar`, `docker`, `docker-compose`.
2. Скачивает Harbor версии 2.11.0, если его ещё нет.
3. Создаёт конфигурационный файл `harbor.yml` с `hostname: localhost` и отключённым HTTPS.
4. Устанавливает Harbor и запускает контейнеры.
5. После установки выводит статус контейнеров через `docker-compose ps`.

**Использование:**
Позволяет подготовить локальный Harbor для тестирования скриптов `create_users_from_csv.py` и `change_password.py` без внешнего сервера.
