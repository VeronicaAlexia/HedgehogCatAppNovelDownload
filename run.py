import sys
import time
# from rich import print
import book
from instance import *
import HbookerAPI
import re
import argparse


def shell_bookshelf():  # download bookshelf book
    response = HbookerAPI.BookShelf.get_shelf_list()  # get bookshelf list
    if response.get('code') != '100000':
        print("code:", response.get('code'), "Msg:", response.get("tip"))
        return False
    for shelf in response['data']['shelf_list']:
        print('bookshelf index:', shelf['shelf_index'], ', bookshelf name:', shelf['shelf_name'])

    if len(response['data']['shelf_list']) > 1:
        shelf_list = response['data']['shelf_list'][int(get("please input book index:").strip()) - 1]
    else:
        shelf_list = response['data']['shelf_list'][0]
        print("this account only one bookshelf, auto bookshelf index:", shelf_list['shelf_name'])

    book_list = HbookerAPI.BookShelf.shelf_list(shelf_list['shelf_id'])
    if book_list.get('code') == '100000':
        for index, data in enumerate(book_list['data']['book_list']):
            Vars.current_bookshelf.append(book.Book(book_info=data['book_info'], index=str(index + 1)))

        for book_info in Vars.current_bookshelf:  # print bookshelf book list
            print("\nindex:", book_info.index)
            print('name:', book_info.book_name, " author:", book_info.author_name, " id:", book_info.book_id)
            print("time:", book_info.last_chapter['uptime'], "chapter:", book_info.last_chapter['chapter_title'])

        input_shelf_book_index = get("please input book index:").strip()
        for book_info in Vars.current_bookshelf:
            if book_info.index == input_shelf_book_index:
                shell_download_book(["", book_info.book_id])
        Vars.current_bookshelf.clear()  # clear bookshelf list
    else:
        print("code:", book_list.get('code'), "Msg:", book_list.get("tip"))


# def shell_login(inputs): # invalid login
#     if len(inputs) >= 3:
#         Vars.cfg.data['account_info'] = {'login_name': inputs[1], 'passwd': inputs[2]}
#         response = HbookerAPI.SignUp.login(Vars.cfg.data.get('account_info'))
#         if response.get('code') == '100000':
#             Vars.cfg.data['common_params'] = {
#                 'account': response['data']['reader_info']['account'],
#                 'login_token': response['data']['login_token'], 'app_version': '2.9.022'
#             }
#             Vars.cfg.save()
#             print('????????????, ?????????????????????:', HbookerAPI.SignUp.user_account())
#         else:
#             print(response.get('tip'))
#     else:
#         print("?????????????????????:", HbookerAPI.SignUp.user_account())


def shell_download_book(inputs):
    if len(inputs) >= 2:
        start_time, book_id = time.time(), get_id(inputs[1])
        if not str(book_id).isdigit():
            print('[ warning ] book-id is not digit')
            Vars.current_book = None
        elif len(str(book_id)) != 9:
            print('[ warning ] book-book-id is not 9 digits')
            Vars.current_book = None
        else:
            Vars.current_book = HbookerAPI.Book.get_info_by_id(book_id)
            if Vars.current_book.get('code') != '100000':
                print("code:", Vars.current_book.get('code'), "Msg:", Vars.current_book.get("tip"))
                if "??????????????????app???????????????" in Vars.current_book.get("tip"):
                    response = HbookerAPI.SignUp.get_ciweimao_version()
                    if response is not None and isinstance(response, dict):
                        print("????????????app????????? : " + Vars.cfg.data['common_params']['app_version'])
                        print("????????????app????????? : " + response['data']['android_version'])
                        print("?????????????????????????????????...")
                        Vars.cfg.data['common_params']['app_version'] = response['data'].get('android_version')
                        Vars.cfg.save()
                    else:
                        print("?????????????????????????????????????????????????????????????????????????????????app?????????")
                Vars.current_book = None

        if Vars.current_book is not None and isinstance(Vars.current_book, dict):
            Vars.current_book = book.Book(book_info=Vars.current_book.get('data').get('book_info'))

            Vars.current_book.book_information()
            if Vars.current_book.get_division_list():
                if len(Vars.current_book.download_chapter_list) != 0:
                    Vars.current_book.start_download_chapter()
                    Vars.current_book.save_export_txt_epub()  # save export txt and epub file
                    if Vars.cfg.data['downloaded_book_id_list'].count(Vars.current_book.book_id) == 0:
                        Vars.cfg.data['downloaded_book_id_list'].append(Vars.current_book.book_id)
                        Vars.cfg.save()
                    print("??????{} ??????: {:.2f}???".format(Vars.current_book.book_name, time.time() - start_time))
                else:
                    print("[info]" + Vars.current_book.book_name, "download chapter list is empty")
                    if Vars.force_output:
                        Vars.current_book.save_export_txt_epub()  # save export txt and epub file

                Vars.current_book = None
    else:
        print('?????????book_id')


