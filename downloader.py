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

    with open(bid_list, 'r') as f:
        for line in f.readlines():
            page_link = line.strip()

            m = re.match(r'([^ ]+)pkAtmMain=(?P<pkAtmMain>\w+)&tenderCaseNo=(?P<tenderCaseNo>[\w\-]+)', page_link)
            pkAtmMain = m.group('pkAtmMain')
            tenderCaseNo = m.group('tenderCaseNo')
            filename = "%s_%s" % (pkAtmMain, tenderCaseNo)

            request_get = requests.get(page_link)
            response = request_get.text.encode('utf8')

            soup = BeautifulSoup(''.join(response), 'lxml')
            print_area = soup.find('div', {"id": "printArea"})

            with open('{}/{}.txt'.format(directory, filename), 'w') as bid_detail:
                bid_detail.write(print_area.prettify("utf-8"))
                bid_detail.write('<div class="pkAtmMain">' + pkAtmMain + '</div>')
                bid_detail.write('<div class="tenderCaseNo">' + tenderCaseNo + '</div>')
                logger.info('Writing bid detail (pkAtmMain: {}, tenderCaseNo: {})'.format(pkAtmMain, tenderCaseNo))

            time.sleep(random.randint(0, 2))  # Prevent from being treated as a DDOS attack
