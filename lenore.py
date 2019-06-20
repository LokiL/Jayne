#!/usr/bin/python
# coding=utf-8
import os
import re
import signal
import sys
import time
from datetime import datetime

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

import db_func
import var_config

if len(sys.argv) < 2:
    print("Usage:")
    print("  lenore.py <bot_token> [</path/to/db.sqlite>]")
    exit(1)

if len(sys.argv) >= 3:
    db_func.db_service_database_path(sys.argv[2])
    db_func.db_service_database_conn_open()
    db_func.db_service_init_tech_tables()

###
### Переменные
###
bot_token = sys.argv[1]  # Lenore token
lenore = telebot.TeleBot(bot_token)

if db_func.db_service_check_restart_trigger_table_exists():
    if db_func.db_service_get_restart_trigger()[0] == 1:
        cid = db_func.db_service_get_restart_trigger()[1]
        mid = db_func.db_service_get_restart_trigger()[2]
        lenore.send_message(cid, 'Синхронизация завершена. Новый код успешно запущен.')
        db_func.db_service_restart_daemon_trigger(cid, mid)


def service_init_table_for_chat(cid, uid, username):
    if not db_func.db_service_check_chat_table_exists(cid):
        db_func.db_service_create_chat_table(cid)
        db_func.db_stat_add_new_user(cid, uid, username)
        db_func.db_mod_set_chmod_for_user(cid, uid, 11111111)
        lenore.send_message(cid, 'Таблица {0} создана успешно.\n'
                                 '{1} получил полный доступ к функциям бота.\n'
                                 'Для успешного функционирования мне нужны права:\n'
                                 '- удаление сообщений;\n'
                                 '- бан пользователей;\n'
                                 '- пин сообщений.\n'
                                 'Если их не будет - я буду постоянно сыпать ошибками :('.format(
            'chat_' + str(cid)[1:] + '_users', username))

    else:
        lenore.send_message(cid, 'О, а этот чатик я знаю!'.format())


###
### Сервисные проверки
###
def check_user_is_admin(user_id, chat_id):
    """
    :param user_id:
    :param chat_id:
    :return:
    :rtype: Bool
    """
    foo = lenore.get_chat_administrators(chat_id)
    current_chat_administrators = []
    for user in foo:
        tmp = user.user.id
        current_chat_administrators.append(tmp)
    if user_id not in current_chat_administrators:
        return False
    else:
        return True


def info_get_current_username(chat_id, user_id):
    foo = lenore.get_chat_member(chat_id, user_id).user
    if foo.username is not None:
        bar = '@' + foo.username
    else:
        try:
            bar = foo.first_name
        except:
            bar = foo.id
    return bar


###
### Обработка новых пользователей
###
@lenore.message_handler(content_types=["new_chat_members"])
def processing_anti_bot(message):
    try:
        cid = message.chat.id
        bot_id = lenore.get_me()
        if bot_id.id == message.new_chat_member.id:
            service_init_table_for_chat(cid, message.from_user.id, message.from_user.first_name)
        else:
            incoming_user_name = info_get_current_username(cid, message.new_chat_member.id)
            foo = db_func.db_service_get_antibot_welcome_messages(cid)
            if foo is not False:
                if db_func.db_service_check_user_exists(cid, message.new_chat_member.id):
                    db_func.db_stat_update_user_last_return(cid, message.new_chat_member.id)
                    welcome_message = foo[3].format(name=incoming_user_name, lb='\n')
                    lenore.send_message(cid, welcome_message)
                else:
                    welcome_message = foo[1].format(name=incoming_user_name, lb='\n')
                    lenore.restrict_chat_member(cid, message.new_chat_member.id, int(time.time()), False,
                                                False,
                                                False, False)
                    approve_data = str(message.new_chat_member.id)
                    antibot_markup = InlineKeyboardMarkup()
                    antibot_markup.add(InlineKeyboardButton("🦐", callback_data=approve_data))
                    lenore.send_message(cid, welcome_message, reply_markup=antibot_markup)
    except Exception as e:
        lenore.send_message(message.chat.id, e)


###
### Обрабатываем /rate
###
# noinspection PyShadowingNames
@lenore.message_handler(content_types=['photo'])
def all_rate_photo(message):
    try:
        uid = message.from_user.id
        cid = message.chat.id
        username = info_get_current_username(cid, uid)
        if db_func.db_service_check_user_exists(cid, uid):
            db_func.db_stat_update_user_message_count(cid, uid)
            db_func.db_stat_update_user_message_count(cid, uid, 'photos')
        else:
            db_func.db_stat_add_new_user(cid, uid, username)
            db_func.db_stat_update_user_message_count(cid, uid)
        if not db_func.db_service_check_user_have_rights(cid, uid, 'actions'):
            lenore.reply_to(message, "I'm sorry Dave, I'm afraid I can't do that.")
        else:
            if message.caption == '/rate':
                lenore.delete_message(cid, message.message_id)
                file_info = lenore.get_file(message.photo[len(message.photo) - 1].file_id)
                rate_markup = InlineKeyboardMarkup()
                rate_markup.row_width = 1
                callback_upvote = 'upvote_photo_{0}_{1}'.format(0, 0)
                callback_downvote = 'downvote_photo_{0}_{1}'.format(0, 0)
                rate_markup.add(InlineKeyboardButton("0 👍", callback_data=callback_upvote),
                                InlineKeyboardButton("0 👎", callback_data=callback_downvote))
                photo_caption = '{0} запостил фото на оценку!✨'.format(username)
                lenore.send_photo(cid, file_info.file_id, caption=photo_caption, reply_markup=rate_markup)
    except Exception as e:
        lenore.send_message(message.chat.id, e)


