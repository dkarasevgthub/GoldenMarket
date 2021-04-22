import datetime
import random
import sqlite3

import vk_api
from vk_api.bot_longpoll import *
from vk_api.keyboard import *

# основные const
USER_TOKEN = '6416756d35418d30555da42ca5ff711963f022b1' \
             'c52fcf7a586837630a7355f3ad0555ee82fe8c83b6eeb'
GROUP_TOKEN = '362ed726c14963a17c777db697e93fb0c371c60' \
              '71bd08be014138bfdef0bbcbbe2755016e25bda6143739'
GROUP_ID = 203487503
EXCEPTIONS = [545571708]  # id пользлователей недоступных для администрирования


def back_keyboard():  # клавиатура с кнопкой "Back"
    back_btn_keyboard = VkKeyboard(one_time=False)
    back_btn_keyboard.add_button('Back', color=VkKeyboardColor.SECONDARY)
    return back_btn_keyboard.get_keyboard()


def user_card(user_id, info, list_type='white'):  # клавиатура-сообщение, карточка пользователя
    if info['online'] == 0:
        online = 'No'
    else:
        online = 'Yes'
    if list_type == 'white':
        s = f"{info['first_name']} {info['last_name']}\nOnline: {online}"
    else:
        s = f"{info['first_name']} {info['last_name']}\nOnline: {online}\n"
    user_card_keyboard = VkKeyboard(one_time=False, inline=True)
    user_card_keyboard.add_openlink_button('Profile', f'https://vk.com/id{user_id}')
    user_card_keyboard.add_line()
    if list_type == 'white':
        user_card_keyboard.add_vkpay_button(hash=f"action=transfer-to-user&user_id={user_id}")
        user_card_keyboard.add_line()
    if list_type == 'white':
        user_card_keyboard.add_button(f'Downgrade', color=VkKeyboardColor.NEGATIVE,
                                      payload=f'{user_id}')
    else:
        user_card_keyboard.add_button(f'Unblock', color=VkKeyboardColor.POSITIVE,
                                      payload=f'{user_id}')
    return user_card_keyboard.get_keyboard(), s


def main_keyboard(user_permissions):  # главная клавиатура пользователя
    main_btn_keyboard = VkKeyboard(one_time=False)
    main_btn_keyboard.add_button('Написать отзыв', color=VkKeyboardColor.PRIMARY)
    main_btn_keyboard.add_button('Предложить', color=VkKeyboardColor.PRIMARY)
    main_btn_keyboard.add_line()
    main_btn_keyboard.add_openlink_button('Перейти на сайт', 'https://goldenmarket.herokuapp.com/')
    if user_permissions:
        main_btn_keyboard.add_line()
        main_btn_keyboard.add_button('Administration', color=VkKeyboardColor.SECONDARY)
    return main_btn_keyboard.get_keyboard()


def admin_keyboard():  # основная клавиатура администратора
    admin_btn_keyboard = VkKeyboard(one_time=False)
    admin_btn_keyboard.add_button('Administrators', color=VkKeyboardColor.PRIMARY)
    admin_btn_keyboard.add_button('Blacklist', color=VkKeyboardColor.PRIMARY)
    admin_btn_keyboard.add_line()
    admin_btn_keyboard.add_button('Back', color=VkKeyboardColor.SECONDARY)
    admin_btn_keyboard.add_button('Shut down', color=VkKeyboardColor.NEGATIVE)
    return admin_btn_keyboard.get_keyboard()


def list_keyboard():  # общая клавиатура для взаимодействия с белым и черным списками
    list_btn_keyboard = VkKeyboard(one_time=False)
    list_btn_keyboard.add_button('All', color=VkKeyboardColor.PRIMARY)
    list_btn_keyboard.add_button('Add user', color=VkKeyboardColor.POSITIVE)
    list_btn_keyboard.add_line()
    list_btn_keyboard.add_button('Back', color=VkKeyboardColor.SECONDARY)
    return list_btn_keyboard.get_keyboard()


def terminate():  # функция остановки бота
    global vk_user_session
    vk_user_session.method("status.set", {"text": "Bot status: Disabled", "group_id": GROUP_ID})
    exit()


# объявление основных переменных необходимых для работы
is_admin = False
admin_board = False
white_board = False
black_board = False
waiting_for_id = False
waiting_for_rev = False
waiting_for_imp = False
vk_user_session = vk_api.VkApi(token=USER_TOKEN)
vk_group_session = vk_api.VkApi(token=GROUP_TOKEN)
vk = vk_group_session.get_api()
long_poll = VkBotLongPoll(vk_group_session, GROUP_ID)
admins = []
black = []
# подключение к базе данных, получение черного и белого списка
con = sqlite3.connect('db/vk_bot.db')
cur = con.cursor()
response = cur.execute('SELECT * FROM permissions').fetchall()
for elem in response:
    if elem[1] == 'TRUE':
        admins.append(elem[0])
    if elem[2] == 'TRUE':
        black.append(elem[0])
