#!/usr/bin/python
# coding=utf-8

# -1001060563829 GG&G
restricted_chats_for_links = [-1001060563829]
# -1001080419111 SGClub
restricted_chats_for_echo_all = [-1001080419111]
chats_for_echo_all = [1001254199480, # оргчат ПМ
                      1001394778416, # пм бот-чат
                      1001444879250, # furmoscow
                      1001457973105, # afterdark
                      1001060563829, # GG&G
                      1001295499832, # furdevnull
                      1001328989582, # furnsfw
                      1001032838103, # FG
                      1001245949155] # AOBC chat

#parameters
master_id = 24978372

bot_message_swelling_time = 90
#chat_fields_by_default
default_warn_swelling_time = 604800  # 604800 1 week
default_automute_time = 3600 # seconds
default_sticker_automute_limit = 3 # for 15s



# noinspection PyShadowingNames
def service_get_chat_forwarding(cid):
    chat_pairs = {}
    # -1001032838103 furrygamers
    # 'chat_1001394778416] пм бот-чат
    chat_pairs['-1001450465443'] = '-1001450465443'  # lenoretest
    chat_pairs['-1001444879250'] = '-1001394778416'  # furmoscow
    chat_pairs['-1001457973105'] = '-1001394778416'  # afterdark
    # -1001394778416 - ПМ-бот-чат
    # -1001254199480 - оргчат ПМ
    # -1001328989582 - https://t.me/furrychatnsfw
    # -1001295499832 - https://t.me/furrydevnull
    if chat_pairs.get(str(cid)) is not None:
        foo = chat_pairs.get(str(cid))
        return foo
    else:
        return False
