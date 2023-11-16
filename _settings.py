# -*- coding: utf-8 -*-
# matomo2clickhouse
# https://github.com/dneupokoev/matomo2clickhouse
#
# Replication Matomo from MySQL to ClickHouse
# Репликация Matomo: переливка данных из MySQL в ClickHouse
#
# 231116.01
# + добавил параметр settings.CONST_TBL_NOT_DELETE_OLD - словарь с таблицами, для которых не надо удалять старые данные, если они удалены в самом matomo.
#
# 230727.01
# + добавил параметр settings..sql_execute_at_end_matomo2clickhouse: скрипты, которые выполнятся в конце работы matomo2clickhouse (можно использовать для удаления дублей или для других задач)
#
# 230403:
# + добавил параметр settings.EXECUTE_CLICKHOUSE (нужен для тестирования) - True: выполнять insert в ClickHouse (боевой режим); False: не выполнять insert (для тестирования и отладки)
# + изменил параметр CH_matomo_dbname - теперь базы в MySQL и ClickHouse могут иметь разные названия
#
# 221005:
# + базовая стабильная версия (полностью протестированная и отлаженная)
#
#
# ВНИМАНИЕ!!! Перед запуском необходимо ЗАПОЛНИТЬ пароли в данном файле и ПЕРЕИМЕНОВАТЬ его в settings.py
#
# подключение к mysql (matomo)
MySQL_matomo_host = '192.168.5.'
MySQL_matomo_port = 3306
MySQL_matomo_dbname = 'matomo'
MySQL_matomo_user = 'user'
MySQL_matomo_password = 'password'
#
CH_matomo_host = '192.168.5.'
CH_matomo_port = 9000
CH_matomo_dbname = 'matomo'
CH_matomo_user = 'user'
CH_matomo_password = 'password'
#
#
#
# *** Настройки ***
# для избыточного логирования True (для тестирования и отладки), иначе False
# DEBUG = True
DEBUG = False
#
# EXECUTE_CLICKHOUSE - True: выполнять insert в ClickHouse (боевой режим); False: не выполнять insert (для тестирования и отладки)
EXECUTE_CLICKHOUSE = True
# EXECUTE_CLICKHOUSE = False
#
# создаем папку для логов:
# sudo mkdir /var/lib/matomo2clickhouse
# выдаем полные права на папку:
# sudo chmod 777 /var/lib/matomo2clickhouse
PATH_TO_LIB = '/var/lib/matomo2clickhouse/'
#
# создаем папку для переменных данного проекта:
# sudo mkdir /var/log/matomo2clickhouse
# выдаем полные права на папку:
# sudo chmod 777 /var/log/matomo2clickhouse
PATH_TO_LOG = '/var/log/matomo2clickhouse/'
#
#
# Какое максимальное количество запросов обрабатывать за один вызов скрипта
# replication_batch_size - общее количество строк (ВНИМАНИЕ! минимум 1!!! иначе ничего обрабатывать не будет)
# replication_batch_size = 10
replication_batch_size = 1000000
#
# replication_batch_sql - строк в одном коннекте (ВНИМАНИЕ! Для построчного выполнения = 0)
# Оптимально около 2000. Если сделать слишком мало, то будет медленно. Если сделать слишком много, то либо съест ОЗУ, либо ClickHouse не сможет обработать такой большой запрос.
replication_batch_sql = 2000
#
# Какое максимальное количество файлов binlog-а обрабатывать за один вызов (если поставить слишком много, то может надолго подвиснуть)
replication_max_number_files_per_session = 20
#
# максимальное количество минут работы скрипта до остановки (0 - без остановки, int - может понадобиться, чтобы гибче управлять автозапуском)
# ВНИМАНИЕ! реально может работать на несколько минут дольше указанного
replication_max_minutes = 50
#
#
# LEAVE_BINARY_LOGS_IN_DAYS - оставляем бинарные логи за предыдущие Х дней
# ВНИМАНИЕ! логи чистятся только если последняя точка репликации позже, чем точка в логах для удаления NOW-точка > LEAVE_BINARY_LOGS_IN_DAYS
LEAVE_BINARY_LOGS_IN_DAYS = 180
# sql: PURGE BINARY LOGS BEFORE DATE(NOW() - INTERVAL 30 DAY) + INTERVAL 0 SECOND;
#
#
# Таблицы, которые нужно реплицировать (только эти таблицы будут заливаться в базу-приемник)
# Ключевые таблицы matomo:
# log_visit - содержит одну запись за посещение (данные о сессии: начало, конец, инфа о посетителе, стандартные utm и т.д.)
# log_action - содержит все типы действий, возможных на веб-сайте (например, уникальные URL-адреса, заголовки страниц, URL-адреса загрузки и т.д.)
# log_link_visit_action - содержит одну запись на каждое действие посетителя (просмотр страницы, т.д.)
# log_conversion - содержит конверсии (действия, соответствующие цели), которые произошли во время посещения
# log_conversion_item - содержит элементы конверсии электронной коммерции
#
# Если необходимо добавить таблицы, то нужно СНАЧАЛА СОЗДАТЬ структуру в ClickHouse,
# ( соответствие типов данных MySQL-ClickHouse: https://clickhouse.com/docs/en/engines/database-engines/mysql/ )
# потом залить в CH данные, которые уже есть в MySQL и
# добавить названия таблиц сюда:
replication_tables = [
    'matomo_custom_dimensions',
    'matomo_goal',
    'matomo_log_action',
    'matomo_log_conversion',
    'matomo_log_conversion_item',
    'matomo_log_link_visit_action',
    'matomo_log_profiling',
    'matomo_log_visit',
    'matomo_site',
    'matomo_site_url',
    # 'matomo_tagmanager_container',
    # 'matomo_tagmanager_container_release',
    # 'matomo_tagmanager_container_version',
    # 'matomo_tagmanager_tag',
    # 'matomo_tagmanager_trigger',
    # 'matomo_tagmanager_variable',
]
#
# таблицы, в которые все update будем менять на insert
# ВНИМАНИЕ! в этих таблицах в кликхаусе должно быть поле dateid UInt64
# чтобы потом корректно с этим работать нужно брать самую свежую запись (максимальное значение поля dateid)
tables_not_updated = [
    'matomo_log_visit',
    'matomo_log_link_visit_action',
]
#
# CONST_TBL_NOT_DELETE_OLD - словарь с таблицами, для которых не надо удалять старые данные, если они удалены в самом matomo.
# col_date - название колонки, дату в которой будем сравнивать с текущей датой.
CONST_TBL_NOT_DELETE_OLD = {
    'matomo_log_visit': {'col_date': 'visit_first_action_time'},
    'matomo_log_link_visit_action': {'col_date': 'server_time'},
    'matomo_log_conversion': {'col_date': 'server_time'},
}
#
# Удаление старых дубликатов
# Если tables_not_updated заполнено, то в указанных таблицах будут копиться старые устаревшие данные.
# Эти данные можно отсекать на уровне запросов (например, при подготовке витрин данных), а можно удалять.
# Для удаления нужно заполнить список tables_clear_old_duplicates запросами, которые выполнятся в конце работы matomo2clickhouse:
sql_execute_at_end_matomo2clickhouse = [
    '''
    /* делает выборку dateid, которые нужно удалить, отправляет на удаление и ждет окончания мутации */
    ALTER TABLE {CH_matomo_dbname}.matomo_log_link_visit_action DELETE
    WHERE 1=1
    AND server_time >= (DATE_sub(NOW(), INTERVAL {dv_days_ago_start} DAY))
    AND server_time <= (DATE_sub(NOW(), INTERVAL {dv_days_ago_finish} DAY))
    AND dateid in (
        SELECT t2.dateid_for_del
        FROM (
            SELECT idlink_va, dateid AS dateid_for_del
            FROM {CH_matomo_dbname}.matomo_log_link_visit_action
            WHERE 1=1
            AND server_time >= (DATE_sub(NOW(), INTERVAL {dv_days_ago_start} DAY))
            AND server_time <= (DATE_sub(NOW(), INTERVAL {dv_days_ago_finish} DAY))
        ) t2
        RIGHT JOIN (
            SELECT idlink_va, max(dateid) AS dateid_max, count(*) AS id_count
            FROM {CH_matomo_dbname}.matomo_log_link_visit_action
            WHERE 1=1
            AND server_time >= (DATE_sub(NOW(), INTERVAL {dv_days_ago_start} DAY))
            AND server_time <= (DATE_sub(NOW(), INTERVAL {dv_days_ago_finish} DAY))
            GROUP BY idlink_va
            HAVING id_count > 1
        ) t1 ON t2.idlink_va = t1.idlink_va
        WHERE t2.dateid_for_del <> t1.dateid_max
    )
    SETTINGS mutations_sync = 1;
    '''.format(CH_matomo_dbname=CH_matomo_dbname, dv_days_ago_start=14, dv_days_ago_finish=0),
    '''
    /* делает выборку dateid, которые нужно удалить, отправляет на удаление и ждет окончания мутации */
    ALTER TABLE {CH_matomo_dbname}.matomo_log_visit DELETE
    WHERE 1=1
    AND visit_first_action_time >= (DATE_sub(NOW(), INTERVAL {dv_days_ago_start} DAY))
    AND visit_first_action_time <= (DATE_sub(NOW(), INTERVAL {dv_days_ago_finish} DAY))
    AND dateid in (
        SELECT t2.dateid_for_del
        FROM (
            SELECT idvisit, dateid AS dateid_for_del
            FROM {CH_matomo_dbname}.matomo_log_visit
            WHERE 1=1
            AND visit_first_action_time >= (DATE_sub(NOW(), INTERVAL {dv_days_ago_start} DAY))
            AND visit_first_action_time <= (DATE_sub(NOW(), INTERVAL {dv_days_ago_finish} DAY))
        ) t2
        RIGHT JOIN (
            SELECT idvisit, max(dateid) AS dateid_max, count(*) AS id_count
            FROM {CH_matomo_dbname}.matomo_log_visit
            WHERE 1=1
            AND visit_first_action_time >= (DATE_sub(NOW(), INTERVAL {dv_days_ago_start} DAY))
            AND visit_first_action_time <= (DATE_sub(NOW(), INTERVAL {dv_days_ago_finish} DAY))
            GROUP BY idvisit
            HAVING id_count > 1
        ) t1 ON t2.idvisit = t1.idvisit
        WHERE t2.dateid_for_del <> t1.dateid_max
    )
    SETTINGS mutations_sync = 1;
    '''.format(CH_matomo_dbname=CH_matomo_dbname, dv_days_ago_start=14, dv_days_ago_finish=0),
]
#
#
#
# True - Проверять свободное место на диске, False - не проверять
CHECK_DISK_SPACE = False
#
#
# TELEGRAM
# True - отправлять результат в телеграм, False - не отправлять
SEND_TELEGRAM = False
# SEND_SUCCESS_REPEATED_NOT_EARLIER_THAN_MINUTES - минимальное количество минут между отправками УСПЕХА (чтобы не заспамить)
SEND_SUCCESS_REPEATED_NOT_EARLIER_THAN_MINUTES = 360
# создать бота - получить токен - создать группу - бота сделать администратором - получить id группы
TLG_BOT_TOKEN = 'your_bot_token'
# TLG_CHAT_FOR_SEND = идентификатор группы
# Как узнать идентификтор группы:
# 1. Добавить бота в нужную группу;
# 2. Написать хотя бы одно сообщение в неё;
# 3. Отправить GET-запрос по следующему адресу:
# curl https://api.telegram.org/bot<your_bot_token>/getUpdates
# 4. Взять значение "id" из объекта "chat". Это и есть идентификатор чата. Для групповых чатов он отрицательный, для личных переписок положительный.
TLG_CHAT_FOR_SEND = -000
#
#
#
#
#
#
#
#
#
#
#
# ВНИМАНИЕ!!! Дальше настройки работы. Перед тем как их трогать НЕОБХОДИМО разобраться в настройках и понимать что к чему!
#
MySQL_connect = [f"-h{MySQL_matomo_host}",
                 f"-P{MySQL_matomo_port}",
                 f"-u{MySQL_matomo_user}",
                 f"-p{MySQL_matomo_password}",
                 f"-d{MySQL_matomo_dbname}",
                 ]