@lenore.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        # noinspection PyShadowingNames
        cid = call.message.chat.id
        mid = call.message.message_id
        clicking_user = str(call.from_user.id)
        if call.data == clicking_user:
            foo = db_func.db_service_get_antibot_welcome_messages(cid)
            if foo is not False:
                welcome_message = foo[2].format(name=call.from_user.first_name, lb='\n')
                lenore.edit_message_text(welcome_message, call.message.chat.id, mid)
            lenore.answer_callback_query(callback_query_id=call.id, show_alert=True, text="Верификация пройдена")
            incoming_user_name = info_get_current_username(cid, call.from_user.id)
            db_func.db_stat_add_new_user(cid, call.from_user.id, incoming_user_name)
            lenore.restrict_chat_member(call.message.chat.id, call.from_user.id, int(time.time()), True, True, True,
                                        True)

        splitted_call = call.data.split('_')
        if splitted_call[0] == 'upvote' or splitted_call[0] == 'downvote':
            mid = call.message.message_id
            cid = call.message.chat.id
            uid = call.from_user.id
            username = info_get_current_username(cid, uid)
            if not db_func.db_service_check_user_exists(cid, uid):
                db_func.db_stat_add_new_user(cid, uid, username)

            upvote = int(splitted_call[2])
            downvote = int(splitted_call[3])

            photo_author = call.message.caption.split(' ')[0]

            list_of_voted_users = call.message.caption.split('✨')

            currently_voting_user = info_get_current_username(cid, uid)
            voted_users = list_of_voted_users[1]
            if currently_voting_user not in voted_users:
                if splitted_call[0] == 'upvote':
                    upvoted_rate_markup = InlineKeyboardMarkup()
                    upvoted_rate_markup.row_width = 1
                    callback_upvote = 'upvote_photo_{0}_{1}'.format(str(upvote + 1), downvote)
                    upvote_caption = "{0} 👍".format(upvote + 1)

                    callback_downvote = 'downvote_photo_{0}_{1}'.format(str(upvote + 1), downvote)
                    downvote_caption = "{0} 👎".format(downvote)

                    if len(voted_users) > 0:
                        voted_users += ', ' + currently_voting_user
                    else:
                        voted_users += 'Проголосовали: ' + currently_voting_user

                    upvoted_rate_markup.add(
                        InlineKeyboardButton(upvote_caption, callback_data=callback_upvote),
                        InlineKeyboardButton(downvote_caption, callback_data=callback_downvote))
                    lenore.edit_message_caption(
                        '{0} запостил фото на оценку!✨ {1}'.format(photo_author, voted_users),
                        call.message.chat.id, call.message.message_id)
                    lenore.edit_message_reply_markup(call.message.chat.id, mid, reply_markup=upvoted_rate_markup)
                    lenore.answer_callback_query(callback_query_id=call.id, show_alert=False, text="Upvoted")

                elif splitted_call[0] == 'downvote':
                    downvoted_rate_markup = InlineKeyboardMarkup()
                    downvoted_rate_markup.row_width = 1
                    callback_upvote = 'upvote_photo_{0}_{1}'.format(upvote, str(downvote + 1))
                    upvote_caption = "{0} 👍".format(upvote)

                    callback_downvote = 'downvote_photo_{0}_{1}'.format(upvote, str(downvote + 1))
                    downvote_caption = "{0} 👎".format(downvote + 1)

                    if len(voted_users) > 0:
                        voted_users += ', ' + currently_voting_user
                    else:
                        voted_users += 'Проголосовали: ' + currently_voting_user

                    downvoted_rate_markup.add(
                        InlineKeyboardButton(upvote_caption, callback_data=callback_upvote),
                        InlineKeyboardButton(downvote_caption, callback_data=callback_downvote))

                    lenore.edit_message_caption(
                        '{0} запостил фото на оценку!✨ {1}'.format(photo_author, voted_users),
                        call.message.chat.id, call.message.message_id)
                    lenore.edit_message_reply_markup(call.message.chat.id, mid, reply_markup=downvoted_rate_markup)
                    lenore.answer_callback_query(callback_query_id=call.id, show_alert=False, text="Downvoted")
            else:
                lenore.answer_callback_query(callback_query_id=call.id, show_alert=False, text="Ты уже проголосовал!")
    except Exception as e:
        lenore.send_message(call.chat.id, e)


###
### Команды на действия, доступные всем
###

@lenore.message_handler(commands=['userinfo'])
def all_userinfo(message):
    try:
        cid = message.chat.id
        if message.reply_to_message is None:
            uid = message.from_user.id
        else:
            uid = message.reply_to_message.from_user.id
        if not db_func.db_service_check_user_exists(cid, uid):
            db_func.db_stat_add_new_user(cid, uid, info_get_current_username(cid, uid))

        if not db_func.db_service_check_user_have_rights(cid, uid, 'actions'):
            lenore.reply_to(message, "I'm sorry Dave, I'm afraid I can't do that.")
        else:
            db_func.db_stat_update_user_command_count(cid, message.from_user.id, 'userinfo')
            user_rights_readable = []
            for r in db_func.db_service_get_all_rights_for_user(cid, uid):
                if r == 1:
                    user_rights_readable.append('✅')
                else:
                    user_rights_readable.append('❌')
            userinfo_msg = "Пользователь `{0}`:\n" \
                           "Количество сообщений: \n" \
                           "- всего: `{1}`\n" \
                           "- за месяц: `{2}`\n" \
                           "- за неделю: `{3}`\n" \
                           "- за день: `{4}`\n" \
                           "Количество предупреждений: `{5}`\n" \
                           "Последнее предупреждение: `{6}`\n" \
                           "Доступ к командам бота: \n" \
                           "`{7} - общие действия;`\n" \
                           "`{8} - варны;`\n" \
                           "`{9} - муты;`\n" \
                           "`{10} - баны;`\n" \
                           "`{11} - пины;`\n" \
                           "`{12} - изменение доступов;`\n" \
                           "`{13} - перезагрузка бота;`\n" \
                           "`{14} - управление антиботом`".format(
                info_get_current_username(cid, uid),
                db_func.db_stat_get_message_count_for_user(cid, uid)[0],
                db_func.db_stat_get_message_count_for_user(cid, uid)[1],
                db_func.db_stat_get_message_count_for_user(cid, uid)[2],
                db_func.db_stat_get_message_count_for_user(cid, uid)[3],
                db_func.db_mod_get_current_warn_info_for_user(cid, uid)[0][0],
                db_func.db_mod_get_current_warn_info_for_user(cid, uid)[1],
                user_rights_readable[0],
                user_rights_readable[1],
                user_rights_readable[2],
                user_rights_readable[3],
                user_rights_readable[4],
                user_rights_readable[5],
                user_rights_readable[6],
                user_rights_readable[7])
            lenore.reply_to(message, userinfo_msg, parse_mode='Markdown')
    except Exception as e:
        lenore.send_message(message.chat.id, e)


@lenore.message_handler(commands=['slap'])
def all_slap(message):
    try:
        cid = message.chat.id
        uid = message.from_user.id
        if not db_func.db_service_check_user_exists(cid, uid):
            db_func.db_stat_add_new_user(cid, uid, info_get_current_username(cid, uid))

        if not db_func.db_service_check_user_have_rights(cid, uid, 'actions'):
            lenore.reply_to(message, "I'm sorry Dave, I'm afraid I can't do that.")
        else:
            db_func.db_stat_update_user_command_count(cid, uid, 'slap')
            spl = message.text.split(' ')
            lenore.delete_message(cid, message.message_id)
            user_from = info_get_current_username(cid, uid)
            msg_text = ''
            if len(spl) == 1:
                msg_text += user_from + ' slaps himself around a bit with a large trout'
                lenore.send_message(cid, msg_text)
            else:
                user_slapped = spl[1]
                msg_text += user_from + ' slaps ' + user_slapped + ' around a bit with a large trout'
                lenore.send_message(cid, msg_text)
    except Exception as e:
        lenore.send_message(message.chat.id, e)


@lenore.message_handler(commands=['me'])
def all_me_action(message):
    try:
        cid = message.chat.id
        uid = message.from_user.id
        if not db_func.db_service_check_user_exists(cid, uid):
            db_func.db_stat_add_new_user(cid, uid, info_get_current_username(cid, uid))

        if not db_func.db_service_check_user_have_rights(cid, uid, 'actions'):
            lenore.reply_to(message, "I'm sorry Dave, I'm afraid I can't do that.")
        else:
            db_func.db_stat_update_user_command_count(cid, uid, 'me')

            spl = message.text.split(' ')
            lenore.delete_message(cid, message.message_id)
            user_from = info_get_current_username(cid, uid)
            me_action_text = ''
            if len(spl) == 1:
                me_action_text += user_from + ' делает что-то подозрительное...'
                lenore.send_message(cid, me_action_text)
            else:
                user_action = ' '.join(spl[1:])
                me_action_text += user_from + ' ' + user_action
                lenore.send_message(cid, me_action_text)
    except Exception as e:
        lenore.send_message(message.chat.id, e)


