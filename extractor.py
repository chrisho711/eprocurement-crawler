# -*- coding: utf-8 -*-
import os
import re
import logging
from optparse import OptionParser
from bs4 import BeautifulSoup
from datetime import datetime, date

_ERRCODE_DIR = 4

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)


def get_response_element(file_name):
    f = open(file_name, 'r')
    response_text = f.read()
    f.close()
    soup = BeautifulSoup(''.join(response_text), 'lxml')
    tender_table = soup.find('table', {'class': 'table_block tender_table'})
    return tender_table


def strip(element):
    return element.strip()


def remove_space(element):
    return ''.join(element.split())


def unescape_conversion(element):
    return remove_space(element).replace('&lt;', '<').replace('&gt;', '>')


def date_conversion(element):
    m = re.match(r'(?P<date>\d+/\d+/\d+)(\s+)*(?P<time>\d+:\d+)?', element.strip())
    if m is not None:
        d = [int(n) for n in m.group('date').split('/')]
        t = [int(n) for n in m.group('time').split(':')] if m.group('time') is not None else None
        if d[0] != '':
            if t is not None:
                return datetime(d[0] + 1911, d[1], d[2], hour=t[0], minute=t[1])
            else:
                return date(d[0] + 1911, d[1], d[2])
    return None


def money_conversion(element):
    m = re.match(r'\$?-?([0-9,]+)', ''.join(element.split()))
    return int(''.join(m.group(0).split(',')))


def phone_conversion(element):
    m = re.match(r'(\((?P<area>\d+)\))?(?P<number>\d+)', element.strip())
    return m.group('area') + '-' + m.group('number') if m.group('area') is not None else m.group('number')


organization_info_map = {
    # award_table_tr_1
    '機關代碼': ('id', remove_space),
    '機關名稱': ('org_name', remove_space),
    '單位名稱': ('unit_name', remove_space),
    '機關地址': ('address', remove_space),
    '聯絡人': ('contact', strip),
    '聯絡電話': ('phone', phone_conversion),
    '傳真號碼': ('fax', phone_conversion)}

procurement_info_map = {
    # award_table_tr_2
    '標案案號': ('job_number', remove_space),
    '招標方式': ('procurement_type', remove_space),
    '決標方式': ('tender_awarding_type', remove_space),
    '標案名稱': ('subject_of_procurement', remove_space),
    '決標資料類別': ('attr_of_tender_awarding', remove_space),
    '標的分類': ('attr_of_procurement', unescape_conversion),
    '預算金額': ('budget_value', money_conversion),
    '開標時間': ('opening_date', date_conversion),
    '歸屬計畫類別': ('project_type', remove_space),
    '總決標金額': ('total_tender_awarding_value', date_conversion),
    'pkAtmMain': ('pkAtmMain', strip)}

award_info_map = {
    # award_table_tr_6
    '底價金額': ('floor_price_value', money_conversion),
    '決標日期': ('tender_awarding_date', date_conversion),
    '決標公告日期': ('tender_awarding_announce_date', date_conversion)}

tender_award_item_map = {
    '得標廠商': 'awarded_tenderer',
    '預估需求數量': 'request_number',
    '決標金額': 'tender_awarding_value',
    '底價金額': 'floor_price_value'}

tenderer_map = {
    '廠商代碼': 'tenderer_code',
    '廠商名稱': 'tenderer_name',
    '是否得標': 'awarded',
    '組織型態': 'organization_type'}


def get_organization_info_dic(element):
    returned_dic = {}
    mapper = organization_info_map
    award_table_tr = element.findAll('tr', {'class': 'award_table_tr_1'})
    for tr in award_table_tr:
        th = tr.find('th')
        if th is not None:
            th_name = th.text.encode('utf-8').strip()
            if th_name in mapper:
                key = mapper[th_name][0]
                content = tr.find('td').text
                returned_dic[key] = mapper[th_name][1](content) if len(mapper[th_name]) == 2 else content

    # Print returned_dic
    if logging.getLogger().isEnabledFor(logging.DEBUG):
        for k, v in returned_dic.iteritems():
            logger.debug(u'{}\t{}'.format(k, v))

    return returned_dic


def get_procurement_info_dic(element):
    returned_dic = {}
    mapper = procurement_info_map
    award_table_tr = element.findAll('tr', {'class': 'award_table_tr_2'})
    for tr in award_table_tr:
        th = tr.find('th')
        if th is not None:
            th_name = th.text.encode('utf-8').strip()
            if th_name in mapper:
                key = mapper[th_name][0]
                content = tr.find('td').text
                returned_dic[key] = mapper[th_name][1](content) if len(mapper[th_name]) == 2 else content

    # Print returned_dic
    if logging.getLogger().isEnabledFor(logging.DEBUG):
        for k, v in returned_dic.iteritems():
            logger.debug(u'{}\t{}'.format(k, v))

    return returned_dic


