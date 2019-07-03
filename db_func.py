#!/usr/bin/python
# coding=utf-8

import sqlite3
import time
import var_config
import var_func


def db_service_database_path(db_path):
    global database
    database = db_path


def db_service_database_conn_open():
    global conn
    global database
    conn = sqlite3.connect(database, check_same_thread=False)


def db_service_database_conn_close():
    global conn
    conn.close()


def db_service_restart_daemon_trigger(cid=0, mid=0):
    global conn
    cursor = conn.cursor()
    sql = """SELECT flag FROM restart_daemon_check"""
    cursor.execute(sql)
    data = cursor.fetchone()
    if data[0] == 1:
        sql = """UPDATE restart_daemon_check SET flag='0', cid='0', mid='0'"""
        cursor.execute(sql)
        conn.commit()

    else:
        sql = """UPDATE restart_daemon_check SET flag='1', cid='{0}', mid='{1}'""".format(cid, mid)
        cursor.execute(sql)
        conn.commit()


def db_service_get_restart_trigger():
    global conn
    cursor = conn.cursor()
    sql = """SELECT flag, cid, mid FROM restart_daemon_check"""
    cursor.execute(sql)
    data = cursor.fetchone()

    return data


def db_service_check_restart_trigger_table_exists():
    global conn
    cursor = conn.cursor()
    cursor.execute("""SELECT count(*) FROM sqlite_master WHERE type='table' AND name='restart_daemon_check'""")
    if cursor.fetchone()[0] == 1:

        return True
    else:

        return False