CH_connect = {'host': CH_matomo_host, 'port': CH_matomo_port, 'database': CH_matomo_dbname}
#
#
# Переменная с параметрами для выгрузки бинлога MySQL в ClickHouse
args_for_mysql_to_clickhouse = [''] + \
                               MySQL_connect + \
                               ['-t'] + replication_tables + \
                               ['--for_clickhouse', '--only-dml']
#
#
#
#
#
import telebot


#
#
def f_telegram_send_message(tlg_bot_token='', tlg_chat_id=None, txt_to_send='', txt_mode=None, txt_type='', txt_name=''):
    '''
    Функция отправляет в указанный чат телеграма текст
    Входные параметры: токен, чат, текст, тип форматирования текста (HTML, MARKDOWN)
    '''
    if txt_type == 'ERROR':
        txt_type = '❌'
        # txt_type = '\u000274C'
    elif txt_type == 'WARNING':
        txt_type = '⚠'
        # txt_type = '\U0002757'
    elif txt_type == 'INFO':
        txt_type = 'ℹ'
        # txt_type = '\U0002755'
    elif txt_type == 'SUCCESS':
        txt_type = '✅'
        # txt_type = '\U000270'
    else:
        txt_type = ''
    txt_to_send = f"{txt_type} {txt_name} | {txt_to_send}"
    try:
        # dv_tlg_bot = telebot.TeleBot(TLG_BOT_TOKEN, parse_mode=None)
        # dv_tlg_bot = telebot.TeleBot(TLG_BOT_TOKEN, parse_mode='MARKDOWN')
        dv_tlg_bot = telebot.TeleBot(tlg_bot_token, parse_mode=txt_mode)
        # отправляем текст
        tmp_out = dv_tlg_bot.send_message(tlg_chat_id, txt_to_send[0:3999])
        return f"chat_id = {tlg_chat_id} | message_id = {tmp_out.id} | html_text = '{tmp_out.html_text}'"
    except Exception as error:
        return f"ERROR: {error}"
