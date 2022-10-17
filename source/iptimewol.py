# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com

reference:
https://gist.github.com/stypr/97a25600ef2f30f14792213d2807a260
'''


import ctypes
import json
import re
import requests
import traceback

from pathlib import Path


current_directory = Path(__file__).resolve().parent
DEFAULT_SETTINGS_PATH = current_directory.joinpath('settings.json')
USER_SETTINGS_PATH = current_directory.parent.joinpath('settings.json')


with open(DEFAULT_SETTINGS_PATH, 'rb') as file:
    defaults = json.load(file)

settings = {}
if USER_SETTINGS_PATH.exists():
    with open(USER_SETTINGS_PATH, 'rb') as file:
        settings = json.load(file)


HOSTNAME = (settings.get('hostname') or defaults.get('hostname')).strip()
USERNAME = (settings.get('username') or defaults.get('hostname')).strip()
PASSWORD = (settings.get('password') or defaults.get('hostname')).strip()
MACADDRESS = (settings.get('macaddress') or defaults.get('hostname')).strip()
PRODUCTNAME = (settings.get('productname') or defaults.get('hostname')).strip()


class IPTIMEWOL:

    session = {}

    def __init__(self, host=HOSTNAME, product=PRODUCTNAME):
        self.host = host
        r = requests.get(f'{self.host}/sess-bin/login_session.cgi')
        assert product in r.text

    def login(self, username=USERNAME, password=PASSWORD):
        ''' typical login method '''

        d = {'init_status': 1, 'captcha_on': 0, 'captcha_file': '',
             'username': username, 'passwd': password, 'default_passwd': '',
             'captcha_code': ''}
        h = {'Referer': f'{self.host}/sess-bin/login_session.cgi',
             'User-Agent': 'Mozilla/5.0'}
        r = requests.post(f'{self.host}/sess-bin/login_handler.cgi', d, h)
        r = r.text
        if 'efm_session_id' in r:
            sess = r.split("setCookie('")[1].split("')")[0]
            self.session['efm_session_id'] = sess
            return True
        else:
            raise Exception('Incorrect Credentials!')

    def list(self):
        ''' list wol '''

        if not self.session['efm_session_id']:
            raise Exception('Not Authenticated')
        r = requests.get(f'{self.host}/sess-bin/timepro.cgi?tmenu=iframe' +
                         '&smenu=expertconfwollist', cookies=self.session)
        r = r.text
        r = r.split('name="remotepc_wollist" style="padding:0; margin:0;"')[1]
        r = r.split('<tr ')[1:]

        # clean up useless stuff
        clean_tag = re.compile('<.*?>')
        for i in range(len(r)):
            r[i] = r[i].split("<td ")
            for j in range(len(r[i])):
                r[i][j] = re.sub(clean_tag, '', '<td ' + r[i][j]).strip()
            if len(r[i]) <= 2:
                r[i] = []
            r[i] = [k for k in r[i] if k]
        r = r[1:]
        r = [k for k in r if k]

        # return format: [[no, mac, id], ...]
        # return r
        return {mac: name for _, mac, name in r}

    def wake(self, macaddress=MACADDRESS):
        ''' wake wol '''

        self.macaddress = macaddress
        if not self.session['efm_session_id']:
            raise Exception('Not Authenticated')
        d = {'tmenu': 'iframe', 'smenu': 'expertconfwollist', 'nomore': '0',
             'wakeupchk': self.macaddress, 'act': 'wake'}
        r = requests.post(f'{self.host}/sess-bin/timepro.cgi',
                          d, cookies=self.session)
        assert self.macaddress in r.text
        return True


def main():
    try:
        iptimewol = IPTIMEWOL()
        iptimewol.login()
        wols = iptimewol.list()
        success = iptimewol.wake()
        error = 'unknown error'
    except Exception:
        success = False
        error = traceback.format_exc()

    title = 'IPTIME WOL'

    if success:
        message = [
            'SUCCESS',
            iptimewol.host,
            iptimewol.macaddress,
            wols.get(iptimewol.macaddress)
        ]
    else:
        message = [
            'FAILED',
            iptimewol.host,
            iptimewol.macaddress,
            error
        ]

    message = '\n'.join(message)
    ctypes.windll.user32.MessageBoxW(0, message, title, 0)


if __name__ == '__main__':
    main()