def db_service_create_chat_table(cid):
    global conn
    cursor = conn.cursor()
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS {0}
        (uid integer,
        username text,
        added integer,
        last_activity integer,
        last_return integer,
        rights integer,
        a_msg integer,
        m_msg integer,
        w_msg integer,
        d_msg integer,
        a_stickers integer,
        m_stickers integer,
        w_stickers integer,
        d_stickers integer,
        a_photos integer,
        m_photos integer,
        w_photos integer,
        d_photos integer,
        a_audio integer,
        m_audio integer,
        w_audio integer,
        d_audio integer,
        a_videomessages integer,
        m_videomessages integer,
        w_videomessages integer,
        d_videomessages integer,
        a_voicemessages integer,
        m_voicemessages integer,
        w_voicemessages integer,
        d_voicemessages integer,
        a_files integer,
        m_files integer,
        w_files integer,
        d_files integer,
        warn_count integer,
        mute_count integer,
        ban_count integer,
        achievements text,
        titles text)""".format('chat_' + str(cid)[1:] + '_users_info'))
    cursor.execute("""INSERT INTO chats_parameters VALUES
            (
            '{chat_id}', '{chat_name}', '{chat_forward_to}', '{echo_all_avialable}',
            '{welcome_msg_default}', '{welcome_msg_approved}', '{welcome_msg_returning}',
            '{voicemessages_limit}', 
            '{warn_swelling_time}', '{warn_automute_time}',
            '{sticker_automute_limit}', '{sticker_automute_time}'
            )""".format(chat_id=str(cid)[1:],
                        chat_name='',
                        chat_forward_to=0,
                        echo_all_avialable=0,
                        welcome_msg_default='',
                        welcome_msg_approved='',
                        welcome_msg_returning='',
                        voicemessages_limit=0,
                        warn_swelling_time=var_config.default_warn_swelling_time,
                        warn_automute_time=var_config.default_automute_time,
                        sticker_automute_limit=var_config.default_sticker_automute_limit,
                        sticker_automute_time=var_config.default_automute_time))
    conn.commit()


def db_service_init_tech_tables():
    global conn
    cursor = conn.cursor()
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS warns_info (
        uid integer,
        cid integer,
        time integer,
        who text,
        reason text)""")
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS mutes_info (
        uid integer,
        cid integer,
        mute_for integer,
        time integer,
        who text,
        reason text)""")
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS bans_info (
        uid integer,
        cid integer,
        time integer,
        who text,
        reason text)""")
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS bot_messages (
        cid integer,
        date integer,
        mid integer)""")
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS comm_usage (
        cid integer,
        uid integer,
        a_comm integer,
        report integer,
        userinfo integer,
        me integer,
        slap integer,
        usuka integer,
        wtfisgoingon integer,
        badumtss integer,
        topmsg integer,
        topweeklymsg integer,
        topdailymsg integer,
        topmonthlymsg integer,
        eww integer)""")
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS mod_comm_usage (
        cid integer,
        uid integer,
        a_comm integer,
        warn integer,
        mute integer,
        ban integer,
        pin integer,
        chmod integer,
        resync integer)""")
    cursor.execute("""SELECT count(*) FROM sqlite_master WHERE type='table' AND name='tech_message_count_reset_date'""")
    if not cursor.fetchone()[0] == 1:
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS tech_message_count_reset_date (
            reset_time_month integer,
            reset_time_week integer,
            reset_time_day integer)""")
        cursor.execute(
            """INSERT INTO tech_message_count_reset_date VALUES ('1559347200', '1560729600', '1560902400')""")

    cursor.execute("""SELECT count(*) FROM sqlite_master WHERE type='table' AND name='restart_daemon_check'""")
    if not cursor.fetchone()[0] == 1:
        cursor.execute("""CREATE TABLE IF NOT EXISTS restart_daemon_check(flag integer, cid integer, mid integer)""")
        cursor.execute("""INSERT INTO restart_daemon_check VALUES ('0', '0', '0')""")

    cursor.execute("""SELECT count(*) FROM sqlite_master WHERE type='table' AND name='chats_parameters'""")
    if not cursor.fetchone()[0] == 1:
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS chats_parameters
            (cid integer,
            chat_name text,
            chat_forward_to integer,
            echo_all_avialable integer, 
            welcome_msg_default text,
            welcome_msg_approved text,
            welcome_msg_returning text,
            voicemessages_limit integer,
            warn_swelling_time integer,
            warn_automute_time integer,
            sticker_automute_limit integer,
            sticker_automute_time integer
            )""")
    conn.commit()


####temp function####
def db_transform2():
    global conn
    cursor = conn.cursor()
    chatlist = db_tech_get_all_chat_tables_list()
    for foo in chatlist:
        chat_id = foo.split('_')

        cursor.execute("""INSERT INTO chats_parameters VALUES
        (
        '{cid}', '{chat_name}', '{chat_forward_to}', '{echo_all_avialable}',
        '{welcome_msg_default}', '{welcome_msg_approved}', '{welcome_msg_returning}',
        '{voicemessages_limit}', 
        '{warn_swelling_time}', '{warn_automute_time}',
        '{sticker_automute_limit}', '{sticker_automute_time}'
        )""".format(cid=chat_id[1],
                    chat_name='',
                    chat_forward_to=0,
                    echo_all_avialable=0,
                    welcome_msg_default='',
                    welcome_msg_approved='',
                    welcome_msg_returning='',
                    voicemessages_limit=0,
                    warn_swelling_time=var_config.default_warn_swelling_time,
                    warn_automute_time=var_config.default_automute_time,
                    sticker_automute_limit=var_config.default_sticker_automute_limit,
                    sticker_automute_time=60))
    conn.commit()
    cursor.execute("""SELECT * FROM antibot_welcome_messages""")
    data = cursor.fetchall()
    for chat in data:
        cid = chat[0]
        welcome_msg_default = chat[1]
        welcome_msg_approved = chat[2]
        welcome_msg_returning = chat[3]
        cursor.execute("""UPDATE chats_parameters
        SET welcome_msg_default = '{0}',
        welcome_msg_approved = '{1}',
        welcome_msg_returning = '{2}'
        WHERE cid = '{3}'
        """.format(welcome_msg_default, welcome_msg_approved, welcome_msg_returning, cid))
    for chat in var_config.chats_for_echo_all:
        cursor.execute("""UPDATE chats_parameters
                SET echo_all_avialable = 1
                WHERE cid = {0}""".format(int(chat)))
    for foo in chatlist:
        chat_id = foo.split('_')
        if var_config.service_get_chat_forwarding('-' + chat_id[1]) is not False:
            cursor.execute("""UPDATE chats_parameters
            SET chat_forward_to = '{0}'
            WHERE cid = '{1}'""".format(var_config.service_get_chat_forwarding('-' + chat_id[1])[1:], chat_id[1]))
        cursor.execute("""SELECT uid, rights FROM {0}""".format(foo))
        data = cursor.fetchall()
        for user in data:
            if user[0] == var_config.master_id:
                cursor.execute("""UPDATE {0} 
                SET rights = '{1}'
                WHERE uid = '{2}'""".format(foo, int(str(user[1]) + '1'), user[0]))
            else:
                cursor.execute("""UPDATE {0} 
                                SET rights = '{1}'
                                WHERE uid = '{2}'""".format(foo, int(str(user[1]) + '0'), user[0]))
    cursor.execute("""DROP TABLE antibot_welcome_messages""")
    print('finished')
    conn.commit()


def db_service_check_chat_table_exists(cid):
    global conn
    cursor = conn.cursor()
    cursor.execute("""SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{0}'""".format(
        'chat_' + str(cid)[1:] + '_users_info'))
    if cursor.fetchone()[0] == 1:

        return True
    else:

        return False


