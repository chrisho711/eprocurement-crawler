#!/usr/bin/python
#  -*- coding: utf-8 -*-
""" Extractor for Taiwan government e-procurement website
Modified from the source code provided by https://github.com/ywchiu/pythonetl"""

import os
import re
import logging
from optparse import OptionParser
from bs4 import BeautifulSoup
from datetime import datetime, date

__author__ = "Yu-chun Huang"
__version__ = "1.0.0b"

_ERRCODE_FILENAME = 3

logger = logging.getLogger(__name__)


def init(filename):
    f = open(filename, 'r', encoding='utf-8')
    response_text = f.read()
    f.close()
    soup = BeautifulSoup(''.join(response_text), 'lxml')
    pk = soup.find('div', {'class': 'primaryKey'}).text
    root = soup.find('table', {'class': 'table_block tender_table'})
    logger.debug('primaryKey: ' + pk)

    return pk, root


def strip(element):
    return element.strip()


def remove_space(element):
    return ''.join(element.split())


def unescape_conversion(element):
    return remove_space(element).replace('&lt;', '<').replace('&gt;', '>')


def yesno_conversion(element):
    m = re.match(r'.*是.*', element.strip())
    return m is not None


def int_conversion(element):
    m = re.match(r'-?([\d,\.]+)', ''.join(element.split()))
    return int(''.join(m.group(0).split(',')))


def float_conversion(element):
    m = re.match(r'-?([\d,\.]+)', ''.join(element.split()))
    return float(''.join(m.group(0).split(',')))


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
    m = re.match(r'\$?-?([\d,\.]+)', ''.join(element.split()))
    return int(''.join(m.group(0).split(',')))


def tel_conversion(element):
    m = re.match(r'(\((?P<area>\d+)\))?\s*(?P<number>\**\d*\**)(\s*分機\s*(?P<extension>\**\d*\**))?', element.strip())
    outstr = ''
    if m.group('area') is not None:
        outstr += m.group('area') + '-'
    if m.group('number') is not None:
        outstr += m.group('number')
    if m.group('extension') is not None:
        outstr += ' ext ' + m.group('extension')
    return outstr


organization_info_map = {
    # <tr class="tender_table_tr_1">
    '機關代碼': ('org_id', remove_space),
    '機關名稱': ('org_name', remove_space),
    '單位名稱': ('unit_name', remove_space),
    '機關地址': ('org_address', remove_space),
    '聯絡人': ('contact', strip),
    '聯絡電話': ('tel', tel_conversion),
    '傳真號碼': ('fax', tel_conversion),
    '電子郵件信箱': ('email', remove_space)}

procurement_info_map = {
    # <tr class="tender_table_tr_2">
    '標案案號': ('tender_case_no', remove_space),
    '標案名稱': ('subject_of_procurement', remove_space),
    '標的分類': ('attr_of_procurement', unescape_conversion),
    '工程計畫編號': ('project_no', strip),
    '本採購案是否屬於建築工程': ('is_construction', yesno_conversion),
    '財物採購性質': ('attr_of_goods', strip),
    '採購金額級距': ('procurement_money_amt_lv', remove_space),
    '辦理方式': ('conduct_procurement', remove_space),
    '依據法條': ('apply_law', remove_space),
    '是否適用WTO政府採購協定(GPA)：': ('is_gpa',),  # Special processing required
    '是否適用臺紐經濟合作協定(ANZTEC)：': ('is_anztec',),  # Special processing required
    '是否適用臺星經濟夥伴協定(ASTEP)：': ('is_astep',),  # Special processing required
    '預算金額': ('budget_amount', money_conversion),
    '預算金額是否公開': ('is_budget_amount_public', yesno_conversion),
    '後續擴充': ('is_extension', yesno_conversion),
    '是否受機關補助': ('is_org_subsidy', yesno_conversion),
    '是否含特別預算': ('is_special_budget', yesno_conversion)}