@lenore.message_handler(commands=['topmsg'])
def all_topmsg(message):
    try:
        cid = message.chat.id
        uid = message.from_user.id
        if not db_func.db_service_check_user_exists(cid, uid):
            db_func.db_stat_add_new_user(cid, uid, info_get_current_username(cid, uid))

        if not db_func.db_service_check_user_have_rights(cid, uid, 'actions'):
            lenore.reply_to(message, "I'm sorry Dave, I'm afraid I can't do that.")
        else:
            db_func.db_stat_update_user_command_count(cid, uid, 'topmsg')
            output = 'Топ-5 флудеров группы за все время:\n'
            for data in db_func.db_stat_get_top_flooders(cid):
                foo = "`{0}` - `{1}`\n".format(data[0], data[1])
                output += foo
            lenore.reply_to(message, output, parse_mode='Markdown')

    except Exception as e:
        lenore.send_message(message.chat.id, e)


@lenore.message_handler(commands=['topweeklymsg'])
def all_topweeklymsg(message):
    try:
        cid = message.chat.id
        uid = message.from_user.id
        if not db_func.db_service_check_user_exists(cid, uid):
            db_func.db_stat_add_new_user(cid, uid, info_get_current_username(cid, uid))
        if not db_func.db_service_check_user_have_rights(cid, uid, 'actions'):
            lenore.reply_to(message, "I'm sorry Dave, I'm afraid I can't do that.")
        else:
            db_func.db_stat_update_user_command_count(cid, uid, 'topweeklymsg')
            output = 'Топ-5 флудеров группы за неделю:\n'
            for data in db_func.db_stat_get_top_flooders(cid, duration='w'):
                foo = "`{0}` - `{1}`\n".format(data[0], data[1])
                output += foo
            lenore.reply_to(message, output, parse_mode='Markdown')

    except Exception as e:
        lenore.send_message(message.chat.id, e)


@lenore.message_handler(commands=['topdailymsg'])
def all_topdailymsg(message):
    try:
        cid = message.chat.id
        uid = message.from_user.id
        if not db_func.db_service_check_user_exists(cid, uid):
            db_func.db_stat_add_new_user(cid, uid, info_get_current_username(cid, uid))
        if not db_func.db_service_check_user_have_rights(cid, uid, 'actions'):
            lenore.reply_to(message, "I'm sorry Dave, I'm afraid I can't do that.")
        else:
            db_func.db_stat_update_user_command_count(cid, uid, 'topdailymsg')
            output = 'Топ-5 флудеров группы за день:\n'
            for data in db_func.db_stat_get_top_flooders(cid, duration='d'):
                foo = "`{0}` - `{1}`\n".format(data[0], data[1])
                output += foo
            lenore.reply_to(message, output, parse_mode='Markdown')
    except Exception as e:
        lenore.send_message(message.chat.id, e)


@lenore.message_handler(commands=['topmonthmsg'])
def all_topmonthmsg(message):
    try:
        cid = message.chat.id
        uid = message.from_user.id
        if not db_func.db_service_check_user_exists(cid, uid):
            db_func.db_stat_add_new_user(cid, uid, info_get_current_username(cid, uid))
        if not db_func.db_service_check_user_have_rights(cid, uid, 'actions'):
            lenore.reply_to(message, "I'm sorry Dave, I'm afraid I can't do that.")
        else:
            db_func.db_stat_update_user_command_count(cid, uid, 'topmonthmsg')
            output = 'Топ-5 флудеров группы за месяц:\n'
            for data in db_func.db_stat_get_top_flooders(cid, duration='m'):
                foo = "`{0}` - `{1}`\n".format(data[0], data[1])
                output += foo
            lenore.reply_to(message, output, parse_mode='Markdown')
    except Exception as e:
        lenore.send_message(message.chat.id, e)


@lenore.message_handler(commands=['report'])
def all_report(message):
    try:
        cid = message.chat.id  # ид чата
        uid = message.from_user.id  # ид отдающего команду
        if not db_func.db_service_check_user_exists(cid, uid):
            db_func.db_stat_add_new_user(cid, uid, info_get_current_username(cid, uid))
        if not db_func.db_service_check_user_have_rights(cid, uid, 'actions'):
            lenore.reply_to(message, "I'm sorry Dave, I'm afraid I can't do that.")
        else:
            if message.reply_to_message is None:
                lenore.reply_to(message, 'Команду возможно использовать только ответом на сообщение!')
            else:
                db_func.db_stat_update_user_command_count(cid, uid, 'report')
                ruid = message.reply_to_message.from_user.id  # id юзера, на сообщение которого реплаят
                rmid = message.reply_to_message.message_id  # id сообщения, на которое реплаят
                if message.chat.username is None:
                    chat_link = '(приватный чат, ссылка недоступна)'
                else:
                    chat_link = 't.me/' + message.chat.username

                if not var_config.service_get_chat_forwarding(cid):
                    lenore.reply_to(message.reply_to_message, '@niohisi, тут в чатике что-то не так!')

                else:
                    lenore.reply_to(message.reply_to_message, 'Сообщение передано модераторам.')
                    lenore.forward_message(var_config.service_get_chat_forwarding(cid), cid,
                                           rmid)
                    lenore.send_message(var_config.service_get_chat_forwarding(cid),
                                        '`{0}` жалуется на сообщение `{1}` в чате {2} ({3})'.format(
                                            info_get_current_username(cid, uid),
                                            info_get_current_username(cid, ruid),
                                            message.chat.title,
                                            chat_link), disable_web_page_preview=True, parse_mode='Markdown')

    except Exception as e:
        lenore.reply_to(message, e)


@lenore.message_handler(commands=['lenorehelp'])
def all_lenorehelp(message):
    welcome_text = """Команды бота:
/report - жалоба на сообщение (реплаем);
/userinfo - ответом на сообщение сообщает статистику для автора сообщения в текущем чате, при использовании без реплая - статистику использовавшего;
/me something - бот выводит сообщение вида @твой юзернейм something;
/slap кто-то - бот выводит сообщение "<твой ник> slaps <кто-то> around a bit with a large trout";
/topmsg - топ-5 флудеров за все время;
/topweeklymsg - топ-5 флудеров за неделю;
/topmonthlymsg - топ-5 флудеров за месяц;
/topdailymsg - топ-5 флудеров за день;
/rate - оценка фото, если написать это в комментарии к отправленному фото, только одно за раз;
/msk_fur - ссылка на чат "Пушистая Москва";
/afterdark - ссылка на afterdark-чат "Пушистой Москвы" (18+) (работает только из основного чата);
/furrygamers - cсылка на Furry gamers [RU] [18+];
/vapefur - ссылка на #Vaporspace (SFW) (RU);
/furcoding - ссылка на furry > /dev/null (чатик для русскоязычных фуррей-программистов);
/eww - гифка eww (реплаем или просто так), доступ на использование просить у админов;
/usuka - стикер "ъуъ съука" (реплаем или просто так), доступ на использование просить у админов;
/wtfisgoingon - мем с Макэвоем "Что происходит вообще" (реплаем или просто так), доступ на использование просить у админов"""

    try:
        cid = message.chat.id  # ид чата
        uid = message.from_user.id  # ид отдающего команду
        if not db_func.db_service_check_user_exists(cid, uid):
            db_func.db_stat_add_new_user(cid, uid, info_get_current_username(cid, uid))

        if not db_func.db_service_check_user_have_rights(cid, uid, 'actions'):
            lenore.reply_to(message, "I'm sorry Dave, I'm afraid I can't do that.")
        else:
            lenore.reply_to(message, welcome_text)
    except Exception as e:
        lenore.send_message(message.chat.id, e)