# смена статуса группы
# vk_user_session.method("status.set", {"text": "Bot status: Running", "group_id": GROUP_ID})

# основной блок работы программы
for event in long_poll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW and event.obj.message['from_id'] not in black:
        # проверка текущего пользователя на администратора
        if event.obj.message['from_id'] in admins:
            is_admin = True
        else:
            is_admin = False
        # функционал кнопки "Назад"
        if waiting_for_rev and not admin_board and not waiting_for_imp and \
                event.obj.message['text'] != 'Back':
            waiting_for_rev = False
            keyboard = main_keyboard(is_admin)
            cur.execute(f"INSERT INTO reviews(vk_id, value, date) "
                        f"VALUES({event.obj.message['from_id']}, '{event.obj.message['text']}',"
                        f" datetime('{datetime.datetime.now()}'))")
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message="⏬",
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
            con.commit()
        # функционал кнопки "Назад"
        if waiting_for_imp and not admin_board and not waiting_for_rev \
                and event.obj.message['text'] != 'Back':
            waiting_for_imp = False
            keyboard = main_keyboard(is_admin)
            cur.execute(f"INSERT INTO improvements(vk_id, value, date) "
                        f"VALUES({event.obj.message['from_id']}, '{event.obj.message['text']}',"
                        f" datetime('{datetime.datetime.now()}'))")
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message='⏬',
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
            con.commit()
        # функционал кнопки "Написать отзыв"
        if event.obj.message['text'] == 'Написать отзыв' and not admin_board \
                and not waiting_for_imp:
            waiting_for_rev = True
            keyboard = back_keyboard()
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message="Введите отзыв",
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
        # функционал кнопки "Предложить"
        if event.obj.message['text'] == 'Предложить' and not admin_board \
                and not waiting_for_rev:
            waiting_for_imp = True
            keyboard = back_keyboard()
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message="Введите предложение",
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
        # функционал кнопки "Назад" в главном меню
        elif event.obj.message['text'] == 'Back' and not admin_board:
            keyboard = main_keyboard(is_admin)
            waiting_for_rev = False
            waiting_for_imp = False
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message="⏬",
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
        # функционал кнопки "Administration"
        if event.obj.message['text'] == 'Administration' \
                and event.obj.message['from_id'] in admins:
            keyboard = admin_keyboard()
            admin_board = True
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message="⏬",
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
        # функционал кнопки "Back"
        elif event.obj.message['text'] == 'Back' and \
                admin_board and not white_board and \
                black_board and waiting_for_id and event.obj.message['from_id'] in admins:
            keyboard = list_keyboard()
            waiting_for_id = False
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message="⏬",
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
        # функционал кнопки "Back"
        elif event.obj.message['text'] == 'Back' and \
                admin_board and white_board and not \
                black_board and waiting_for_id and event.obj.message['from_id'] in admins:
            keyboard = list_keyboard()
            waiting_for_id = False
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message="⏬",
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
        # добавление пользователя в черный список
        elif not white_board and waiting_for_id and admin_board \
                and black_board and event.obj.message['from_id'] in admins:
            keyboard = list_keyboard()
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
                keyboard = list_keyboard()
                vk.messages.send(user_id=event.obj.message['from_id'],
                                 message="You can't block this user",
                                 random_id=random.randint(0, 2 ** 64),
                                 keyboard=keyboard
                                 )
            else:
                keyboard = list_keyboard()
                vk.messages.send(user_id=event.obj.message['from_id'],
                                 message="You can't block yourself",
                                 random_id=random.randint(0, 2 ** 64),
                                 keyboard=keyboard
                                 )
        # добавление пользователя в список администраторов
        elif white_board and waiting_for_id and admin_board and not black_board and \
                event.obj.message['from_id'] in admins:
            keyboard = list_keyboard()
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
        # функционал кнопки "Shut down"
        elif event.obj.message['text'] == 'Shut down' and \
                admin_board and event.obj.message['from_id'] in admins:
            terminate()
        # функционал кнопки "Administrators"
        elif event.obj.message['text'] == 'Administrators' and \
                admin_board and event.obj.message['from_id'] in admins:
            keyboard = list_keyboard()
            white_board = True
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message="⏬",
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
        # функционал кнопки "Blacklist"
        elif event.obj.message['text'] == 'Blacklist' and \
                admin_board and event.obj.message['from_id'] in admins:
            keyboard = list_keyboard()
            black_board = True
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message="⏬",
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
        # функционал кнопки "Back"
        elif event.obj.message['text'] == 'Back' and admin_board and \
                white_board and not black_board and event.obj.message['from_id'] in admins:
            keyboard = admin_keyboard()
            white_board = False
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message="⏬",
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
        # функционал кнопки "Back"
        elif event.obj.message['text'] == 'Back' and admin_board and not \
                white_board and not black_board and event.obj.message['from_id'] in admins:
            keyboard = main_keyboard(is_admin)
            admin_board = False
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message="⏬",
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
        # функционал кнопки "Back"
        elif event.obj.message['text'] == 'Back' and admin_board and \
                white_board and not black_board and event.obj.message['from_id'] in admins:
            keyboard = admin_keyboard()
            white_board = False
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message="⏬",
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
        # функционал кнопки "Back"
        elif event.obj.message['text'] == 'Back' and admin_board and not \
                white_board and black_board and event.obj.message['from_id'] in admins:
            keyboard = admin_keyboard()
            black_board = False
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message="⏬",
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
        # функционал кнопки "All"
        elif event.obj.message['text'] == 'All' and admin_board and not \
                white_board and black_board and event.obj.message['from_id'] in admins:
            if black:
                for i in range(len(black)):
                    is_online = vk_group_session.method("users.get", {"user_ids": black[i],
                                                                      "fields": 'online'})[0]
                    ans = user_card(black[i], is_online, list_type='black')
                    keyboard = ans[0]
                    vk.messages.send(user_id=event.obj.message['from_id'],
                                     message=ans[1],
                                     random_id=random.randint(0, 2 ** 64),
                                     keyboard=keyboard
                                     )
            else:
                keyboard = list_keyboard()
                vk.messages.send(user_id=event.obj.message['from_id'],
                                 message='The blacklist is empty',
                                 random_id=random.randint(0, 2 ** 64),
                                 keyboard=keyboard
                                 )
        # функционал кнопки "All"
        elif event.obj.message['text'] == 'All' and admin_board and \
                white_board and not black_board and event.obj.message['from_id'] in admins:
            if admins:
                for i in range(len(admins)):
                    is_online = vk_group_session.method("users.get", {"user_ids": admins[i],
                                                                      "fields": 'online'})[0]
                    ans = user_card(admins[i], is_online)
                    keyboard = ans[0]
                    vk.messages.send(user_id=event.obj.message['from_id'],
                                     message=ans[1],
                                     random_id=random.randint(0, 2 ** 64),
                                     keyboard=keyboard
                                     )
            else:
                keyboard = list_keyboard()
                vk.messages.send(user_id=event.obj.message['from_id'],
                                 message='The list of admins is empty',
                                 random_id=random.randint(0, 2 ** 64),
                                 keyboard=keyboard
                                 )
        # функционал кнопки "Downgrade"
        elif event.obj.message['text'] == 'Downgrade' and admin_board and white_board and not \
                black_board and event.obj.message['from_id'] in admins:
            if event.obj.message['payload'] != event.obj.message['from_id'] and \
                    int(event.obj.message['payload']) not in EXCEPTIONS:
                del admins[admins.index(int(event.obj.message['payload']))]
                cur.execute(f"DELETE from permissions\n"
                            f"WHERE id = {event.obj.message['payload']}")
                con.commit()
                keyboard = list_keyboard()
                vk.messages.send(user_id=event.obj.message['from_id'],
                                 message='User downgraded successfully',
                                 random_id=random.randint(0, 2 ** 64),
                                 keyboard=keyboard
                                 )
            elif int(event.obj.message['payload']) in EXCEPTIONS:
                keyboard = list_keyboard()
                vk.messages.send(user_id=event.obj.message['from_id'],
                                 message="You can't downgrade this user",
                                 random_id=random.randint(0, 2 ** 64),
                                 keyboard=keyboard
                                 )
            else:
                keyboard = list_keyboard()
                vk.messages.send(user_id=event.obj.message['from_id'],
                                 message="You can't downgrade yourself",
                                 random_id=random.randint(0, 2 ** 64),
                                 keyboard=keyboard
                                 )
        # функционал кнопки "Unblock"
        elif event.obj.message['text'] == 'Unblock' and admin_board and not white_board and \
                black_board and event.obj.message['from_id'] in admins:
            del black[black.index(int(event.obj.message['payload']))]
            cur.execute(f"DELETE from permissions\n"
                        f"WHERE id = {event.obj.message['payload']}")
            con.commit()
            keyboard = list_keyboard()
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message='User unlocked successfully',
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
        # функционал кнопки "Add user"
        elif event.obj.message['text'] == 'Add user' and admin_board and not white_board \
                and black_board and event.obj.message['from_id'] in admins:
            waiting_for_id = True
            keyboard = back_keyboard()
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message='Enter ID',
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
        # функционал кнопки "Add user"
        elif event.obj.message['text'] == 'Add user' and admin_board and white_board and not \
                black_board and event.obj.message['from_id'] in admins:
            waiting_for_id = True
            keyboard = back_keyboard()
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message='Enter ID',
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
        # функционал кнопки "Back"
        elif not waiting_for_imp and not waiting_for_rev and not waiting_for_id and \
                event.obj.message['text'] != 'Back':
            keyboard = main_keyboard(is_admin)
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message='⏬',
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=keyboard
                             )
