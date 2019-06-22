#!/usr/bin/python
# coding=utf-8

# -1001060563829 GG&G
restricted_chats_for_links = [-1001060563829]
# -1001080419111 SGClub
restricted_chats_for_echo_all = [-1001080419111]
chats_for_echo_all = [1001254199480, 1001394778416, 1001444879250, 1001457973105, 1001060563829, 1001295499832,
                      1001328989582, 1001032838103, 1001245949155]
master_id = 24978372
bot_message_swelling_time = 90


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