def db_service_check_user_exists(cid, uid):
    global conn
    cursor = conn.cursor()
    cursor.execute("""SELECT * FROM '{0}' WHERE uid = '{1}'""".format('chat_' + str(cid)[1:] + '_users_info', uid))
    data = cursor.fetchone()

    if data is not None:
        return True
    else:
        return False


def db_stat_add_new_user(cid, uid, username):
    global conn
    cursor = conn.cursor()
    current_time = int(time.time())
    cursor.execute("""INSERT INTO {0} VALUES (
    '{1}', '{2}', '{3}', '{4}', 
    '{5}', '{6}', '{7}', '{8}',
    '{9}', '{10}', '{11}', '{12}', 
    '{13}', '{14}','{15}', '{16}', 
    '{17}', '{18}', '{19}', '{20}', 
    '{21}', '{22}', '{23}', '{24}', 
    '{25}', '{26}', '{27}', '{28}', 
    '{29}','{30}', '{31}', '{32}', '{33}', 
    '{34}','{35}','{36}', '{37}', '{38}', '{39}'
    )""".format('chat_' + str(cid)[1:] + '_users_info',
                uid, username, current_time, current_time,
                current_time, 100000000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                0,
                0, 0, 0, 0, '', ''))
    cursor.execute("""INSERT INTO comm_usage VALUES (
    '{0}','{1}', 
    '{2}','{3}','{4}',
    '{5}','{6}','{7}', 
    '{8}','{9}','{10}', 
    '{11}','{12}','{13}', 
    '{14}')""".
                   format(str(cid)[1:], uid,
                          0, 0, 0,
                          0, 0, 0,
                          0, 0, 0,
                          0, 0, 0,
                          0))

    cursor.execute("""INSERT INTO mod_comm_usage VALUES (
    '{0}', '{1}', 
    '{2}', '{3}', '{4}',
    '{5}', '{6}', '{7}', 
    '{8}')""".format(str(cid)[1:], uid,
                     0, 0, 0,
                     0, 0, 0,
                     0))
    conn.commit()

    return True


def db_mod_set_chmod_for_user(cid, uid, rights):
    global conn
    cursor = conn.cursor()
    sql = """
            UPDATE {0}
            SET rights = '{1}'
            WHERE uid = '{2}'
            """.format('chat_' + str(cid)[1:] + '_users_info', rights, uid)
    cursor.execute(sql)
    conn.commit()

    return True