declaration_info_map = {
    # <tr class="tender_table_tr_3">
    '招標方式': ('procurement_type', remove_space),
    '決標方式': ('awarding_type', remove_space),
    '是否依政府採購法施行細則第64條之2辦理': ('is_follow_law_64_2', yesno_conversion),
    '是否電子報價': ('is_electronic_quote', yesno_conversion),
    '新增公告傳輸次數': ('num_transmit', int_conversion),
    '招標狀態': ('procurement_status', strip),
    '公告日': ('publication_date', date_conversion),
    '是否複數決標': ('is_multiple_award', yesno_conversion),
    '是否訂有底價': ('is_base_price', yesno_conversion),
    '是否屬特殊採購': ('is_special', yesno_conversion),
    '是否已辦理公開閱覽': ('is_public_view', yesno_conversion),
    '是否屬統包': ('is_design_build_contract', yesno_conversion),
    '是否屬共同供應契約採購': ('is_inter_ent_sup_contract', yesno_conversion),
    '是否屬二以上機關之聯合採購(不適用共同供應契約規定)': ('is_joint_procurement', yesno_conversion),
    '是否應依公共工程專業技師簽證規則實施技師簽證': ('is_engineer_cert_required', yesno_conversion),
    '是否採行協商措施': ('is_negotiation', yesno_conversion),
    '是否適用採購法第104條或105條或招標期限標準第10條或第4條之1': ('is_follow_law_104_105', yesno_conversion),
    '是否依據採購法第106條第1項第1款辦理': ('is_follow_law_106_1_1', yesno_conversion)}

attend_info_map = {
    # <tr class="tender_table_tr_4">
    '是否提供電子領標': ('is_elec_receive_tender', yesno_conversion),
    '是否提供電子投標': ('is_elec_submit_tender', yesno_conversion),
    '截止投標': ('submit_date', date_conversion),
    '開標時間': ('award_date', date_conversion),
    '開標地點': ('award_address', strip),
    '是否須繳納押標金': ('is_tender_bond', yesno_conversion),
    '投標文字': ('submit_language', remove_space),
    '收受投標文件地點': ('submit_address', strip)}

other_info_map = {
    # <tr class="tender_table_tr_5">
    '是否依據採購法第99條': ('is_follow_law_99', yesno_conversion),
    '履約地點': ('fulfill_location', strip),
    '履約期限': ('fulfill_deadline', remove_space),
    '是否刊登公報': ('is_post_bulletin', yesno_conversion),
    '本案採購契約是否採用主管機關訂定之範本': ('is_authorities_template', yesno_conversion),
    '歸屬計畫類別': ('project_type', remove_space),
    '廠商資格摘要': ('qualify_abstract', strip),
    '是否訂有與履約能力有關之基本資格': ('is_qualify_fulfill', yesno_conversion)}


def get_organization_info_dic(root_element):
    if root_element is None:
        return None

    returned_dic = {}
    mapper = organization_info_map
    award_table_tr = root_element.findAll('tr', {'class': 'tender_table_tr_1'})
    for tr in award_table_tr:
        th = tr.find('th')
        if th is not None:
            th_name = remove_space(th.text)
            if th_name in mapper:
                key = mapper[th_name][0]
                content = tr.find('td').text
                returned_dic[key] = mapper[th_name][1](content) if len(mapper[th_name]) == 2 else content

    # Print returned_dic
    if logging.getLogger().isEnabledFor(logging.DEBUG):
        for k, v in returned_dic.items():
            logger.debug('{}\t{}'.format(k, v))

    return returned_dic


