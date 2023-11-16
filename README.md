# matomo2clickhouse

Replication Matomo from MySQL to ClickHouse (Репликация Matomo: переливка данных из MySQL в ClickHouse)

Для работы потребуется Linux (тестирование проводилось на ubuntu 22.04.01). При необходимости переписать под windows, вероятно, вам не составит большого труда.

Сначала всё настроить, потом вручную запускать проект: ```matomo2clickhouse_start.sh```

Для автоматизации можно настроить (например, через cron) выполнение скрипта ```matomo2clickhouse.py```

### Кратко о том как устроена работа matomo2clickhouse:

- MySQL делает репликацию (пишет binlog со всеми запросами, которые выполняются в базе данных).
- При запуске matomo2clickhouse читает репликацию (настройки и их описания содержатся в ```settings.py```) с момента предыдущей остановки, преобразует sql-запросы
  выбранных таблиц в формат для ClickHouse и выполняет эти запросы в ClickHouse.
- В таблице ```ClickHouse.log_replication``` ведется логирование: какая позиция бинлога успешно записана в ClickHouse (соответственно по записям можно понять что
  загружено и во сколько). Именно этой таблицей пользуется matomo2clickhouse при запуске, чтобы понять с какого места бинлога продолжать переливать данные в
  ClickHouse.

### Кратко весь процесс настройки:

- Создать таблицы в ClickHouse (для создания таблиц выполнить скрипт из проекта с учетом своих настроек)
- Скопировать все уже существующие данные из MySQL в ClickHouse (самостоятельно любым способом)
- Настроить репликацию из MySQL в ClickHouse (настроить как описано в текущей инструкции, но с учётом особенностей вашей системы)

***ВНИМАНИЕ! Пути до каталогов и файлов везде указывайте свои!***

### MySQL

- Matomo может использовать MySQL/MariaDB/Percona или другие DB семейства MySQL, далее будем это всё называть MySQL
- Для работы python с MySQL скорее всего сначала потребуется установить клиентскую библиотеку для ОС, поэтому пробуем установить:
```
sudo apt install libmysqlclient-dev
```

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
```
sudo systemctl restart mariadb.service
```

- В базе MySQL завести пользователя и задать ему права:
```
GRANT SELECT, PROCESS, SUPER, REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 'user'@'%';
```

### ClickHouse

- Для создания структуры выполнить скрипт: ```script_create_clickhouse_table.sql``` (ВНИМАНИЕ!!! сначала необходимо изучить скрипт!)
- Если потребуются дополнительные таблицы, то читать описание внутри ```settings.py```

### Установка matomo2clickhouse (выполняем пошагово)

- Устанавливаем python (тестирование данной инструкции проводилось на 3.10, на остальных версиях работу не гарантирую, но должно работать на версиях 3.9+, если
  вам потребуется, то без особенного труда сможете переписать даже под 2.7)
- Устанавливаем pip:
```
sudo apt install python3-pip
```

- Далее устанавливаем pipenv (на linux):
```
pip3 install pipenv
```

- Создаем нужный каталог в нужном нам месте
- Копируем в этот каталог файлы проекта https://github.com/dneupokoev/matomo2clickhouse
- Заходим в созданный каталог и создаем в нем пустой каталог .venv
- В каталоге проекта выполняем команды (либо иным способом устанавливаем пакеты из requirements.txt):
```
pipenv shell
```
```
pipenv sync
```

- Редактируем и переименовываем файл ```_settings.py``` в ```settings.py``` (описание внутри файла)
- Настраиваем регулярное выполнение (например, через cron) скрипта:
```
matomo2clickhouse.py
```




### Дополнительно

- Обратите внимание на описание внутри ```settings.py``` - там все настройки
- Если работает экземпляр программы, то второй экземпляр запускаться не будет (отслеживается через создание и проверку наличия файла)
- Записывается лог ошибок (настраивается в settings, рекомендуется сюда: /var/log/matomo2clickhouse/)
- Если задать нужные настройки в ```settings.py```, то результат работы будет присылать в телеграм (в личку или указанный канал)
- Можно включить (в ```settings.py```) вывод информации о дисковом пространстве
- Иногда имеет смысл почистить таблицу в ClickHouse с логированием переливки от старых данных (обычно старые логи не нужны, а место занимают). Примерно так: 
```
ALTER TABLE matomo.log_replication DELETE WHERE created_at < '2023-01-01 00:00:00'
```