def db_service_check_user_have_rights(cid, uid, right):
    global conn
    cursor = conn.cursor()
    sql = """
    SELECT rights 
    FROM '{0}' 
    WHERE uid = '{1}'
    """.format('chat_' + str(cid)[1:] + '_users_info', uid)
    cursor.execute(sql)
    data = cursor.fetchone()
    rights = [int(x) for x in str(data[0])]

    # actions, warn, mute, ban, pin, chmod, resync, set_antibot
    res = False
    if right == 'actions' and rights[0] == 1:
        res = True
    elif right == 'warn' and rights[1] == 1:
        res = True
    elif right == 'mute' and rights[2] == 1:
        res = True
    elif right == 'ban' and rights[3] == 1:
        res = True
    elif right == 'pin' and rights[4] == 1:
        res = True
    elif right == 'chmod' and rights[5] == 1:
        res = True
    elif right == 'resync' and rights[6] == 1:
        res = True
    elif right == 'set_antibot' and rights[7] == 1:
        res = True
    elif right == 'chat_config' and rights[8] == 1:
        res = True

    return res


def db_service_get_all_rights_for_user(cid, uid):
    # actions, warn, mute, ban, pin, chmod, resync
    global conn
    cursor = conn.cursor()
    sql = """
    SELECT rights 
    FROM '{0}' 
    WHERE uid = '{1}'
    """.format('chat_' + str(cid)[1:] + '_users_info', uid)
    cursor.execute(sql)
    data = cursor.fetchone()

    rights = [int(x) for x in str(data[0])]
    return rights


def db_mod_increase_ban_count_for_user(cid, ruid, uid, reason):
    global conn
    cursor = conn.cursor()
    cursor.execute("""
            SELECT ban_count
            FROM '{0}' 
            WHERE uid = '{1}'
            """.format('chat_' + str(cid)[1:] + '_users_info', ruid))
    data = cursor.fetchone()
    ban_count = data[0] + 1
    cursor.execute("""
        UPDATE {0}
        SET ban_count = '{1}'
        WHERE uid = '{2}'""".format('chat_' + str(cid)[1:] + '_users_info', ban_count, ruid))
    cursor.execute("""INSERT INTO bans_info 
        VALUES (
        '{0}',
        '{1}',
        '{2}',
        '{3}',
        '{4}'
        )""".format(ruid, str(cid)[1:], int(time.time()), uid, reason))
    conn.commit()

    return True


def db_mod_increase_warn_count_for_user(cid, ruid, uid, reason):
    global conn
    cursor = conn.cursor()
    cursor.execute("""
        SELECT warn_count
        FROM '{0}' 
        WHERE uid = '{1}'
        """.format('chat_' + str(cid)[1:] + '_users_info', ruid))
    data = cursor.fetchone()
    warn_count = data[0] + 1
    cursor.execute("""
    UPDATE {0}
    SET warn_count = '{1}'
    WHERE uid = '{2}'""".format('chat_' + str(cid)[1:] + '_users_info', warn_count, ruid))
    cursor.execute("""INSERT INTO warns_info 
    VALUES (
    '{0}',
    '{1}',
    '{2}',
    '{3}',
    '{4}'
    )""".format(ruid, str(cid)[1:], int(time.time()), uid, reason))
    conn.commit()

    return warn_count


def db_mod_increase_mute_count_for_user(ruid, cid, mute_time, uid, mute_reason):
    global conn
    cursor = conn.cursor()
    cursor.execute("""
        SELECT mute_count
        FROM '{0}' 
        WHERE uid = '{1}'
        """.format('chat_' + str(cid)[1:] + '_users_info', ruid))
    data = cursor.fetchone()
    mute_count = data[0] + 1
    cursor.execute("""
    UPDATE {0}
    SET mute_count = '{1}'
    WHERE uid = '{2}'""".format('chat_' + str(cid)[1:] + '_users_info', mute_count, ruid))

    cursor.execute("""
    INSERT INTO mutes_info 
    VALUES (
    '{0}',
    '{1}',
    '{2}',
    '{3}',
    '{4}',
    '{5}'
    )""".format(ruid, str(cid)[1:], int(time.time()), mute_time, uid, mute_reason))
    conn.commit()

    return True


