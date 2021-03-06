#!/usr/bin/python
#  -*- coding: utf-8 -*-
""" Downloader for Taiwan government e-procurement website
Modified from the source code provided by https://github.com/ywchiu/pythonetl"""

import os
import requests
import logging
import time
import re
import random
from optparse import OptionParser
from bs4 import BeautifulSoup

__author__ = "Yu-chun Huang"
__version__ = "1.0.0b"

_ERRCODE_FILENAME = 3
_ERRCODE_DIR = 4

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_args():
    p = OptionParser()
    p.add_option('-f', '--list_filename', action='store',
                 dest='list_filename', type='string', default='')
    p.add_option('-d', '--directory', action='store',
                 dest='directory', type='string', default='bid_detail')
    return p.parse_args()


if __name__ == '__main__':
    options, remainder = parse_args()

    bid_list = options.list_filename.strip()
    if not bid_list:
        logger.error('Invalid bid list filename.')
        quit(_ERRCODE_FILENAME)

    directory = options.directory.strip()
    if directory:
        try:
            os.makedirs(directory)
        except OSError:
            if not os.path.isdir(directory):
                logger.error('Fail to create directory.')
                quit(_ERRCODE_DIR)

    with open(bid_list, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            page_link = line.strip()

            m1 = re.match(r'([^ ]+)pkAtmMain=(?P<pkAtmMain>\w+)&tenderCaseNo=(?P<tenderCaseNo>[\w\-]+)', page_link)
            if m1 is None:
                m2 = re.match(r'([^ ]+)primaryKey=(?P<primaryKey>[\w\-]+)', page_link)
                if m2 is None:
                    continue
                else:
                    primaryKey = m2.group('primaryKey')
                    if primaryKey is None:
                        continue
                    else:
                        filename = primaryKey
            else:
                pkAtmMain = m1.group('pkAtmMain')
                tenderCaseNo = m1.group('tenderCaseNo')
                if pkAtmMain is None or tenderCaseNo is None:
                    continue
                else:
                    filename = "%s_%s" % (pkAtmMain, tenderCaseNo)

            try:
                request_get = requests.get(page_link)
                response = request_get.text

                soup = BeautifulSoup(''.join(response), 'lxml')
                if m1 is not None:
                    print_area = soup.find('div', {"id": "printArea"})
                else:
                    print_area = soup.find('div', {"id": "print_area"})

                with open('{}/{}.txt'.format(directory, filename), 'w', encoding='utf-8') as bid_detail:
                    bid_detail.write(print_area.prettify())
                    if m1 is not None:
                        bid_detail.write('<div class="pkAtmMain">' + pkAtmMain + '</div>\n')
                        bid_detail.write('<div class="tenderCaseNo">' + tenderCaseNo + '</div>')
                        logger.info(
                            'Writing bid detail (pkAtmMain: {}, tenderCaseNo: {})'.format(pkAtmMain, tenderCaseNo))
                    else:
                        bid_detail.write('<div class="primaryKey">' + primaryKey + '</div>\n')
                        logger.info(
                            'Writing bid detail (primaryKey: {})'.format(primaryKey))
            except:
                with open(options.list_filename.strip() + '.download.err', 'a', encoding='utf-8') as err_file:
                    err_file.write(page_link + '\n')
                continue

            time.sleep(1)  # Prevent from being treated as a DDOS attack
