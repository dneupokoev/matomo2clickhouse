# Дубликаты строк matomo2clickhouse в ClickHouse

**ВНИМАНИЕ!!!** Перед любыми манипуляциями с дубликатами необходимо **ДОЖДАТЬСЯ ЗАВЕРШЕНИЯ** текущей работы matomo2clickhouse и **ОТКЛЮЧИТЬ** запуск matomo2clickhouse!!!
Не лишним будет сделать бэкап! После завершения манипуляций не забыть включить штатную работу.

При работе matomo2clickhouse возможно **образование дубликатов строк** в таблицах ClickHouse.

**Как образуются дубликаты:** в переменной ```settings.tables_not_updated``` указаны таблицы, для которых все UPDATE заменены на INSERT, т.е. записи добавляются, а не изменяются. Это и приводит к дубликатам.

***Чтобы в отчетах данные были корректные нужно учитывать возможность наличия дубликатов!***

Считаем, что у вас в ```settings.py``` значения параметров заполнены так (дальше все примеры будут ИМЕНЕНО для таких данных):
```
CH_matomo_dbname = 'matomo'

replication_max_minutes = 50

tables_not_updated = [
    'matomo_log_visit',
    'matomo_log_link_visit_action',
]

и в кроне настроен запуск matomo2clickhouse каждый час
```



## Удаление дубликатов вручную

### Сначала считаем количество дубликатов в таблицах:
```
-- matomo.matomo_log_link_visit_action:
SELECT count(*)
FROM (
	SELECT idlink_va, dateid AS dateid_for_del
	FROM matomo.matomo_log_link_visit_action
	WHERE 1=1
	AND server_time >= (DATE_sub(NOW(), INTERVAL 365 DAY))
	AND server_time <= (DATE_sub(NOW(), INTERVAL 0 DAY))
) t2
RIGHT JOIN (
	SELECT idlink_va, max(dateid) AS dateid_max, count(*) AS id_count
	FROM matomo.matomo_log_link_visit_action
	WHERE 1=1
	AND server_time >= (DATE_sub(NOW(), INTERVAL 365 DAY))
	AND server_time <= (DATE_sub(NOW(), INTERVAL 0 DAY))
	GROUP BY idlink_va
	HAVING id_count > 1
) t1 ON t2.idlink_va = t1.idlink_va
```
```
-- matomo.matomo_log_visit:
SELECT count(*)
FROM (
    SELECT idvisit, dateid AS dateid_for_del
    FROM matomo.matomo_log_visit
    WHERE 1=1
    AND visit_first_action_time >= (DATE_sub(NOW(), INTERVAL 365 DAY))
    AND visit_first_action_time <= (DATE_sub(NOW(), INTERVAL 0 DAY))
) t2
RIGHT JOIN (
    SELECT idvisit, max(dateid) AS dateid_max, count(*) AS id_count
    FROM matomo.matomo_log_visit
    WHERE 1=1
    AND visit_first_action_time >= (DATE_sub(NOW(), INTERVAL 365 DAY))
    AND visit_first_action_time <= (DATE_sub(NOW(), INTERVAL 0 DAY))
    GROUP BY idvisit
    HAVING id_count > 1
) t1 ON t2.idvisit = t1.idvisit
WHERE t2.dateid_for_del <> t1.dateid_max
```
Обратите внимание как настраивается глубина: ```(DATE_sub(NOW(), INTERVAL 365 DAY))``` и ```(DATE_sub(NOW(), INTERVAL 0 DAY))```


### Перед тем, как перейти к удалению, изучите описание:

Если строк для удаления слишком много (больше десятка тысяч), то удалять нужно частями. Вообще нужно тестировать и понять сколько записей(какой период) за раз обрабатывается без ошибок.
Сломать данные запуском большого периода не получится, поэтому опасаться этого не стоит, НО нужно учитывать, что после ошибки некоторое время (ориентировочно до 30 минут) любой запрос на удаление будет завершаться ошибкой.

Ошибка примерно такая:
```
SQL Error [341] [07000]: Code: 341. DB::Exception: Exception happened during execution of mutation 'mutation_40528485.txt'
with part '202212_21545511_21719093_479_40528484' reason: 'Code: 241. DB::Exception: Memory limit (total) exceeded:
would use 17.63 GiB (attempt to allocate chunk of 0 bytes), maximum: 17.56 GiB: While executing AggregatingTransform.
(MEMORY_LIMIT_EXCEEDED) (version 22.2.2.1)'. This error maybe retryable or not.
In case of unretryable error, mutation can be killed with KILL MUTATION query. (UNFINISHED)
```

Проверить какие мутации еще не завершены можно так:
```
SELECT * FROM system.mutations WHERE is_done = 0
```
Убивать мутации нет необходимости - они сами исчезнут со временем.
Но если очень хочется пощекотать нервы, то убить мутацию можно примерно так (**ВНИМАНИЕ! ОПАСНО!** изучите инcтрукцию к ClickHouse + убивается не мгновенно, некоторое время еще будет висеть):
```
KILL MUTATION WHERE database = 'matomo' AND table = 'matomo_log_link_visit_action' AND mutation_id = 'mutation_48523052.txt'
```