def get_award_info_dic(element):
    returned_dic = {}
    mapper = award_info_map
    award_table_tr = element.findAll('tr', {'class': 'award_table_tr_6'})
    for tr in award_table_tr:
        th = tr.find('th')
        if th is not None:
            th_name = th.text.encode('utf-8').strip()
            if th_name in mapper:
                key = mapper[th_name][0]
                content = tr.find('td').text
                returned_dic[key] = mapper[th_name][1](content) if len(mapper[th_name]) == 2 else content

    # Print returned_dic
    if logging.getLogger().isEnabledFor(logging.DEBUG):
        for k, v in returned_dic.iteritems():
            logger.debug(u'{}\t{}'.format(k, v))

    return returned_dic


def get_tenderer_info_dic(element):
    returned_dic = {}
    award_table_tr_3 = element.findAll('tr', {'class': 'award_table_tr_3'})
    for tr in award_table_tr_3:
        tb = tr.find('table')
        grp_num = 0
        if tb is not None:
            row = tb.findAll('tr')
            for r in row:
                th = r.find('th').text
                m = re.match(r'投標廠商(\d+)', th.encode('utf-8').strip())
                if m is not None:
                    grp_num = int(m.group(1))
                    returned_dic[grp_num] = {'tenderer_num': grp_num}
                else:
                    if th.encode('utf-8').strip() in tenderer_map:
                        returned_dic[grp_num][tenderer_map[th.encode('utf-8').strip()]] = r.find('td').text.strip()

    # Print returned_dic
    if logging.getLogger().isEnabledFor(logging.DEBUG):
        for rec in returned_dic:
            for i in returned_dic[rec]:
                logger.debug(u'{}\t{}'.format(i, returned_dic[rec][i]))

    return returned_dic


def get_tender_award_item_dic(element):
    returned_dic = {}
    award_table_tr_4 = element.findAll('tr', {'class': 'award_table_tr_4'})
    for tr in award_table_tr_4:
        tb = tr.find('table')
        if tb is not None:
            row = tb.findAll('tr')
            item_num = 0
            grp_num = 0
            for r in row:
                if r.find('th') is not None:
                    th = r.find('th').text
                    # print r.find('th').text
                    m = re.match(r'第(\d+)品項', th.encode('utf-8').strip())
                    m2 = re.match(r'得標廠商(\d+)', th.encode('utf-8').strip())
                    if m is not None:
                        item_num = int(m.group(1).decode('utf-8'))
                        returned_dic[item_num] = {}
                    elif m2 is not None:
                        grp_num = int(m2.group(1).decode('utf-8'))
                        returned_dic[item_num][grp_num] = {}
                    else:
                        if th.encode('utf-8').strip() in tender_award_item_map:
                            # print th.encode('utf-8').strip().decode('utf-8')
                            if th.encode('utf-8').strip() == '決標金額' or th.encode('utf-8').strip() == '底價金額':
                                m = re.match(r"\$?-?([0-9,]+)", "".join(r.find('td').text.split()))
                                returned_dic[item_num][grp_num][
                                    tender_award_item_map[th.encode('utf-8').strip()]] = int(
                                    ''.join(m.group(0).split(',')))
                            else:
                                returned_dic[item_num][grp_num][
                                    tender_award_item_map[th.encode('utf-8').strip()]] = r.find(
                                    'td').text.strip()

    # Print returned_dic
    if logging.getLogger().isEnabledFor(logging.DEBUG):
        for item_k, item_v in returned_dic.iteritems():
            for tender_k, tender_v in item_v.iteritems():
                for detail_k, detail_v in tender_v.iteritems():
                    logger.debug(u'Item: {}, tender: {}, {}\t{}'.format(item_k, tender_k, detail_k, detail_v))

    return returned_dic


def parse_args():
    p = OptionParser()
    p.add_option('-d', '--directory', action='store',
                 dest='directory', type='string', default='bid_detail')
    return p.parse_args()


if __name__ == '__main__':
    options, remainder = parse_args()

    directory = options.directory.strip()
    if not os.path.isdir(directory):
        logger.error('No such directory: ' + directory)
        quit(_ERRCODE_DIR)

    response_element = get_response_element(directory + '/' + '51744761_09.txt')
    get_organization_info_dic(response_element)
    get_procurement_info_dic(response_element)
    get_tenderer_info_dic(response_element)
    get_tender_award_item_dic(response_element)
    get_award_info_dic(response_element)