def db_mod_remove_last_warn_for_user(cid, ruid):
    global conn
    cursor = conn.cursor()
    cursor.execute("""
            SELECT warn_count
            FROM '{0}' 
            WHERE uid = '{1}'
            """.format('chat_' + str(cid)[1:] + '_users_info', ruid))
    data = cursor.fetchone()
    warn_count = data[0] - 1
    cursor.execute("""DELETE FROM warns_info
            WHERE ROWID in
            (
            SELECT ROWID FROM warns_info WHERE uid = {0} AND cid = {1} ORDER BY time DESC LIMIT 1
            )            
            """.format(ruid, str(cid)[1:]))
    cursor.execute("""
    UPDATE {0} 
    SET warn_count = '{1}'
    WHERE uid = '{2}'""".format('chat_' + str(cid)[1:] + '_users_info', warn_count, ruid))
    conn.commit()
    return True


def db_mod_nullify_warn_count_for_user(cid, ruid):
    global conn
    cursor = conn.cursor()
    cursor.execute("""DELETE FROM warns_info
                WHERE uid = {0} AND cid = {1}
                """.format(ruid, str(cid)[1:]))
    cursor.execute("""
        UPDATE {0} 
        SET warn_count = '{1}'
        WHERE uid = '{2}'""".format('chat_' + str(cid)[1:] + '_users_info', 0, ruid))
    conn.commit()
    return True


def db_mod_get_current_warn_info_for_user(cid, uid):
    global conn
    cursor = conn.cursor()
    cursor.execute("""
            SELECT warn_count
            FROM '{0}' 
            WHERE uid = '{1}'
            """.format('chat_' + str(cid)[1:] + '_users_info', uid))
    # data = cursor.fetchone()
    a_warn_count = cursor.fetchone()
    cursor.execute("""
    SELECT reason
    FROM warns_info
    WHERE uid = '{0}' AND cid = '{1}' 
    ORDER BY time DESC LIMIT 1""".format(uid, str(cid)[1:]))
    data = cursor.fetchone()
    if data is not None:
        last_warn_reason = data[0]
    else:
        last_warn_reason = ''

    return [a_warn_count, last_warn_reason]


def db_stat_get_message_count_for_user(cid, uid):
    """
    :rtype: tuple(int message_count)
    """
    global conn
    cursor = conn.cursor()
    sql = """
            SELECT a_msg, m_msg, w_msg, d_msg
            FROM '{0}' 
            WHERE uid = '{1}'
            """.format('chat_' + str(cid)[1:] + '_users_info', uid)
    cursor.execute(sql)
    data = cursor.fetchone()

    return data


def db_service_get_username_from_db(cid, uid):
    global conn
    cursor = conn.cursor()
    cursor.execute("""
        SELECT username 
        FROM '{0}' 
        WHERE uid = '{1}'
        """.format('chat_' + str(cid)[1:] + '_users_info', uid))
    data = cursor.fetchone()

    if data is not None:
        return data[0]
    else:
        return False


def db_service_update_username_for_user(cid, uid, username):
    global conn
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE {0} 
        SET username = '{1}' 
        WHERE uid = '{2}'
        """.format('chat_' + str(cid)[1:] + '_users_info', username, uid))
    conn.commit()


def db_stat_update_user_last_return(cid, uid):
    global conn
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE {0} 
        SET last_return = '{1}' 
        WHERE uid = '{2}'
    """.format('chat_' + str(cid)[1:] + '_users_info', int(time.time()), uid))
    conn.commit()
    return True


def db_tech_get_all_chat_tables_list():
    global conn
    cursor = conn.cursor()
    cursor.execute("""SELECT name FROM sqlite_master WHERE type='table'""")
    data = cursor.fetchall()

    table_list = []
    for table in data:
        if '_users_info' in table[0]:
            table_list += table
    return table_list


