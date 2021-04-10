import vk_api
from vk_api.keyboard import *
from vk_api.bot_longpoll import *
import random
import sqlite3

USER_TOKEN = '6416756d35418d30555da42ca5ff711963f022b1' \
             'c52fcf7a586837630a7355f3ad0555ee82fe8c83b6eeb'
GROUP_TOKEN = '362ed726c14963a17c777db697e93fb0c371c60' \
              '71bd08be014138bfdef0bbcbbe2755016e25bda6143739'
GROUP_ID = 203487503
EXCEPTIONS = [545571708]


def back_keyb():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('Back', color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


def user(id, info, type='white'):
    if info['online'] == 0:
        online = 'No'
    else:
        online = 'Yes'
    if type == 'white':
        s = f"{info['first_name']} {info['last_name']}\nOnline: {online}"
    else:
        s = f"{info['first_name']} {info['last_name']}\nOnline: {online}\n"
    keyboard = VkKeyboard(one_time=False, inline=True)
    keyboard.add_openlink_button('Profile', f'https://vk.com/id{id}')
    keyboard.add_line()
    if type == 'white':
        keyboard.add_vkpay_button(hash=f"action=transfer-to-user&user_id={id}")
        keyboard.add_line()
    if type == 'white':
        keyboard.add_button(f'Downgrade', color=VkKeyboardColor.NEGATIVE, payload=f'{id}')
    else:
        keyboard.add_button(f'Unblock', color=VkKeyboardColor.POSITIVE, payload=f'{id}')
    return keyboard.get_keyboard(), s


def keyb(is_admin):
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('Write a review', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Offer an improvement', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_openlink_button('Go to the website', 'http://127.0.0.1:5000')
    if is_admin:
        keyboard.add_line()
        keyboard.add_button('Administration', color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


def admin_keyb():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('Administrators', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Blacklist', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('Back', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('Shut down', color=VkKeyboardColor.NEGATIVE)
    return keyboard.get_keyboard()


def list_keyb():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('All', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Add user', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button('Back', color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


def terminate():
    vk_user_session = vk_api.VkApi(token=USER_TOKEN)
    vk_user_session.method("status.set", {"text": "Bot status: Disabled", "group_id": GROUP_ID})
    exit()


vk_user_session = vk_api.VkApi(token=USER_TOKEN)
vk_group_session = vk_api.VkApi(token=GROUP_TOKEN)
vk = vk_group_session.get_api()
longpoll = VkBotLongPoll(vk_group_session, GROUP_ID)
admins = []
black = []
con = sqlite3.connect('../db/vkbot.db')
cur = con.cursor()
response = cur.execute('SELECT * FROM permissions').fetchall()
for elem in response:
    if elem[1] == 'TRUE':
        admins.append(elem[0])
    if elem[2] == 'TRUE':
        black.append(elem[0])

is_admin = False
admin_board = False
white_board = False
black_board = False
waiting_for_id = False
waiting_for_rev = False
waiting_for_imp = False
vk_user_session.method("status.set", {"text": "Bot status: Running", "group_id": GROUP_ID})
for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW and event.obj.message['from_id'] not in black:
        if event.obj.message['from_id'] in admins:
            is_admin = True
        else:
            is_admin = False
        if waiting_for_rev and not admin_board and not waiting_for_imp and event.obj.message[
            'text'] != 'Back':
            waiting_for_rev = False
            keyboard = keyb(is_admin)
            cur.execute(f"INSERT INTO reviews(vk_id, value) "
                        f"VALUES({event.obj.message['from_id']}, '{event.obj.message['text']}')")
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message="Thanks for your review!",
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
            con.commit()
        if waiting_for_imp and not admin_board and not waiting_for_rev and event.obj.message[
            'text'] != 'Back':
            waiting_for_imp = False
            keyboard = keyb(is_admin)
            cur.execute(f"INSERT INTO improvements(vk_id, value) "
                        f"VALUES({event.obj.message['from_id']}, '{event.obj.message['text']}')")
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message="Thanks for your improvement!",
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
            con.commit()
        if event.obj.message['text'] == 'Write a review' and not admin_board \
                and not waiting_for_imp:
            waiting_for_rev = True
            keyboard = back_keyb()
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message="Enter your review",
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
        if event.obj.message['text'] == 'Offer an improvement' and not admin_board \
                and not waiting_for_rev:
            waiting_for_imp = True
            keyboard = back_keyb()
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message="Enter your improvement",
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
        elif event.obj.message['text'] == 'Back' and not admin_board:
            keyboard = keyb(is_admin)
            waiting_for_rev = False
            waiting_for_imp = False
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message="⏬",
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
        if event.obj.message['text'] == 'Administration' \
                and event.obj.message['from_id'] in admins:
            keyboard = admin_keyb()
            admin_board = True
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message="⏬",
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
        elif event.obj.message['text'] == 'Back' and \
                admin_board and not white_board and \
                black_board and waiting_for_id and event.obj.message['from_id'] in admins:
            keyboard = list_keyb()
            waiting_for_id = False
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message="⏬",
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
        elif event.obj.message['text'] == 'Back' and \
                admin_board and white_board and not \
                black_board and waiting_for_id and event.obj.message['from_id'] in admins:
            keyboard = list_keyb()
            waiting_for_id = False
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message="⏬",
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
        elif not white_board and waiting_for_id and admin_board \
                and black_board and event.obj.message['from_id'] in admins:
            keyboard = list_keyb()
            waiting_for_id = False
            if int(event.obj.message['text']) != event.obj.message['from_id'] and int(
                    event.obj.message['text']) not in EXCEPTIONS:
                if int(event.obj.message['text']) not in black:
                    black.append(int(event.obj.message['text']))
                    cur.execute(f"INSERT INTO permissions(id, is_blocked, is_admin) "
                                f"VALUES({event.obj.message['text']}, 'TRUE', 'FALSE')")
                else:
                    cur.execute(f"UPDATE permissions\nSET is_blocked = 'TRUE'\n"
                                f"WHERE id = {event.obj.message['text']}")
                    cur.execute(f"UPDATE permissions\nSET is_admin = 'FALSE'\n"
                                f"WHERE id = {event.obj.message['text']}")
                con.commit()
                vk.messages.send(user_id=event.obj.message['from_id'],
                                 message='User added successfully',
                                 random_id=random.randint(0, 2 ** 64),
                                 keyboard=keyboard
                                 )
            elif int(event.obj.message['text']) in EXCEPTIONS:
                keyboard = list_keyb()
                vk.messages.send(user_id=event.obj.message['from_id'],
                                 message="You can't block this user",
                                 random_id=random.randint(0, 2 ** 64),
                                 keyboard=keyboard
                                 )
            else:
                keyboard = list_keyb()
                vk.messages.send(user_id=event.obj.message['from_id'],
                                 message="You can't block yourself",
                                 random_id=random.randint(0, 2 ** 64),
                                 keyboard=keyboard
                                 )
        elif white_board and waiting_for_id and admin_board and not black_board and \
                event.obj.message['from_id'] in admins:
            keyboard = list_keyb()
            waiting_for_id = False
            if int(event.obj.message['text']) not in admins:
                admins.append(int(event.obj.message['text']))
                cur.execute(f"INSERT INTO permissions(id, is_blocked, is_admin) "
                            f"VALUES({event.obj.message['text']}, 'FALSE', 'TRUE')")
            else:
                cur.execute(f"UPDATE permissions\nSET is_blocked = 'FALSE'\n"
                            f"WHERE id = {event.obj.message['text']}")
                cur.execute(f"UPDATE permissions\nSET is_admin = 'TRUE'\n"
                            f"WHERE id = {event.obj.message['text']}")
            con.commit()
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message='User added successfully',
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
        elif event.obj.message['text'] == 'Shut down' and \
                admin_board and event.obj.message['from_id'] in admins:
            terminate()
        elif event.obj.message['text'] == 'Administrators' and \
                admin_board and event.obj.message['from_id'] in admins:
            keyboard = list_keyb()
            white_board = True
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message="⏬",
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
        elif event.obj.message['text'] == 'Blacklist' and \
                admin_board and event.obj.message['from_id'] in admins:
            keyboard = list_keyb()
            black_board = True
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message="⏬",
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
        elif event.obj.message['text'] == 'Back' and admin_board and \
                white_board and not black_board and event.obj.message['from_id'] in admins:
            keyboard = admin_keyb()
            white_board = False
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message="⏬",
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
        elif event.obj.message['text'] == 'Back' and admin_board and not \
                white_board and not black_board and event.obj.message['from_id'] in admins:
            keyboard = keyb(is_admin)
            admin_board = False
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message="⏬",
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
        elif event.obj.message['text'] == 'Back' and admin_board and \
                white_board and not black_board and event.obj.message['from_id'] in admins:
            keyboard = admin_keyb()
            white_board = False
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message="⏬",
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
        elif event.obj.message['text'] == 'Back' and admin_board and not \
                white_board and black_board and event.obj.message['from_id'] in admins:
            keyboard = admin_keyb()
            black_board = False
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message="⏬",
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
        elif event.obj.message['text'] == 'All' and admin_board and not \
                white_board and black_board and event.obj.message['from_id'] in admins:
            if black:
                for i in range(len(black)):
                    is_online = vk_group_session.method("users.get", {"user_ids": black[i],
                                                                      "fields": 'online'})[0]
                    ans = user(black[i], is_online, type='black')
                    keyboard = ans[0]
                    vk.messages.send(user_id=event.obj.message['from_id'],
                                     message=ans[1],
                                     random_id=random.randint(0, 2 ** 64),
                                     keyboard=keyboard
                                     )
            else:
                keyboard = list_keyb()
                vk.messages.send(user_id=event.obj.message['from_id'],
                                 message='The blacklist is empty',
                                 random_id=random.randint(0, 2 ** 64),
                                 keyboard=keyboard
                                 )
        elif event.obj.message['text'] == 'All' and admin_board and \
                white_board and not black_board and event.obj.message['from_id'] in admins:
            if admins:
                for i in range(len(admins)):
                    is_online = vk_group_session.method("users.get", {"user_ids": admins[i],
                                                                      "fields": 'online'})[0]
                    ans = user(admins[i], is_online)
                    keyboard = ans[0]
                    vk.messages.send(user_id=event.obj.message['from_id'],
                                     message=ans[1],
                                     random_id=random.randint(0, 2 ** 64),
                                     keyboard=keyboard
                                     )
            else:
                keyboard = list_keyb()
                vk.messages.send(user_id=event.obj.message['from_id'],
                                 message='The list of admins is empty',
                                 random_id=random.randint(0, 2 ** 64),
                                 keyboard=keyboard
                                 )
        elif event.obj.message['text'] == 'Downgrade' and admin_board and white_board and not \
                black_board and event.obj.message['from_id'] in admins:
            if int(event.obj.message['text'].split()[1][1:-1]) != event.obj.message['from_id'] and \
                    int(event.obj.message['payload']) not in EXCEPTIONS:
                del admins[admins.index(int(event.obj.message['payload']))]
                cur.execute(f"DELETE from permissions\n"
                            f"WHERE id = {event.obj.message['payload']}")
                con.commit()
                keyboard = list_keyb()
                vk.messages.send(user_id=event.obj.message['from_id'],
                                 message='User downgraded successfully',
                                 random_id=random.randint(0, 2 ** 64),
                                 keyboard=keyboard
                                 )
            elif int(event.obj.message['payload']) in EXCEPTIONS:
                keyboard = list_keyb()
                vk.messages.send(user_id=event.obj.message['from_id'],
                                 message="You can't downgrade this user",
                                 random_id=random.randint(0, 2 ** 64),
                                 keyboard=keyboard
                                 )
            else:
                keyboard = list_keyb()
                vk.messages.send(user_id=event.obj.message['from_id'],
                                 message="You can't downgrade yourself",
                                 random_id=random.randint(0, 2 ** 64),
                                 keyboard=keyboard
                                 )
        elif event.obj.message['text'] == 'Unblock' and admin_board and not white_board and \
                black_board and event.obj.message['from_id'] in admins:
            del black[black.index(int(event.obj.message['payload']))]
            cur.execute(f"DELETE from permissions\n"
                        f"WHERE id = {event.obj.message['payload']}")
            con.commit()
            keyboard = list_keyb()
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message='User unlocked successfully',
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
        elif event.obj.message['text'] == 'Add user' and admin_board and not white_board \
                and black_board and event.obj.message['from_id'] in admins:
            waiting_for_id = True
            keyboard = back_keyb()
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message='Enter ID',
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
        elif event.obj.message['text'] == 'Add user' and admin_board and white_board and not \
                black_board and event.obj.message['from_id'] in admins:
            waiting_for_id = True
            keyboard = back_keyb()
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message='Enter ID',
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
        elif not waiting_for_imp and not waiting_for_rev and not waiting_for_id and \
                event.obj.message['text'] != 'Back':
            keyboard = keyb(is_admin)
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message='⏬',
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