### Добавление задания в cron

Смотрим какие задания уже созданы для данного пользователя:
```
crontab -l
```

Открываем файл для создания задания:
```
crontab -e
```

Каждая задача формируется следующим образом (для любого значения нужно использовать звездочку "*"):
```
минута(0-59) час(0-23) день(1-31) месяц(1-12) день_недели(0-7) /полный/путь/к/команде
```

Чтобы matomo2clickhouse запускался каждый час ровно в 7 минут, создаем строку и сохраняем файл:
```
7 */1 * * * /opt/dix/matomo2clickhouse/matomo2clickhouse_cron.sh
```

ВНИМАНИЕ!!! отредактируйте содержимое файла ```matomo2clickhouse_cron.sh``` и сделайте его исполняемым




### Возможные проблемы и их решение

- При выполнении скрипта появилась ошибка, что ClickHouse не может загрузить данные.
Нужно в файле ```settings.py``` заменить (запомните как настроено, когда почините, нужно будет вернуть) значения параметров так:
  ```
  DEBUG = True
  replication_batch_sql = 0
  ```
  Далее запустить скрипт вручную. В самой последней строке, содержащей переменную ```dv_sql_for_execute_last``` будет тело "проблемного" запроса. Необходимо разобраться что с ним не так и принять меры. Обязательно изучите все комментарии в ```settings.py``` 

- Всё установили и запускам, но получаем ошибку ```unknown encoding: utf8mb3```, скорее всего можно починить примерно так:
  ```
  cd /usr/lib/python3.10/encodings
  cp utf_8.py utf8mb3.py
  ```


- При ошибке ```'utf-8' codec can't decode bytes in position 790-791: unexpected end of data```
  помогло добавление параметра ```errors="ignore"```
  в ```.venv/lib/python3.10/site-packages/pymysqlreplication/events.py```
  строка 203 в параметр
  ```
  .decode("utf-8", errors="ignore"): self.query = self.packet.read(event_size - 13 - self.status_vars_length - self.schema_length - 1).decode("utf-8", errors="ignore")
  ```