def db_stat_update_user_message_count(cid, uid, message_type='msg'):
    # count_type can be msg, stickers, photos, audio, videomessages, voicemessages, files
    global conn
    cursor = conn.cursor()
    sql = """
    SELECT a_{2}, m_{2}, w_{2}, d_{2}
    FROM '{0}' 
    WHERE uid = '{1}'
    """.format('chat_' + str(cid)[1:] + '_users_info', uid, message_type)
    cursor.execute(sql)
    data = cursor.fetchone()
    current_a_msg_count = int(data[0]) + 1
    current_m_msg_count = int(data[1]) + 1
    current_w_msg_count = int(data[2]) + 1
    current_d_msg_count = int(data[3]) + 1
    sql = """
    UPDATE {0}
    SET a_{1} = '{a_msg_count}',
    m_{1} = '{m_msg_count}',
    w_{1} = '{w_msg_count}',
    d_{1} = '{d_msg_count}',
    last_activity = '{2}'
    WHERE uid = '{3}'
    """.format('chat_' + str(cid)[1:] + '_users_info', message_type, int(time.time()), uid,
               a_msg_count=current_a_msg_count,
               m_msg_count=current_m_msg_count,
               w_msg_count=current_w_msg_count,
               d_msg_count=current_d_msg_count)
    cursor.execute(sql)
    conn.commit()

    return True


def db_stat_update_user_command_count(cid, uid, command_type):
    # command_type can be:
    # - report, userinfo, me, slap, usuka, wtfisgoingon, badumtss
    # - warn, mute, ban, pin, chmod, resync
    global conn
    cursor = conn.cursor()
    table = ''
    if command_type in ['report', 'userinfo', 'me', 'eww', 'slap', 'usuka', 'wtfisgoingon', 'badumtss', 'topmsg',
                        'topweeklymsg', 'topdailymsg', 'topmonthlymsg', 'eww']:
        table = 'comm_usage'
    if command_type in ['warn', 'mute', 'ban', 'pin', 'chmod', 'resync']:
        table = 'mod_comm_usage'
    cursor.execute("""
    SELECT a_comm, {0}
    FROM {1}
    WHERE cid = '{2}' AND uid = '{3}'""".format(command_type, table, str(cid)[1:], uid))
    data = cursor.fetchone()
    foo = data[0] + 1
    bar = data[1] + 1
    cursor.execute("""
        UPDATE {0}
        SET a_comm = '{1}', 
        {2} = '{3}'
        WHERE cid = '{4}' AND uid = '{5}'""".format(table, foo, command_type, bar, str(cid)[1:], uid))
    conn.commit()


def db_service_reset_message_counters(countertype, new_timer, msg_type='msg'):
    # countertype can be day, week, month
    # msg_type can be msg, stickers, photos, audio, videomessages, voicemessages, files
    chats_for_work = db_tech_get_all_chat_tables_list()
    global conn
    cursor = conn.cursor()
    cursor.execute("""UPDATE tech_message_count_reset_date SET reset_time_{0}='{1}'""".format(countertype, new_timer))
    for table in chats_for_work:
        cursor.execute("""UPDATE {0} SET m_{1}=0""".format(table, msg_type))
    conn.commit()


def db_service_reset_message_counters_for_users(msg_type='msg'):
    # msg_type can be msg, stickers, photos, audio, videomessages, voicemessages, files
    current_time = int(time.time())
    current_triggers = var_func.check_triggers_for_timestamp(current_time)

    global conn
    cursor = conn.cursor()
    chats_for_work = db_tech_get_all_chat_tables_list()
    cursor.execute("""SELECT 
    reset_time_month, 
    reset_time_week, 
    reset_time_day 
    FROM tech_message_count_reset_date""")
    data = cursor.fetchone()
    stored_trigger_month = var_func.check_triggers_for_timestamp(int(data[0]))[2]
    stored_trigger_week = var_func.check_triggers_for_timestamp(int(data[1]))[1]
    stored_trigger_day = var_func.check_triggers_for_timestamp(int(data[2]))[0]
    output_message = ""
    # monthly
    if current_triggers[2] != stored_trigger_month:
        cursor.execute(
            """UPDATE tech_message_count_reset_date 
            SET reset_time_month='{0}'""".format(var_func.get_first_day_of_month()))
        for table in chats_for_work:
            cursor.execute("""UPDATE {0} 
            SET m_{1}=0""".format(table, msg_type))
        conn.commit()
        output_message += "Reset Monthly messages; "

    # weekly
    if current_triggers[1] != stored_trigger_week:
        cursor.execute(
            """UPDATE tech_message_count_reset_date 
            SET reset_time_week='{0}'""".format(var_func.get_last_monday()))
        for table in chats_for_work:
            cursor.execute("""UPDATE {0} 
            SET w_{1}=0""".format(table, msg_type))
        conn.commit()
        output_message += "Reset Weekly messages; "

    # daily
    if current_triggers[0] != stored_trigger_day:
        cursor.execute(
            """UPDATE tech_message_count_reset_date 
            SET reset_time_day='{0}'""".format(var_func.get_last_midnight()))
        for table in chats_for_work:
            cursor.execute("""UPDATE {0} 
            SET d_{1}=0""".format(table, msg_type))
        conn.commit()
        output_message += "Reset Daily messages; "
    return output_message