def shell_update():
    if len(Vars.cfg.data.get('downloaded_book_id_list')) == 0:
        print('???????????????????????????????????????config.json downloaded_book_id_list')
    else:
        for index, book_id in enumerate(Vars.cfg.data['downloaded_book_id_list']):
            shell_download_book([index, book_id])
    print('[??????]?????????????????????')


def update_config():
    Vars.cfg.load()
    if Vars.cfg.data.get('downloaded_book_id_list') is None:
        Vars.cfg.data['downloaded_book_id_list'] = []
    if not isinstance(Vars.cfg.data.get('max_thread'), int):
        Vars.cfg.data['max_thread'] = 32
    if not isinstance(Vars.cfg.data.get('save_path'), str):
        Vars.cfg.data['save_path'] = "./Hbooker/"
    if not isinstance(Vars.cfg.data.get('out_path'), str):
        Vars.cfg.data['out_path'] = "./downloads/"
    if not isinstance(Vars.cfg.data.get('common_params'), dict):
        Vars.cfg.data['common_params'] = {
            'login_token': "", 'account': "", 'app_version': '2.9.022', 'device_token': 'ciweimao_'}
    Vars.cfg.save()


def new_tests_account_login():
    if Vars.cfg.data['common_params']['login_token'] == "":
        print("[warn]test login_token is empty, please input login_token in config.json")
        print("[input]please input your login_token:")
        account_token = get('>').strip()
        if len(account_token) == 32:
            Vars.cfg.data['common_params']['login_token'] = account_token
            Vars.cfg.save()
            print("[info]login_token is saved in config.json")
        else:
            print('[warn]login_token is length error!\nplease input length 32 login_token:')
            sys.exit(0)

    if Vars.cfg.data['common_params']['account'] == "":
        print("[warn]test account is empty, please input account in config.json")
        print("[input]please input your account:")
        account_name = get('>').strip()
        if len(account_name) > 0 and "??????" in account_name:
            Vars.cfg.data['common_params']['account'] = account_name
            Vars.cfg.save()
            print("[info]account is saved in config.json")
        else:
            print('[warn]account info is invalid!\nplease input again')
            sys.exit(0)
    if HbookerAPI.SignUp.user_account() is None:
        print("[warn]hbooker api test account is invalid, test your config.json information")
        Vars.cfg.data.clear()
        update_config()
        new_tests_account_login()
    else:
        print('[info]the current account is:', HbookerAPI.SignUp.user_account())


def new_shell_login(frequency=0):
    if frequency == 0:
        print("[input]please input your login_token:")
        account_token = get('>').strip()
        if len(account_token) == 32:
            Vars.cfg.data['common_params']['login_token'] = account_token
            Vars.cfg.save()
            print("[info]login_token is saved in config.json")
        else:
            print('[warn]login_token is length error!\nplease input length 32 login_token:')
            new_shell_login()
    print("[input]please input your account name:")
    account_name = get('>').strip()
    if len(account_name) > 0 and "??????" in account_name:
        Vars.cfg.data['common_params']['account'] = account_name
        Vars.cfg.save()
        print("account info is saved in config.json")
    else:
        print('[warn]account info is invalid!\nplease input again')
        new_shell_login(1)