###
### Правила
###

@lenore.message_handler(commands=['rules'])
def link_rules_GG(message):
    try:
        if message.chat.id == -1001060563829:
            rules_text = """За нарушение правил участнику выдаётся предупреждение при помощи бота.
1. Мат, как способ оскорбления и (или) провокации в сторону всех или отдельных участников чата. Допускается употребление мата в качестве выражения эмоций, междометий и мат, не несущий оскорбительного подтекста. Сюда же входит запрет на обсуждение политики, наций и тем наркотиков или умышленного вреда здоровью. 
2. Просьба не злоупотреблять заглавными буквами, кои рассматриваются в переписках как крик.
3. Категорически запрещаются публикации порно в виде видео- и аудио- контента, а также изображения, содержащие половые органы. 
4. Никаких спойлеров или обсуждений главных сюжетных развитий игр, сериалов, фильмов и подобного контента, дабы не угасить чужой интерес и сохранить интригу. 
5. Запрещена реклама в любом виде. 
6. Никаких виртуальных секс-переписок и домогательств."""
            lenore.reply_to(message, rules_text)
        else:
            lenore.reply_to(message, "I'm sorry Dave, I'm afraid I can't do that.")
    except Exception as e:
        lenore.send_message(message.chat.id, e)


###
### Линки на чатики
###
@lenore.message_handler(commands=['afterdark'])
def link_afterdark(message):
    try:
        if message.chat.id not in var_config.restricted_chats_for_links:
            available_chats = [-1001457973105, -1001444879250]
            if message.chat.id in available_chats:
                lenore.reply_to(message, 'Ссылка на afterdark-чат Пушистой Москвы. Внимание, чат 18+!: \n'
                                         'https://t.me/joinchat/AX0jxAwS6vipAuCUL0ickw')
            else:
                lenore.reply_to(message, 'Прошу прощения, запрос этой ссылки работает только из основного чата ПМ')
        else:
            lenore.reply_to(message, "I'm sorry Dave, I'm afraid I can't do that.")
    except Exception as e:
        lenore.send_message(message.chat.id, e)


@lenore.message_handler(commands=['furrygamers'])
def link_furrygamers(message):
    try:
        if message.chat.id not in var_config.restricted_chats_for_links:
            lenore.reply_to(message, 'Ссылка на Furry gamers [RU] [18+]: \n'
                                     'https://t.me/FurryGS')
        else:
            lenore.reply_to(message, "I'm sorry Dave, I'm afraid I can't do that.")
    except Exception as e:
        lenore.send_message(message.chat.id, e)


@lenore.message_handler(commands=['msk_fur'])
def link_msk_fur(message):
    try:
        if message.chat.id not in var_config.restricted_chats_for_links:
            lenore.reply_to(message, 'Ссылка на чат "Пушистая Москва": \n'
                                     'https://t.me/msk_fur')
        else:
            lenore.reply_to(message, "I'm sorry Dave, I'm afraid I can't do that.")
    except Exception as e:
        lenore.send_message(message.chat.id, e)


@lenore.message_handler(commands=['vapefur'])
def link_vapefur(message):
    try:
        if message.chat.id not in var_config.restricted_chats_for_links:
            lenore.reply_to(message, 'Ссылка на #Vaporspace (SFW) (RU): \n'
                                     'https://t.me/vapefur')
        else:
            lenore.reply_to(message, "I'm sorry Dave, I'm afraid I can't do that.")
    except Exception as e:
        lenore.send_message(message.chat.id, e)


# furry > /dev/null
@lenore.message_handler(commands=['furcoding'])
def link_furrydevnull(message):
    try:
        if message.chat.id not in var_config.restricted_chats_for_links:
            lenore.reply_to(message, 'Ссылка на чат русскоязычных фуррей-программистов "furry > /dev/null": \n'
                                     'https://t.me/furrydevnull')
        else:
            lenore.reply_to(message, "I'm sorry Dave, I'm afraid I can't do that.")
    except Exception as e:
        lenore.send_message(message.chat.id, e)


@lenore.message_handler(commands=['eww'])
def all_eww(message):
    try:
        cid = message.chat.id  # ид чата
        uid = message.from_user.id  # ид отдающего команду
        if not db_func.db_service_check_user_exists(cid, uid):
            db_func.db_stat_add_new_user(cid, uid, info_get_current_username(cid, uid))
        if not db_func.db_service_check_user_have_rights(cid, uid, 'actions'):
            lenore.reply_to(message, "I'm sorry Dave, I'm afraid I can't do that.")
        else:
            db_func.db_stat_update_user_command_count(cid, uid, 'eww')
            dn = os.path.dirname(os.path.realpath(__file__))
            fn = os.path.join(dn, "eww.mp4")
            f = open(fn, 'rb')
            if message.reply_to_message is None:
                lenore.delete_message(cid, message.message_id)
                lenore.send_document(cid, f)
            else:
                lenore.delete_message(cid, message.message_id)
                lenore.send_document(cid, f, message.reply_to_message.message_id)
    except Exception as e:
        lenore.send_message(message.chat.id, e)


@lenore.message_handler(commands=['usuka'])
def all_usuka(message):
    try:
        cid = message.chat.id  # ид чата
        uid = message.from_user.id  # ид отдающего команду
        if not db_func.db_service_check_user_exists(cid, uid):
            db_func.db_stat_add_new_user(cid, uid, info_get_current_username(cid, uid))
        if not db_func.db_service_check_user_have_rights(cid, uid, 'actions'):
            lenore.reply_to(message, "I'm sorry Dave, I'm afraid I can't do that.")
        else:
            db_func.db_stat_update_user_command_count(cid, uid, 'usuka')
            dn = os.path.dirname(os.path.realpath(__file__))
            fn = os.path.join(dn, "usuka.webp")
            f = open(fn, 'rb')
            if message.reply_to_message is None:
                lenore.delete_message(cid, message.message_id)
                lenore.send_sticker(cid, f)
            else:
                lenore.delete_message(cid, message.message_id)
                lenore.send_sticker(cid, f, message.reply_to_message.message_id)
    except Exception as e:
        lenore.send_message(message.chat.id, e)