def get_procurement_info_dic(root_element):
    if root_element is None:
        return None

    returned_dic = {}
    mapper = procurement_info_map
    award_table_tr = root_element.findAll('tr', {'class': 'tender_table_tr_2'})
    for tr in award_table_tr:
        th = tr.find('th')
        if th is not None:
            th_name = remove_space(th.text)
            if th_name in mapper:
                key = mapper[th_name][0]
                content = tr.find('td').text
                returned_dic[key] = mapper[th_name][1](content) if len(mapper[th_name]) == 2 else content
                continue

            # Special case
            if th_name == '是否適用條約或協定之採購':
                content = remove_space(tr.find('td').text)
                m_str = r'.*\(GPA\)：(?P<gpa>[是否]).*\(ANZTEC\)：(?P<anztec>[是否]).*\(ASTEP\)：(?P<astep>[是否]).*'
                m = re.match(m_str, content)
                if m is not None:
                    returned_dic['is_gpa'] = \
                        yesno_conversion(m.group('gpa')) if m.group('gpa') is not None else content
                    returned_dic['is_anztec'] = \
                        yesno_conversion(m.group('anztec')) if m.group('anztec') is not None else content
                    returned_dic['is_astep'] = \
                        yesno_conversion(m.group('astep')) if m.group('astep') is not None else content

    # Print returned_dic
    if logging.getLogger().isEnabledFor(logging.DEBUG):
        for k, v in returned_dic.items():
            logger.debug('{}\t{}'.format(k, v))

    return returned_dic


def get_declaration_info_dic(root_element):
    if root_element is None:
        return None

    returned_dic = {}
    mapper = declaration_info_map
    award_table_tr = root_element.findAll('tr', {'class': 'tender_table_tr_3'})
    for tr in award_table_tr:
        th = tr.find('th')
        if th is not None:
            th_name = remove_space(th.text)
            if th_name in mapper:
                key = mapper[th_name][0]
                content = tr.find('td').text
                returned_dic[key] = mapper[th_name][1](content) if len(mapper[th_name]) == 2 else content

    # Print returned_dic
    if logging.getLogger().isEnabledFor(logging.DEBUG):
        for k, v in returned_dic.items():
            logger.debug('{}\t{}'.format(k, v))

    return returned_dic


def get_attend_info_dic(root_element):
    if root_element is None:
        return None

    returned_dic = {}
    mapper = attend_info_map
    award_table_tr = root_element.findAll('tr', {'class': 'tender_table_tr_4'})
    for tr in award_table_tr:
        th = tr.find('th')
        if th is not None:
            th_name = remove_space(th.text)
            if th_name in mapper:
                key = mapper[th_name][0]
                content = tr.find('td').text
                returned_dic[key] = mapper[th_name][1](content) if len(mapper[th_name]) == 2 else content

    # Print returned_dic
    if logging.getLogger().isEnabledFor(logging.DEBUG):
        for k, v in returned_dic.items():
            logger.debug('{}\t{}'.format(k, v))

    return returned_dic


def get_other_info_dic(root_element):
    if root_element is None:
        return None

    returned_dic = {}
    mapper = other_info_map
    award_table_tr = root_element.findAll('tr', {'class': 'tender_table_tr_5'})
    for tr in award_table_tr:
        th = tr.find('th')
        if th is not None:
            th_name = remove_space(th.text)
            if th_name in mapper:
                key = mapper[th_name][0]
                content = tr.find('td').text
                returned_dic[key] = mapper[th_name][1](content) if len(mapper[th_name]) == 2 else content

    # Print returned_dic
    if logging.getLogger().isEnabledFor(logging.DEBUG):
        for k, v in returned_dic.items():
            logger.debug('{}\t{}'.format(k, v))

    return returned_dic


def parse_args():
    p = OptionParser()
    p.add_option('-f', '--filename', action='store',
                 dest='filename', type='string', default='')
    return p.parse_args()


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

    options, remainder = parse_args()

    file_name = options.filename.strip()
    if not os.path.isfile(file_name):
        logger.error('File not found: ' + file_name)
        quit(_ERRCODE_FILENAME)

    primary_key, root_element = init(file_name)

    get_organization_info_dic(root_element)
    get_procurement_info_dic(root_element)
    get_declaration_info_dic(root_element)
    get_attend_info_dic(root_element)
    get_other_info_dic(root_element)