def db_service_warn_swelling():
    current_time = int(time.time())
    global conn
    cursor = conn.cursor()
    cursor.execute("""
    SELECT ROWID, time, cid, uid FROM warns_info ORDER BY time DESC
    """)
    warns_data = cursor.fetchall()
    for warn in warns_data:
        cursor.execute("""SELECT warn_swelling_time FROM chats_parameters WHERE cid = '{0}'""".format(warn[2]))
        warn_swelling_time_for_current_chat = cursor.fetchone()[0]
        if current_time - warn[1] > warn_swelling_time_for_current_chat:
            db_mod_remove_last_warn_for_user('-' + str(warn[2]), warn[3])
    return warns_data


def db_stat_get_top_flooders(cid, limit=5, duration='a', msg_type='msg'):
    # duration: a, m, w, d = all, month, week, day
    # msg_type: msg, stickers, photos, audio, videomessages, voicemessages, files
    global conn
    cursor = conn.cursor()
    cursor.execute("""
            SELECT username, {0}_{1}
            FROM '{2}'
            ORDER BY {0}_{1} DESC LIMIT {3};            
            """.format(duration, msg_type, 'chat_' + str(cid)[1:] + '_users_info', limit))
    data = cursor.fetchall()
    # 'chat_' + str(cid)[1:] + '_users_info'
    return data


def db_service_get_warn_automute_time(cid):
    global conn
    cursor = conn.cursor()
    cursor.execute(
        """SELECT warn_automute_time
        FROM chats_parameters
        WHERE cid = '{0}'""".format(str(cid)[1:]))
    data = cursor.fetchone()[0]
    return data


def db_service_get_antibot_welcome_messages(cid):
    global conn
    cursor = conn.cursor()
    cursor.execute("""
    SELECT cid, welcome_msg_default, welcome_msg_approved, welcome_msg_returning
    FROM chats_parameters
    WHERE cid = '{0}'
    """.format(str(cid)[1:]))
    data = cursor.fetchone()
    if data is not None:
        return [data[0], str(data[1]), str(data[2]), str(data[3])]
    else:
        return False


def db_mod_set_antibot_welcome_messages(cid, rm=False,
                                        welcome_msg_default='Добро пожаловать в чат, {name}',
                                        welcome_msg_approved='Спасибо, проверка пройдена!',
                                        welcome_msg_returning='С возвращением, {name}!'):
    global conn
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cid, welcome_msg_default, welcome_msg_approved, welcome_msg_returning
        FROM chats_parameters
        WHERE cid = '{0}'
        """.format(str(cid)[1:]))
    data = cursor.fetchone()
    if not rm:
        cursor.execute("""
        UPDATE chats_parameters 
        SET welcome_msg_default='{1}',
        welcome_msg_approved='{2}',
        welcome_msg_returning='{3}'
        WHERE cid = '{0}'
        """.format(str(cid)[1:], welcome_msg_default, welcome_msg_approved, welcome_msg_returning))
        conn.commit()
    else:
        cursor.execute("""
                    UPDATE chats_parameters 
                    SET welcome_msg_default='',
                    welcome_msg_approved='',
                    welcome_msg_returning=''
                    WHERE cid = '{0}'
                    """.format(str(cid)[1:]))
        conn.commit()


def db_service_add_bot_message(cid, message):
    global conn
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO bot_messages VALUES ('{0}', '{1}', '{2}')
    """.format(cid, int(time.time()), message.message_id))
    conn.commit()