- Ошибка "DB::Exception: Too many parts (600). Merges are processing significantly slower than inserts".

  Описание как бороться здесь: [clickhouse.com/docs/knowledgebase/exception-too-many-parts](https://clickhouse.com/docs/knowledgebase/exception-too-many-parts)
  Если кратко, то: главное требование при вставке в ClickHouse: никогда не отправлять слишком много запросов в секунду.
  В идеале - одна вставка в секунду/в несколько секунд, с UPDATE и DELETE нужно быть еще аккуратнее, а в идеале вообще избегать их.
  Один из вариантов, как избежать UPDATE описан в [settings.tables_not_updated](#tables_not_updated)

- Ошибка, что **не хватает в талице столбца**, выглядит примерно так: ```ERROR = ServerException('DB::Exception: No such column custom_dimension_6 in table matomo.matomo_log_visit ...```

  Необходимо разобраться почему столбца не хватает. Например, могли обновить matomo или добавить кастомное поле. 
  Как добавлять столбцы описано [в инструкции ClickHouse: ADD COLUMN](https://clickhouse.com/docs/ru/sql-reference/statements/alter/column#alter_add-column)

- Ошибка "DB::Exception: There is no supertype for types String, Float64 because some of them are String/FixedString and some of them are not."

  Означает, что в поле String пытаемся записать Float64. Скорее всего изначально тип поля выбрали неправильно. Нужно найти это поле и таблицу, править (изменить тип поля) примерно так:
  ```
  ALTER TABLE `matomo`.`matomo_goal` MODIFY COLUMN `revenue` Float64
  ```




### Полключаем базу из MySQL в ClickHouse для обмена данными между ClickHouse и MySQL

Официальная инструкция от ClickHouse: https://clickhouse.com/docs/ru/engines/database-engines/mysql

Данное действие может понадобиться, например, для переливки данных из MySQL в ClickHouse, для проверки целостности данных и т.д.

- Полключаем базу из MySQL в ClickHouse:
```
CREATE DATABASE mysql_matomo ENGINE = MySQL('localhost:3306', 'dbname', 'my_user', 'user_password')
```
- Проверяем, что база данных mysql_matomo появилась в ClickHouse:
```
SHOW DATABASES
SHOW TABLES FROM mysql_matomo
```
- Делаем запрос к таблице из базы MySQL:
```
SELECT * FROM mysql_matomo.matomo_site_url
```
- Далее между ClickHouse и MySQL можно данные джойнить, делать инсерты и прочее...




### Принудительная отправка строки таблицы в репликацию

***ВНИМАНИЕ!!! Всё на свой страх и риск! Очень легко БЕЗВОЗВРАТНО убить данные!!!***

В этом примере отправка строки происходит через удаление и добавление, поэтому возможны неприятные сюрпризы и вы должны четко понимать что делаете.

- Для примера будем переносить данные из таблицы matomo_site_url
```
SELECT * FROM matomo.matomo_site_url;
```
- Чтобы принудительно отправить строку в репликацию выполнить последовательно запросы. Для небольших таблиц можно выполнять без WHERE - можно переносить сразу полностью таблицу
```
-- сначала создаем временную таблицу с нужной строкой
CREATE TEMPORARY TABLE matomo.tmp_tbl SELECT * FROM matomo.matomo_site_url WHERE `idsite` = '20';
```
```
-- проверим, что всё создалось
-- SELECT * FROM matomo.tmp_tbl;
```
```
-- удалим строку в ИТОГОВОЙ таблице (в clickhouse)
DELETE FROM matomo.matomo_site_url WHERE `idsite` = '20';
```
***ВНИМАНИЕ!!! Если в mysql долго данных не будет, то ОБЯЗАТЕЛЬНО возникнут проблемы в работе matomo! Между DELETE и INSERT должно быть МИНИМУМ времени!!!***
```
-- удалим строку в ИСХОДНОЙ таблице (в mysql)
DELETE FROM matomo.matomo_site_url WHERE `idsite` = '20';
-- вставим строку из временной таблицы в ИСХОДНУЮ (в mysql)
INSERT INTO matomo.matomo_site_url SELECT * FROM matomo.tmp_tbl WHERE `idsite` = '20';
```
- Удалим временную таблицу:
```
DROP TEMPORARY TABLE IF EXISTS matomo.tmp_tbl;
```




### ВНИМАНИЕ!

- Поробности о работе с дублями строк в [doc_old_duplicates.md](./doc_old_duplicates.md)
- В ```settings.sql_execute_at_end_matomo2clickhouse``` находятся скрипты, которые выполнятся после переливки бинлогов. Необходимо использовать для удаления старых дубликатов.
  Подробности в ```settings.py```, переменная ```sql_execute_at_end_matomo2clickhouse```. Изучите скрипты, там можно настроить глубину удаления.
  ВНИМАНИЕ! если настроить слишком большую глубину, то возможна ошибка из-за превышения допустимого объема памяти (скрипт выполняется в оперативной памяти).
  Обратите внимание, что данные запросы будут выполняться только если ```settings.replication_max_minutes > 10```.
- В переменной <span id="tables_not_updated">```settings.tables_not_updated```<span> указаны таблицы, для которых все UPDATE заменены на INSERT, т.е. записи добавляются, а не изменяются.
  Это необходимо учитывать при селектах! Актуальные записи - те, у которых максимальное значение ```dateid```.
  Сделано это для того, чтобы ClickHouse работал корректно (он не заточен на UPDATE - это ОЧЕНЬ медленная операция). Для примера (как получать актуальные
  данные. ВНИМАНИЕ! Это только пример для понимания! На большом количестве данных работать будет очень медленно) созданы 2 представления: ```view_matomo_log_visit``` и```view_matomo_log_link_visit_action```.
  Для реальной работы вы должны сами решить как обрабатывать дубли.
```
-- Узнать количество старых дублей за период можно примерно так (обратите внимание как указывается период):
SELECT count(*)
FROM (
	SELECT idlink_va, dateid AS dateid_for_del
	FROM matomo.matomo_log_link_visit_action
	WHERE 1=1
	AND server_time >= (DATE_sub(NOW(), INTERVAL 14 DAY))
	AND server_time <= (DATE_sub(NOW(), INTERVAL 0 DAY))
) t2
RIGHT JOIN (
	SELECT idlink_va, max(dateid) AS dateid_max, count(*) AS id_count
	FROM matomo.matomo_log_link_visit_action
	WHERE 1=1
	AND server_time >= (DATE_sub(NOW(), INTERVAL 14 DAY))
	AND server_time <= (DATE_sub(NOW(), INTERVAL 0 DAY))
	GROUP BY idlink_va
	HAVING id_count > 1
) t1 ON t2.idlink_va = t1.idlink_va
```
- Перед обновлением matomo НЕОБХОДИМО (!!!) изучить что меняется. В случае, если меняется структура базы данных, то нужно проработать план обновления (перед
  обновой сначала провести полный обмен с остановкой базы данных matomo, после этого привести структуру(метаданные) баз данных в соответствите и т.д.)
- За один запуск matomo2clickhouse переливает не все бинлоги, а только то, что вы настроите в ```settings.py``` (например, можно настроить время работы и/или
  количество строк). Не рекомендуется слишком долгое выполнение и слишком много строк. Например, для тестирования достаточно 5-10 минут. В прод: запускать раз в
  час на 50 минут.
- matomo2clickhouse не переливает все таблицы и всё их содержимое, а читает настройки в settings.py, ищет последнюю позицию в
  ```ClickHouse.log_replication.log_time``` и пишет только то, что появилось новое в бинлогах с момента прошлой остановки matomo2clickhouse. То есть если вы
  сегодня включили репликацию, то данные будут переливаться только с этого момента. Если в какой-то момент вы удалите файл репликации, а он нужен
  matomo2clickhouse, то переливка остановится с ошибкой. Если вы полностью очистите таблицу ```ClickHouse.log_replication```, то будут переливаться все
  имеющиеся бинлоги, не зависимо от того переливались ли они ранее.




### Версии

231116.01
+ добавил параметр settings.CONST_TBL_NOT_DELETE_OLD - словарь с таблицами, для которых не надо удалять старые данные, если они удалены в самом matomo.
+ добавил проверку даты для строк delete (если дата старая, то игнорируем эту строку и выполнять на итоговой БД не будем: обработчик для settings.CONST_TBL_NOT_DELETE_OLD)
+ считаю количество отклоненных удалений и вывожу в лог
+ немного почистил код от рудиментов

230727.01
+ добавил settings.sql_execute_at_end_matomo2clickhouse: скрипты, которые выполнятся в конце работы matomo2clickhouse (можно использовать для удаления дублей или для других задач)

230719.01:
+ отключил асинхронность мутаций (update и delete теперь будут ждать завершения мутаций на данном сервере), чтобы не отваливалось из-за большого числа delete  
+ исправил глюк с инсертом и апдейтом одной записи, когда они идут подряд (с очень маленьким интервалом) и пишутся в таблицы из settings.tables_not_updated

230505.02:
+ исправил ошибку обработки одинарной кавычки в запросе: добавил перед кавычкой экранирование, чтобы sql-запрос отрабатывал корректно
+ добавил автоматическое изменение на построчное выполнение запросов (при следующем запуске) после ошибки выполнения запроса - необходимо для определения проблемного запроса без изменения параметров: запрос будет в логе в строке с dv_sql_for_execute_last в результате повторного запуска после появления ошибки
+ добавил больше логирования

230406.01:
+ для ускорения изменил алгоритм: теперь запросы группируются, собираются в батчи и выполняются сразу партиями (обработка ускорилась примерно в 12 раз). Для тонкой настройки можно "поиграть" параметром settings.replication_batch_sql

230403.01:
+ добавил параметр settings.EXECUTE_CLICKHOUSE (нужен для тестирования) - True: выполнять insert в ClickHouse (боевой режим); False: не выполнять insert (для тестирования и отладки)
+ изменил параметр settings.CH_matomo_dbname - теперь базы в MySQL и ClickHouse могут иметь разные названия
+ изменил проверку исключения для построчного выполнения (dv_find_text)

221206.03:
+ базовая стабильная версия (полностью протестированная и отлаженная)