@lenore.message_handler(commands=['wtfisgoingon'])
def all_wtfisgoingon(message):
    try:
        cid = message.chat.id  # ид чата
        uid = message.from_user.id  # ид отдающего команду
        if not db_func.db_service_check_user_exists(cid, uid):
            db_func.db_stat_add_new_user(cid, uid, info_get_current_username(cid, uid))
        if not db_func.db_service_check_user_have_rights(cid, uid, 'actions'):
            lenore.reply_to(message, "I'm sorry Dave, I'm afraid I can't do that.")
        else:
            db_func.db_stat_update_user_command_count(cid, uid, 'wtfisgoingon')
            dn = os.path.dirname(os.path.realpath(__file__))
            fn = os.path.join(dn, "wtfisgoingon.jpg")
            f = open(fn, 'rb')
            if message.reply_to_message is None:
                lenore.delete_message(cid, message.message_id)
                lenore.send_photo(cid, f, caption='')
            else:
                lenore.delete_message(cid, message.message_id)
                lenore.send_photo(cid, f, caption='', reply_to_message_id=message.reply_to_message.message_id)

    except Exception as e:
        lenore.send_message(message.chat.id, e)


@lenore.message_handler(commands=['badumtss'])
def mod_badumtss(message):
    try:
        cid = message.chat.id  # ид чата
        uid = message.from_user.id  # ид отдающего команду
        if not db_func.db_service_check_user_exists(cid, uid):
            db_func.db_stat_add_new_user(cid, uid, info_get_current_username(cid, uid))
        if not db_func.db_service_check_user_have_rights(cid, uid, 'actions'):
            lenore.reply_to(message, "I'm sorry Dave, I'm afraid I can't do that.")
        else:
            db_func.db_stat_update_user_command_count(cid, uid, 'badumtss')
            dn = os.path.dirname(os.path.realpath(__file__))
            fn = os.path.join(dn, "badumtss.png")
            f = open(fn, 'rb')
            if message.reply_to_message is None:
                lenore.delete_message(cid, message.message_id)
                lenore.send_sticker(cid, f)
            else:
                lenore.delete_message(cid, message.message_id)
                lenore.send_sticker(cid, f, message.reply_to_message.message_id)
    except Exception as e:
        lenore.send_message(message.chat.id, e)


###
### Модераторские команды
###


@lenore.message_handler(commands=['warn'])
def mod_warn(message):
    try:
        cid = message.chat.id  # ид чата
        uid = message.from_user.id  # ид отдающего команду
        if not db_func.db_service_check_user_exists(cid, uid):
            db_func.db_stat_add_new_user(cid, uid, info_get_current_username(cid, uid))
        if not db_func.db_service_check_user_have_rights(cid, uid, 'warn'):
            lenore.reply_to(message, "I'm sorry Dave, I'm afraid I can't do that.")
        else:
            if message.reply_to_message is None:
                lenore.reply_to(message, 'Команду возможно использовать только ответом на сообщение!')
            else:
                ruid = message.reply_to_message.from_user.id  # id юзера, на сообщение которого реплаят
                rmid = message.reply_to_message.message_id  # id сообщения, на которое реплаят
                if check_user_is_admin(ruid, cid):
                    lenore.reply_to(message, "I'm sorry Dave, I'm afraid I can't do that.")
                else:
                    spl = str(message.text).split(' ')
                    if len(spl) == 1:
                        lenore.reply_to(message, 'Неверный синтаксис команды, бака!\nПравильно: /warn [причина]')
                    else:
                        db_func.db_stat_update_user_command_count(cid, uid, 'warn')
                        reason = ' '.join(spl[1:])
                        warned_user_naming = info_get_current_username(cid, ruid)
                        if message.chat.username is None:
                            chat_link = '(приватный чат, ссылка недоступна)'
                        else:
                            chat_link = 't.me/' + message.chat.username
                        if not db_func.db_service_check_user_exists(cid, ruid):
                            db_func.db_stat_add_new_user(cid, ruid, warned_user_naming)
                        current_warn_count = db_func.db_mod_increase_warn_count_for_user(cid, ruid, uid, reason)
                        warn_message = "{0}, предупреждение!\nПричина: {1}\n" \
                                       "Текущее количество предупреждений: {2}".format(
                            warned_user_naming, reason, current_warn_count)
                        info_message_text = "`{0}` выдал варн пользователю {1} в чате {2} ({3})\n" \
                                            "Причина: {4}\nТекущее количество предупреждений: {5}".format(
                            info_get_current_username(cid, uid),
                            warned_user_naming,
                            message.chat.title,
                            chat_link, reason, current_warn_count)
                        if not var_config.service_get_chat_forwarding(cid):
                            lenore.reply_to(message.reply_to_message, warn_message)
                        else:
                            lenore.reply_to(message.reply_to_message, warn_message)
                            lenore.forward_message(var_config.service_get_chat_forwarding(cid), cid, rmid)
                            lenore.send_message(var_config.service_get_chat_forwarding(cid), info_message_text,
                                                disable_web_page_preview=True, parse_mode='Markdown')
    except Exception as e:
        lenore.reply_to(message, e)


@lenore.message_handler(commands=['chmod'])
def mod_chmod(message):
    # all_actions_allowed, limited_actions_allowed, warn_func, mute_func, ban_func, pin_func, can_change_rights
    try:
        cid = message.chat.id  # ид чата
        uid = message.from_user.id  # ид отдающего команду
        mid = message.message_id  # id сообщения с командой
        if not db_func.db_service_check_user_exists(cid, uid):
            db_func.db_stat_add_new_user(cid, uid, info_get_current_username(cid, uid))
        if not check_user_is_admin(uid, cid):
            lenore.delete_message(cid, mid)
        else:
            if message.reply_to_message is None:
                lenore.reply_to(message,
                                "I'm sorry Dave, I'm afraid I can't do that.\nКоманда должна быть дана реплаем")
            else:
                if not db_func.db_service_check_user_have_rights(cid, uid, 'chmod'):
                    lenore.reply_to(message,
                                    "I'm sorry Dave, I'm afraid I can't do that.\nУ тебя нет доступа на изменение прав.")
                else:
                    command = str(message.text).split(' ')
                    if not re.match(r'[01]{8}\Z', command[1]):
                        lenore.reply_to(message,
                                        "I'm sorry Dave, I'm afraid I can't do that.\nНекорректный синтаксис. /chmod [nnnnnnnn], где n=0 или 1")
                    else:
                        db_func.db_stat_update_user_command_count(cid, uid, 'chmod')
                        ruid = message.reply_to_message.from_user.id  # id юзера, на сообщение которого реплаят
                        if not db_func.db_service_check_user_exists(cid, ruid):
                            db_func.db_stat_add_new_user(cid, ruid, info_get_current_username(cid, ruid))
                        user_rights_readable_old = []
                        for r in db_func.db_service_get_all_rights_for_user(cid, ruid):
                            if r == 1:
                                user_rights_readable_old.append('✅')
                            else:
                                user_rights_readable_old.append('❌')
                        db_func.db_mod_set_chmod_for_user(cid, ruid, command[1])
                        user_rights_readable_new = []
                        for r in db_func.db_service_get_all_rights_for_user(cid, ruid):
                            if r == 1:
                                user_rights_readable_new.append('✅')
                            else:
                                user_rights_readable_new.append('❌')
                        lenore.reply_to(message, "Права успешно изменены для {0}:\n" \
                                                 "{1} > {2} - общие действия\n" \
                                                 "{3} > {4} - варны\n" \
                                                 "{5} > {6} - муты\n" \
                                                 "{7} > {8} - баны\n" \
                                                 "{9} > {10} - пины\n" \
                                                 "{11} > {12} - изменение доступов\n" \
                                                 "{13} > {14} - перезапуск бота\n"
                                                 "{15} > {16} - управление антиботом".format(
                            info_get_current_username(cid, ruid),
                            user_rights_readable_old[0], user_rights_readable_new[0],
                            user_rights_readable_old[1], user_rights_readable_new[1],
                            user_rights_readable_old[2], user_rights_readable_new[2],
                            user_rights_readable_old[3], user_rights_readable_new[3],
                            user_rights_readable_old[4], user_rights_readable_new[4],
                            user_rights_readable_old[5], user_rights_readable_new[5],
                            user_rights_readable_old[6], user_rights_readable_new[6],
                            user_rights_readable_old[7], user_rights_readable_new[7]))
    except Exception as e:
        lenore.reply_to(message, e)