### Рекомендации по периодам при ручном удалении:

Периоды должны перекрываться.
Для начала можно попробовать большие периоды, которые перекрывать 10 дней.
После этого проверить сколько осталось дублей и сместить периоды.

Например, сначала чистим период 100-50 дней, далее 60-10, далее 20-0. Далее проверяем есть ли еще дубли на всей глубине 100-0. Если дубли есть, то 100-40, 60-0. И опять проверяем наличие дублей.


### Приступаем к удалению:

Ручной запуск удаления дубликатов из таблица (***ВНИМАНИЕ! внимательно настройте глубину удаления!!!***): 
```
-- matomo.matomo_log_link_visit_action:
-- делает выборку dateid, которые нужно удалить, отправляет на удаление и ждет окончания мутации
ALTER TABLE matomo.matomo_log_link_visit_action DELETE
WHERE 1=1
AND server_time >= (DATE_sub(NOW(), INTERVAL 30 DAY))
AND server_time <= (DATE_sub(NOW(), INTERVAL 15 DAY))
AND dateid in (
	SELECT t2.dateid_for_del
	FROM (
		SELECT idlink_va, dateid AS dateid_for_del
		FROM matomo.matomo_log_link_visit_action
		WHERE 1=1
		AND server_time >= (DATE_sub(NOW(), INTERVAL 30 DAY))
		AND server_time <= (DATE_sub(NOW(), INTERVAL 15 DAY))
	) t2
	RIGHT JOIN (
		SELECT idlink_va, max(dateid) AS dateid_max, count(*) AS id_count
		FROM matomo.matomo_log_link_visit_action
		WHERE 1=1
		AND server_time >= (DATE_sub(NOW(), INTERVAL 30 DAY))
		AND server_time <= (DATE_sub(NOW(), INTERVAL 15 DAY))
		GROUP BY idlink_va
		HAVING id_count > 1
	) t1 ON t2.idlink_va = t1.idlink_va
	WHERE t2.dateid_for_del <> t1.dateid_max
)
SETTINGS mutations_sync = 1;
```
```
-- matomo.matomo_log_visit:
-- делает выборку dateid, которые нужно удалить, отправляет на удаление и ждет окончания мутации
ALTER TABLE matomo.matomo_log_visit DELETE
WHERE 1=1
AND visit_first_action_time >= (DATE_sub(NOW(), INTERVAL 30 DAY))
AND visit_first_action_time <= (DATE_sub(NOW(), INTERVAL 15 DAY))
AND dateid in (
	SELECT t2.dateid_for_del
	FROM (
		SELECT idvisit, dateid AS dateid_for_del
		FROM matomo.matomo_log_visit
		WHERE 1=1
		AND visit_first_action_time >= (DATE_sub(NOW(), INTERVAL 30 DAY))
		AND visit_first_action_time <= (DATE_sub(NOW(), INTERVAL 15 DAY))
	) t2
	RIGHT JOIN (
		SELECT idvisit, max(dateid) AS dateid_max, count(*) AS id_count
		FROM matomo.matomo_log_visit
		WHERE 1=1
		AND visit_first_action_time >= (DATE_sub(NOW(), INTERVAL 30 DAY))
		AND visit_first_action_time <= (DATE_sub(NOW(), INTERVAL 15 DAY))
		GROUP BY idvisit
		HAVING id_count > 1
	) t1 ON t2.idvisit = t1.idvisit
	WHERE t2.dateid_for_del <> t1.dateid_max
)
SETTINGS mutations_sync = 1;
```


## Автоматическое удаление дубликатов

Для автоматического удаления в файле ```settings.py``` есть переменная ```sql_execute_at_end_matomo2clickhouse```, в ней заполняются sql-запросы,
которые выполнятся в конце работы matomo2clickhouse. В этих запросах и есть удаление старых дубликатов.

Принцип работы такой: сначала выполняется переливка данных в ClickHouse, затем поочередно запускаются sql-запросы и удаляют дубликаты за указанный в них период.

**ВНИМАНИЕ!!!** автоматическое удаление не исключает наличие дубликатов в базе данных, т.к. между началом заливки данных и удалением есть промежуток времени.
Но в идеале все данные после завершения работы скрипта matomo2clickhouse и до начала его следующего запуска БЕЗ дубликатов.
**Т.е. формально в select-запросах с фильтром "сейчас минус 2 часа" данные должны быть корректны:**
```
matomo.matomo_log_link_visit_action.server_time <= (DATE_sub(NOW(), INTERVAL 2 HOUR))
matomo.matomo_log_visit.visit_first_action_time <= (DATE_sub(NOW(), INTERVAL 2 HOUR))
```
  