# def tests_account_login():
#     if HbookerAPI.SignUp.user_account() is not None:
#         print("??????????????????:", HbookerAPI.SignUp.user_account())
#     else:
#         if Vars.cfg.data.get('account_info') is not None:
#             print("????????????????????????????????????????????????...")
#             response = HbookerAPI.SignUp.login(Vars.cfg.data['account_info'])
#             if response.get('code') == '100000':
#                 Vars.cfg.data['common_params'] = {
#                     'account': response['data']['reader_info']['account'],
#                     'login_token': response['data']['login_token'], 'app_version': '2.9.022'
#                 }
#                 Vars.cfg.save()
#                 print("??????:", HbookerAPI.SignUp.user_account(), "?????????????????????")
#             else:
#                 print("????????????:", response.get('tip'))
#         else:
#             print("??????????????????????????????????????????????????????????????????")


def shell(inputs):
    choice = inputs[0].lower()
    if choice == 'q' or choice == 'quit':
        sys.exit(3)
    elif choice == 'l' or choice == 'login':
        new_shell_login()
    elif choice == 'd' or choice == 'download':
        shell_download_book(inputs)
    elif choice == 'bs' or choice == 'bookshelf':
        shell_bookshelf()
    elif choice == 'up' or choice == 'update':
        shell_update()


def shell_parser():
    parser, shell_console = argparse.ArgumentParser(), False
    parser.add_argument("-d", "--download", dest="downloadbook", nargs=1, default=None, help="please input book_id")
    parser.add_argument("-m", "--max", dest="threading_max", default=None, help="please input max threading")
    parser.add_argument("-up", "--update", dest="update", default=False, action="store_true", help="update books")
    parser.add_argument("-bi", "--bookinfo", dest="bookinfo", nargs=1, default=None, help="please input book_id")
    parser.add_argument("-bs", "--bookshelf", default=False, action="store_true", help="download bookshelf books")
    parser.add_argument("-clear", "--clear_cache", dest="clear_cache", default=False, action="store_true")
    # parser.add_argument("-s", "--shell", dest="shell", default=False, action="store_true", help="??????????????????")
    parser.add_argument("-f", "--force", action="store_true", default=False, dest="force",
                        help="Export to txt and epub files even when there is no new content downloaded.")
    args = parser.parse_args()
    Vars.force_output = args.force
    if args.bookshelf:
        shell_bookshelf()
        shell_console = True

    if args.update:
        shell_update()
        shell_console = True

    if args.clear_cache:
        Vars.cfg.data.clear()
        Vars.cfg.save()
        sys.exit(3)

    if args.threading_max:
        Vars.cfg.data['max_thread'] = int(args.max)

    if args.downloadbook:
        shell_download_book(['d'] + args.downloadbook)
        shell_console = True

    if args.bookinfo:
        Vars.current_book = HbookerAPI.Book.get_info_by_id(get_id(args.bookinfo[0])).get('data')
        if Vars.current_book is not None:
            Vars.current_book = book.Book(book_info=Vars.current_book.get('book_info'))
        shell_console = True

    # if args.login is not None:  # invalid login
    #     shell_login(['login'] + args.login)
    #     shell_console = True

    if not shell_console:
        for info in Vars.help_info:
            print('[??????]', info)
        while True:
            shell(re.split('\\s+', get('>').strip()))


if __name__ == '__main__':
    update_config()  # update config.json
    try:
        new_tests_account_login()  # this is for login test
        # tests_account_login() # this is invalid test account login
        shell_parser()  # this is for shell
    except KeyboardInterrupt:  # Ctrl+C to exit
        print('\n[??????]???????????????')