@lenore.message_handler(commands=['set_antibot'])
def mod_set_antibot(message):
    try:
        cid = message.chat.id  # ид чата
        uid = message.from_user.id  # ид отдающего команду
        mid = message.message_id  # id сообщения с командой
        if not db_func.db_service_check_user_exists(cid, uid):
            db_func.db_stat_add_new_user(cid, uid, info_get_current_username(cid, uid))
        if not check_user_is_admin(uid, cid):
            lenore.reply_to(message, "I'm sorry Dave, I'm afraid I can't do that.")
        else:
            if not db_func.db_service_check_user_have_rights(cid, uid, 'set_antibot'):
                lenore.reply_to(message,
                                "I'm sorry Dave, I'm afraid I can't do that.\nУ тебя нет доступа на управление антиботом.")
            else:
                if message.text == '/set_antibot rm':
                    db_func.db_mod_set_antibot_welcome_messages(cid, rm=True)
                    lenore.reply_to(message, "Антибот успешно отключен")
                else:
                    spl_command = message.text.split(' ')
                    raw_welcomes = ' '.join(spl_command[1:])
                    clean_welcomes = raw_welcomes.split('|')
                    if len(clean_welcomes) != 3:
                        lenore.reply_to(message,
                                        "Неверный синтаксис: /set_antibot welcome_msg_default|welcome_msg_approved|welcome_msg_returning")
                    else:
                        db_func.db_mod_set_antibot_welcome_messages(cid,
                                                                    welcome_msg_default=clean_welcomes[0],
                                                                    welcome_msg_approved=clean_welcomes[1],
                                                                    welcome_msg_returning=clean_welcomes[2])
                        setted = db_func.db_service_get_antibot_welcome_messages(cid)
                        reply_text = "Антибот успешно включен.\n" \
                                     "Сообщение на нового пользователя: \n" \
                                     "`{0}`\n" \
                                     "Сообщение аппрува: \n" \
                                     "`{1}`\n" \
                                     "Сообщение для старого пользователя:\n" \
                                     "`{2}`".format(setted[1], setted[2], setted[3])
                        lenore.reply_to(message, reply_text, parse_mode='Markdown')


    except Exception as e:
        lenore.reply_to(message, e)


@lenore.message_handler(commands=['mute'])
def mod_mute(message):
    try:
        cid = message.chat.id  # ид чата
        uid = message.from_user.id  # ид отдающего команду
        if not db_func.db_service_check_user_exists(cid, uid):
            db_func.db_stat_add_new_user(cid, uid, info_get_current_username(cid, uid))
        if not db_func.db_service_check_user_have_rights(cid, uid, 'mute'):
            lenore.reply_to(message, "I'm sorry Dave, I'm afraid I can't do that.")
        else:
            if message.reply_to_message is None:
                lenore.reply_to(message, 'Команду возможно использовать только ответом на сообщение!')
            else:
                ruid = message.reply_to_message.from_user.id  # id юзера, на сообщение которого реплаят
                rmid = message.reply_to_message.message_id  # id сообщения, на которое реплаят
                if check_user_is_admin(ruid, cid):
                    lenore.reply_to(message, 'Невозможно наложить мут на того, кто сильнее меня, я простой бот. :(')
                else:
                    if not db_func.db_service_check_user_exists(cid, ruid):  # проверяем наличие цели молчанки
                        db_func.db_stat_add_new_user(cid, uid, info_get_current_username(cid, ruid))

                    command = str(message.text).split(' ')
                    if not re.match(r'((\d*\s)([dmh])(\s)(.*))', ' '.join(command[1:])):
                        lenore.reply_to(message, 'Неверный синтаксис команды, бака!\n'
                                                 'Правильно: /mute [time] [m/d/h] [причина]')
                    else:
                        db_func.db_stat_update_user_command_count(cid, uid, 'mute')
                        mute_time = 60
                        if command[2] == 'd':
                            mute_time = int(command[1]) * 86400
                        elif command[2] == 'h':
                            mute_time = int(command[1]) * 3600
                        elif command[2] == 'm':
                            mute_time = int(command[1]) * 60
                        mute_reason = ' '.join(command[3:])
                        mute_until = int(time.time()) + mute_time
                        lenore.restrict_chat_member(cid, ruid,
                                                    mute_until, False, False,
                                                    False, False)
                        db_func.db_mod_increase_mute_count_for_user(ruid, cid, mute_time, uid, mute_reason)

                        muted_user_naming = info_get_current_username(cid, ruid)
                        mute_ending_date = str(datetime.utcfromtimestamp(int(mute_until + 10800)).strftime(
                            '%Y-%m-%d %H:%M:%S'))
                        lenore.reply_to(message.reply_to_message, "Поздравляю, {0}! "
                                                                  "На тебя наложена молчанка до {1}\n"
                                                                  "Причина (если еще не понятно): {2}".format(
                            muted_user_naming,
                            mute_ending_date,
                            mute_reason))

                        if var_config.service_get_chat_forwarding(cid):
                            if message.chat.username is None:
                                chat_link = '(приватный чат, ссылка недоступна)'
                            else:
                                chat_link = 't.me/' + message.chat.username

                            forward_message_text = "`{0}` наложил молчанку на `{1}` до {2} в чате {3} ({4})\nПричина: {5}".format(
                                info_get_current_username(cid, uid),
                                muted_user_naming,
                                mute_ending_date,
                                message.chat.title,
                                chat_link,
                                mute_reason)

                            lenore.forward_message(var_config.service_get_chat_forwarding(cid), cid, rmid)
                            lenore.send_message(var_config.service_get_chat_forwarding(cid), forward_message_text,
                                                disable_web_page_preview=True, parse_mode='Markdown')
    except Exception as e:
        lenore.reply_to(message, e)


