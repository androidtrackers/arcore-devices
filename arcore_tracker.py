#!/usr/bin/env python3.7
"""ARCore supported devices tracker"""

import difflib
from datetime import date
from os import environ, rename, path, system

from bs4 import BeautifulSoup
from requests import get, post
import pandas as pd

TODAY = str(date.today())
TG_CHAT = "@ARCoreDevices"
BOT_TOKEN = environ['bottoken']
GIT_OAUTH_TOKEN = environ['XFU']
CHANGES = []


def scrap_to_csv(url):
    """
    fetches Google's page and scrape device's table to csv
    """
    response = get(url)
    page = BeautifulSoup(response.content, 'html.parser')
    tables = page.findAll("table")
    data = pd.read_html(str(tables), index_col=0)
    open('devices.csv', 'w').close()
    for table in data:
        [table.drop(columns=column, axis=1, inplace=True)
         for column in table.columns if 'Notes' in column or 'Unnamed' in column]
        with open('devices.csv', 'a') as out:
            table.to_csv(out, sep=';', header=None)


def diff_files():
    """
    compare csv files to check for newly added devices
    """
    with open('old.csv', 'r') as old, open('devices.csv', 'r') as new:
        diff = difflib.unified_diff(old.readlines(), new.readlines(), fromfile='old', tofile='new')
        for line in diff:
            if line.startswith('+'):
                CHANGES.append(str(line))


def csv_to_md():
    """
    convert csv file to markdown
    """
    with open('devices.csv', 'r') as csv_file:
        csv = csv_file.readlines()
    with open('README.md', 'w', encoding='UTF-8') as out:
        out.write('# Google ARCore Supported devices\n')
        out.write('Last sync is {}\n\nhttps://developers.google.com/ar/'
                  'discover/supported-devices\n\n'.format(TODAY))
        out.write('|Brand|Device|\n')
        out.write('|---|---|\n')
        for line in csv:
            info = line.strip().split(";")
            try:
                brand = info[0]
                name = info[1]
                out.write(f'|{brand}|{name}|\n')
            except IndexError:
                pass


def post_to_tg():
    """
    post new devices to telegram channel
    """
    for item in CHANGES[1:]:
        info = item.split(";")
        brand = info[0].replace('+', '')
        name = info[1]
        telegram_message = f"New ARCore device added!:\nBrand: *{brand}*\nName: *{name}*"
        params = (
            ('chat_id', TG_CHAT),
            ('text', telegram_message),
            ('parse_mode', "Markdown"),
            ('disable_web_page_preview', "yes")
        )
        telegram_url = "https://api.telegram.org/bot" + BOT_TOKEN + "/sendMessage"
        telegram_req = post(telegram_url, params=params)
        telegram_status = telegram_req.status_code
        if telegram_status == 200:
            print("{0}: Telegram Message sent".format(name))
        else:
            print("Telegram Error")


def git_commit_push():
    """
    git add - git commit - git push
    """
    system(f"git add README.md && git -c \"user.name=XiaomiFirmwareUpdater\" "
           f"-c \"user.email=xiaomifirmwareupdater@gmail.com\""
           f"commit -m \"[skip ci] sync: {TODAY}\" && "" \
           f""git push -q https://{GIT_OAUTH_TOKEN}@github.com/"" \
           ""androidtrackers/arcore-devices.git HEAD:master")


def main():
    """
    ARCore supported devices tracker and scraper
    """
    if path.exists('devices.csv'):
        rename('devices.csv', 'old.csv')
    url = 'https://developers.google.com/ar/discover/supported-devices'
    scrap_to_csv(url)
    diff_files()
    if CHANGES:
        post_to_tg()
        csv_to_md()
        git_commit_push()


if __name__ == '__main__':
    main()