def db_service_get_old_bot_messages(bot_message_swelling_time):
    global conn
    cursor = conn.cursor()
    time_diff = int(time.time()) - bot_message_swelling_time
    cursor.execute(
        """SELECT ROWID, cid, mid FROM bot_messages WHERE date < '{0}'""".format(time_diff))
    data = cursor.fetchall()
    if data is not None:
        return data
    else:
        return False


def db_service_delete_old_bot_message(rowid):
    global conn
    cursor = conn.cursor()
    cursor.execute(
        """DELETE FROM bot_messages
                WHERE ROWID = {0}""".format(rowid))
    conn.commit()


def add_mid_column_into_bot_messages_once():
    global conn
    cursor = conn.cursor()
    cursor.execute("""
    ALTER TABLE bot_messages ADD COLUMN mid integer
    """)
    conn.commit()
    return 'Created'


#########################################################################################

def db_service_add_chat_forward():
    pass

# def db_service_get_user_id_by_username(cid, username):
#     global conn
#     cursor = conn.cursor()
#     table_for_use = 'chat_' + str(cid)[1:]
#     sql = """
#         SELECT uid
#         FROM '{0}'
#         WHERE username = '{1}'
#         """.format(table_for_use, username)
#     cursor.execute(sql)
#     data = cursor.fetchone()
#
#     if data is not None:
#         return data[0]
#     else:
#         return False


###################
#
# def db_tech_get_all_old_chat_tables_list():
#     global conn
#     cursor = conn.cursor()
#     cursor.execute("""SELECT name FROM sqlite_master WHERE type='table'""")
#     data = cursor.fetchall()
#
#     table_list = []
#     for table in data:
#         if ('chat_' in table[0]) and not ('users_info' in table[0]):
#             table_list += table
#     return table_list


# def db_transfer(cid):
#     global conn
#     cursor = conn.cursor()
#     print('chat_' + cid + ' > ' + 'chat_' + cid + '_users_info started')
#     cursor.execute("""
#     SELECT * FROM {0}""".format('chat_' + cid))
#     data = cursor.fetchall()
#     old_format_data = data
#     for foo in old_format_data:
#         uid = foo[0]
#         date_added = foo[2]
#         message_count = foo[3]
#         warn_count = foo[4]
#         weekly_message_count = foo[15]
#         if uid == var_config.master_id:
#             new_rights = 11111111
#         else:
#             new_rights = int(
#                 str(foo[8]) + str(foo[10]) + str(foo[11]) + str(foo[12]) + str(foo[13]) + str(foo[14]) + '0' + '0')
#         # actions, warn, mute, ban, pin, chmod, resync, set_antibot
#         db_stat_add_new_user('-' + cid, foo[0], foo[1])
#         cursor.execute("""
#         UPDATE chat_{0}_users_info
#         SET
#         added = '{1}',
#         rights = '{2}',
#         a_msg = '{3}',
#         w_msg = '{4}',
#         m_msg = '{4}',
#         warn_count = '{5}'
#         WHERE uid = '{6}'
#         """.format(cid, date_added, new_rights, message_count, weekly_message_count, warn_count, uid))
#     print('chat_' + cid + ' > ' + 'chat_' + cid + ' users_info processed')
#     cursor.execute("""DROP TABLE chat_{0}""".format(cid))
#     print('chat_' + cid + ' dropped')
#     conn.commit()
#
#
# def db_drop_tech():
#     global conn
#     cursor = conn.cursor()
#     cursor.execute("""DROP TABLE tech_message_count_reset_date""")
#     conn.commit()