@lenore.message_handler(commands=['ban'])
def mod_ban(message):
    try:
        cid = message.chat.id  # ид чата
        uid = message.from_user.id  # ид отдающего команду
        mid = message.message_id  # id сообщения с командой
        rmid = message.reply_to_message.message_id  # id
        if not db_func.db_service_check_user_exists(cid, uid):
                db_func.db_stat_add_new_user(cid, uid, info_get_current_username(cid, uid))

        if not db_func.db_service_check_user_have_rights(cid, uid, 'ban'):
            lenore.reply_to(message, "I'm sorry Dave, I'm afraid I can't do that.")
        else:
            if message.reply_to_message is None:
                lenore.reply_to(message, "I'm sorry Dave, I'm afraid I can't do that.")
            else:
                ruid = message.reply_to_message.from_user.id
                if check_user_is_admin(ruid, cid):
                    lenore.reply_to(message, 'Админа нельзя забанить.')
                else:
                    command = str(message.text).split(' ')
                    kicked_user_naming = info_get_current_username(cid, ruid)
                    if not len(command) > 1:
                        lenore.reply_to(message, 'Необходимо указать причину бана!')
                    else:
                        kick_reason = ' '.join(command[1:])
                        lenore.kick_chat_member(cid, ruid)
                        db_func.db_stat_update_user_command_count(cid, uid, 'ban')
                        if not db_func.db_service_check_user_exists(cid, ruid):
                            db_func.db_stat_add_new_user(cid, ruid, kicked_user_naming)
                            db_func.db_mod_increase_ban_count_for_user(cid, ruid, uid, kick_reason)
                        else:
                            db_func.db_mod_increase_ban_count_for_user(cid, ruid, uid, kick_reason)

                        kick_text = """{0} был забанен. \nПричина бана: {1}""".format(kicked_user_naming,
                                                                                      kick_reason)
                        lenore.reply_to(message, kick_text)

                        if var_config.service_get_chat_forwarding(cid):
                            if message.chat.username is None:
                                chat_link = '(приватный чат, ссылка недоступна)'
                            else:
                                chat_link = 't.me/' + message.chat.username
                            forward_message_text = "`{0}` забанил `{1}` в чате {2} ({3})\nПричина: {4}".format(
                                info_get_current_username(cid, uid),
                                kicked_user_naming,
                                message.chat.title,
                                chat_link, kick_reason)
                            lenore.forward_message(var_config.service_get_chat_forwarding(cid), cid, rmid)
                            lenore.send_message(var_config.service_get_chat_forwarding(cid), forward_message_text,
                                                disable_web_page_preview=True, parse_mode='Markdown')
    except Exception as e:
        lenore.reply_to(message, e)


@lenore.message_handler(commands=['nullifywarn'])
def mod_nullify_warn(message):
    try:
        cid = message.chat.id
        uid = message.from_user.id  # ид отдающего команду
        if db_func.db_service_check_chat_table_exists(cid):
            if not db_func.db_service_check_user_exists(cid, uid):
                db_func.db_stat_add_new_user(cid, uid, info_get_current_username(cid, uid))
            if db_func.db_service_check_user_have_rights(cid, uid, 'warn'):
                if message.reply_to_message is None:
                    lenore.delete_message(cid, message.message_id)
                else:
                    ruid = message.reply_to_message.from_user.id  # получаем цель, которую варним

                    if check_user_is_admin(ruid, cid):  # проверяем цель на админа
                        lenore.delete_message(cid, message.message_id)
                    else:  # если не админ  # удаляем исходное сообщение
                        unwarned_user_naming = info_get_current_username(cid, ruid)  # получаем видимое имя пользователя

                        if message.chat.username is None:  # получаем ссылку на чат, чтобы использовать дальше
                            chat_link = '(приватный чат, ссылка недоступна)'
                        else:
                            chat_link = 't.me/' + message.chat.username

                        if db_func.db_service_check_chat_table_exists(cid):  # проверяем, есть ли чат в базе данных
                            if db_func.db_mod_get_current_warn_info_for_user(cid, ruid)[0][0] > 0:
                                if db_func.db_service_check_user_exists(cid,
                                                                        ruid):  # если есть - проверяем наличие юзера
                                    db_func.db_mod_nullify_warn_count_for_user(cid, ruid)  # стираем варны

                                    # сообщение для случая, если чат в базе
                                    nullify_message = 'Предупреждения сняты для {0}\n' \
                                                      'Текущее количество предупреждений: 0'.format(
                                        unwarned_user_naming)
                                    # сообщение для пересылки, если чат в базе
                                    info_message_text = '{0} снял все предупреждения для {1} в чате {2} ({3})'.format(
                                        info_get_current_username(cid, message.from_user.id),
                                        unwarned_user_naming,
                                        message.chat.title,
                                        chat_link)
                                    # если чата нет в списке на форвард, просто отправляем сообщение
                                    if not var_config.service_get_chat_forwarding(message.chat.id):
                                        lenore.reply_to(message, nullify_message)
                                    # если чат есть в списке на форвард - отправляем сообщение с анварном в чат и пересылаем куда надо
                                    else:
                                        lenore.reply_to(message, nullify_message)
                                        lenore.forward_message(var_config.service_get_chat_forwarding(message.chat.id),
                                                               message.chat.id,
                                                               message.reply_to_message.message_id)
                                        lenore.send_message(var_config.service_get_chat_forwarding(message.chat.id),
                                                            info_message_text)
                                else:
                                    lenore.reply_to(message,
                                                    'Юзер {0} в базе не зарегистрирован!'.format(
                                                        unwarned_user_naming))
                            else:
                                lenore.reply_to(message,
                                                'Мне интересно, как ты собираешься снимать варны у {0}, если их вообще-то нет?'.format(
                                                    unwarned_user_naming))

                        else:
                            lenore.send_message(cid,
                                                'Поскольку чат не в базе, варны не считаются и снять их невозможно.')
            else:
                lenore.reply_to(message, "I'm sorry Dave, I'm afraid I can't do that.")
    except Exception as e:
        lenore.reply_to(message, e)


@lenore.message_handler(commands=['removewarn'])
def mod_remove_warn(message):
    try:
        cid = message.chat.id
        uid = message.from_user.id  # ид отдающего команду
        if not db_func.db_service_check_user_exists(cid, uid):
            db_func.db_stat_add_new_user(cid, uid, info_get_current_username(cid, uid))

        if not db_func.db_service_check_user_have_rights(cid, uid, 'warn'):
            lenore.reply_to(message, "I'm sorry Dave, I'm afraid I can't do that.")
        else:
            if message.reply_to_message is None:
                lenore.reply_to(message, "I'm sorry Dave, I'm afraid I can't do that.")
            else:
                ruid = message.reply_to_message.from_user.id

                if check_user_is_admin(ruid, cid):
                    lenore.reply_to(message, "I'm sorry Dave, I'm afraid I can't do that.")
                else:
                    unwarned_user_naming = info_get_current_username(cid, ruid)

                    if not db_func.db_service_check_user_exists(cid, ruid):
                        db_func.db_stat_add_new_user(cid, ruid, info_get_current_username(cid, ruid))
                        lenore.reply_to(message, "Юзера не было в базе до этого момента, откуда у него варны?")
                    else:
                        if not db_func.db_mod_get_current_warn_info_for_user(cid, ruid)[0][0] > 0:
                            lenore.reply_to(message,
                                            'Мне интересно, как ты собираешься снимать варны у {0}, если их вообще-то нет?'.format(
                                                unwarned_user_naming))
                        else:
                            db_func.db_mod_remove_last_warn_for_user(cid, ruid)  # стираем варн
                            current_warn_count = db_func.db_mod_get_current_warn_info_for_user(cid, ruid)[0][0]
                            info_message = 'Предупреждение снято для {0}\n' \
                                           'Текущее количество предупреждений: {1}'.format(unwarned_user_naming,
                                                                                           current_warn_count)
                            if not var_config.service_get_chat_forwarding(cid):
                                lenore.reply_to(message, info_message)

                            else:

                                if message.chat.username is None:
                                    chat_link = '(приватный чат, ссылка недоступна)'
                                else:
                                    chat_link = 't.me/' + message.chat.username
                                forward_message_text = '{0} снял одно предупреждение {1} в чате {2} ({3})'.format(
                                    info_get_current_username(cid, message.from_user.id),
                                    unwarned_user_naming,
                                    message.chat.title,
                                    chat_link)
                                lenore.reply_to(message, info_message)
                                lenore.forward_message(var_config.service_get_chat_forwarding(cid), cid,
                                                       message.reply_to_message.message_id)
                                lenore.send_message(var_config.service_get_chat_forwarding(cid),
                                                    forward_message_text)
    except Exception as e:
        lenore.reply_to(message, e)


