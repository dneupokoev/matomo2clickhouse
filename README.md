# matomo2clickhouse

Replication Matomo from MySQL to ClickHouse (Репликация Matomo: переливка данных из MySQL в ClickHouse)

Сначала настроить, потом вручную запускать проект: ```matomo2clickhouse_start.sh```

Для автоматизации можно настроить через cron выполнение команды:

```pipenv run python3 matomo2clickhouse.py```


### Кратко весь процесс настройки:
- Создать таблицы в ClickHouse (всю структуру таблиц)
- Скопировать все уже существующие данные из MySQL в ClickHouse
- Настроить репликацию из MySQL в ClickHouse 

***ВНИМАНИЕ! Пути до каталогов и файлов везде указывайте свои!***

### MySQL
- Matomo может использовать MySQL/MariaDB/Percona или другие DB семейства MySQL, далее будем это всё называть MySQL
- Для работы python с MySQL скорее всего сначала потребуется установить клиентскую библиотеку для ОС, поэтому пробуем установить:

```sudo apt install libmysqlclient-dev```

- Для работы репликации в MySQL нужно включить binlog. Внимание: необходимо предусмотреть чтобы было достаточно места на диске для бинлога!

```
Редактируем /etc/mysql/mariadb.conf.d/50-server.cnf (файл может быть в другом месте):

[mysqld]:
default-authentication-plugin = mysql_native_password
server_id = 1
log_bin = /var/log/mysql/mysql-bin.log
max_binlog_size = 100M
expire_logs_days = 30
binlog_format = row
binlog_row_image = full
binlog_do_db = название базы, (можно несколько строк для нескольких баз)
```

- После внесенных изменений рестартуем сервис БД (название сервиса может отличаться):

```sudo systemctl restart mariadb.service```

- В базе MySQL завести пользователя и задать ему права:

```GRANT SELECT, PROCESS, SUPER, REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 'user'@'%';```


### ClickHouse
- Для создания структуры выполнить скрипт: script_create_clickhouse_table.sql (ВНИМАНИЕ!!! сначала необходимо изучить скрипт!)
- Если потребуются дополнительные таблицы, то читать описание внутри _settings.py


### Установка matomo2clickhouse (выполняем пошагово)

- Для работы потребуется Linux (тестирование проводилось на ubuntu 22.04.01)
- Устанавливаем питон (тестирование данной инструкции проводилось на 3.10, на остальных версиях работу не гарантирую, но должно работать на версиях 3.9+, если вам потребуется, то без особенного труда сможете переписать даже под 2.7)
- Устанавливаем pip:

```sudo apt install python3-pip```

- Далее устанавливаем pipenv (на linux):

```pip3 install pipenv```

- Создаем нужный каталог в нужном нам месте
- Копируем в этот каталог файлы проекта https://github.com/dneupokoev/matomo2clickhouse
- Заходим в созданный каталог и создаем в нем пустой каталог .venv
- В каталоге проекта выполняем команды (либо иным способом устанавливаем пакеты из requirements.txt):

```pipenv shell```

```pipenv sync```

- Редактируем файл _settings.py (описание все настроек внутри файла!)
- Настраиваем регулярное выполнение (например, через cron) команды:

```pipenv run python3 matomo2clickhouse.py```


### Дополнительно
- Обратите внимание на описание внутри _settings.py - там все настройки
- Если работает экземпляр программы, то второй экземпляр запускаться не будет (отслеживается через создание и проверку наличия файла)  
- Записывается лог ошибок (настраивается в settings, рекомендуется сюда: /var/log/matomo2clickhouse/)
- Если задать нужные настройки в settings, то результат работы будет присылать в телеграм (в личку или указанный канал)
- Можно включить (в settings) вывод информации о дисковом пространстве


### Добавления задания в cron
Смотрим какие задания уже созданы для данного пользователя:

```crontab -l```

Открываем файл для создания задания:

```crontab -e```

Каждая задача формируется следующим образом (для любого значения нужно использовать звездочку "*"):

```минута(0-59) час(0-23) день(1-31) месяц(1-12) день_недели(0-7) /полный/путь/к/команде```

Чтобы matomo2clickhouse запускался каждые 2 часа ровно в 8 минут создаем строку и сохраняем файл:

```8 */2 * * * /opt/dix/matomo2clickhouse/matomo2clickhouse_cron.sh```

ВНИМАНИЕ!!! отредактируйте содержимое файла matomo2clickhouse_cron.sh и сделайте его исполняемым


### Частые проблемы
- Всё установили и запускам, но получаем ошибку ```unknown encoding: utf8mb3```, скорее всего можно починить примерно так:
```
cd /usr/lib/python3.10/encodings
cp utf_8.py utf8mb3.py
```

### ВНИМАНИЕ!
- в переменной ```settings.tables_not_updated``` указаны таблицы, для которых все UPDATE заменены на INSERT, т.е. записи добавляются, а не изменяются. Это необходимо учитывать при селектах! Актуальные записи - те, у которых максимальное значение ```dateid```.
Сделано это для того, чтобы ClickHouse работал корректно (он не заточен на UPDATE - это ОЧЕНЬ медленная операция)