@lenore.message_handler(commands=['pin'])
def mod_pin(message):
    try:
        cid = message.chat.id
        uid = message.from_user.id  # ид отдающего команду
        if not db_func.db_service_check_user_exists(cid, uid):
            db_func.db_stat_add_new_user(cid, uid, info_get_current_username(cid, uid))
        if not db_func.db_service_check_user_have_rights(cid, uid, 'pin'):
            lenore.reply_to(message, "I'm sorry Dave, I'm afraid I can't do that.")
        else:
            if message.reply_to_message is None:
                lenore.delete_message(cid, message.message_id)
            else:
                ruid = message.reply_to_message.from_user.id
                if not db_func.db_service_check_user_exists(cid, ruid):
                    db_func.db_stat_add_new_user(cid, ruid, info_get_current_username(cid, ruid))
                lenore.delete_message(cid, message.message_id)
                lenore.pin_chat_message(cid, message.reply_to_message.message_id)
                db_func.db_stat_update_user_command_count(cid, uid, 'pin')

    except Exception as e:
        lenore.reply_to(message, e)


@lenore.message_handler(commands=['unpin'])
def mod_unpin(message):
    try:
        cid = message.chat.id
        uid = message.from_user.id  # ид отдающего команду
        if not db_func.db_service_check_user_exists(cid, uid):
            db_func.db_stat_add_new_user(cid, uid, info_get_current_username(cid, uid))

        if not db_func.db_service_check_user_have_rights(cid, uid, 'pin'):
            lenore.reply_to(message, "I'm sorry Dave, I'm afraid I can't do that.")
        else:
            lenore.delete_message(cid, message.message_id)
            lenore.unpin_chat_message(cid)

    except Exception as e:
        lenore.reply_to(message, e)


###
### Технические команды
###

@lenore.message_handler(commands=['resync'])
def tech_resync(message):
    try:
        cid = message.chat.id
        mid = message.message_id
        uid = message.from_user.id
        if not db_func.db_service_check_user_exists(cid, uid):
            db_func.db_stat_add_new_user(cid, uid, info_get_current_username(cid, uid))

        if not db_func.db_service_check_user_have_rights(cid, uid, 'resync'):
            lenore.reply_to(message, "I'm sorry Dave, I'm afraid I can't do that.")
        else:
            db_func.db_stat_update_user_command_count(cid, uid, 'resync')
            lenore.reply_to(message, 'Cинхронизация кода. Ожидайте пять секунд.')
            db_func.db_service_restart_daemon_trigger(cid, mid)
            db_func.db_service_database_conn_close()
            os.kill(os.getpid(), signal.SIGINT)
    except Exception as e:
        lenore.reply_to(message, e)


###
### UID и CID
###
@lenore.message_handler(commands=['get_tech'])
def tech_get_chat_info(message):
    try:
        cid = message.chat.id
        if message.from_user.id == var_config.master_id:
            if message.reply_to_message is None:
                uid = message.from_user.id
            else:
                uid = message.reply_to_message.from_user.id
            infostring = "UID: {0}\n CID: {1}\n".format(uid, cid)
            lenore.send_message(cid, infostring)
    except Exception as e:
        lenore.reply_to(message, e)



###
### Запуск таблицы для чата
###
# @lenore.message_handler(commands=['init'])
# def tech_init_table_for_chat(message):
#     # try:
#     cid = message.chat.id
#     uid = message.from_user.id
#     spl = str(message.text).split(' ')
#     if message.from_user.id == var_config.master_id:
#         table_name = 'chat_' + str(cid)[1:] + '_users'
#         if not db_func.db_service_check_chat_table_exists(cid):
#             db_func.db_service_create_chat_table(cid)
#             lenore.reply_to(message, 'Таблица {0} создана успешно.'.format(table_name))
#             if not db_func.db_service_check_user_exists(cid, uid):
#                 db_func.db_stat_add_new_user(cid, uid, info_get_current_username(cid, uid))
#             current_user_rights = db_func.db_service_get_all_rights_for_user(cid, uid)
#             db_func.db_mod_set_chmod_for_user(cid, uid, 11111111)
#             new_user_rights = db_func.db_service_get_all_rights_for_user(cid, uid)
#             lenore.reply_to(message, 'Права успешно изменены для {0}:\n'
#                                      'Было:  {1}\n'
#                                      'Стало: {2}'.format(info_get_current_username(cid, uid),
#                                                          current_user_rights,
#                                                          new_user_rights))
#         else:
#             lenore.reply_to(message, 'Таблица {0} уже существует'.format(table_name))


@lenore.message_handler(commands=['echo_all'])
def tech_echo_all(message):
    try:
        spl = str(message.text).split(' ')
        if message.from_user.id == var_config.master_id:
            text_message = ' '.join(spl[1:])
            for foo in db_func.db_tech_get_all_chat_tables_list():
                bar = str(foo).split('_')
                lenore.send_message(int('-' + bar[1]), text_message)
    except Exception as e:
        lenore.reply_to(message, e)


###
### Обработка войсов
###
@lenore.message_handler(content_types=['voice'])
def processing_detect_voice(message):
    try:
        if not lenore.get_chat_member(message.chat.id, lenore.get_me().id).can_delete_messages:
            pass
        else:
            cid = message.chat.id
            uid = message.from_user.id
            if not db_func.db_service_check_user_exists(cid, uid):
                db_func.db_stat_add_new_user(cid, uid, info_get_current_username(cid, uid))
            lenore.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        lenore.reply_to(message, e)


###
### Сбор статистики
###

@lenore.message_handler(content_types=['text'])
def processing_add_stat_info_to_db(message):
    try:
        uid = message.from_user.id
        cid = message.chat.id
        username = info_get_current_username(cid, uid)
        if not db_func.db_service_check_user_exists(cid, uid):
            db_func.db_stat_add_new_user(cid, uid, username)
            db_func.db_stat_update_user_message_count(cid, uid)
        else:
            db_func.db_stat_update_user_message_count(cid, uid)
            if lenore.get_chat_member(cid, uid).user.username is not None:
                current_username = '@' + lenore.get_chat_member(cid, uid).user.username
                if current_username != db_func.db_service_get_username_from_db(cid, uid):
                    db_func.db_service_update_username_for_user(cid, uid, current_username)
        db_func.db_service_reset_message_counters_for_users()
    except Exception as e:
        lenore.reply_to(message, e)


lenore.polling()
