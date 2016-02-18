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

is_init_ok = False
pk_atm_main = None
tender_case_no = None
root_element = None


def get_root_element(file_name):
    f = open(file_name, 'r')
    response_text = f.read()
    f.close()
    soup = BeautifulSoup(''.join(response_text), 'lxml')
    tender_table = soup.find('table', {'class': 'table_block tender_table'})
    return tender_table


def init(file_name):
    global is_init_ok
    global root_element
    global pk_atm_main
    global tender_case_no

    f = open(file_name, 'r')
    response_text = f.read()
    f.close()
    soup = BeautifulSoup(''.join(response_text), 'lxml')
    pk_atm_main = soup.find('div', {'class': 'pkAtmMain'}).text
    tender_case_no = soup.find('div', {'class': 'tenderCaseNo'}).text
    root_element = soup.find('table', {'class': 'table_block tender_table'})
    logger.debug('pkAtmMain: ' + pk_atm_main)
    logger.debug('tenderCaseNo: ' + tender_case_no)
    if root_element is None or \
                    pk_atm_main is None or tender_case_no is None or \
                    pk_atm_main.strip() == '' or tender_case_no.strip() == '':
        is_init_ok = False
    else:
        is_init_ok = True

    return is_init_ok


def get_primary_key():
    return {'pk_atm_main': pk_atm_main, 'tender_case_no': tender_case_no}


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
    return int(element.strip())


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


def tel_conversion(element):
    m = re.match(r'(\((?P<area>\d+)\))?\s*(?P<number>\d+)', element.strip())
    return m.group('area') + '-' + m.group('number') if m.group('area') is not None else m.group('number')


organization_info_map = {
    # <tr class="award_table_tr_1">
    '機關代碼': ('org_id', remove_space),
    '機關名稱': ('org_name', remove_space),
    '單位名稱': ('unit_name', remove_space),
    '機關地址': ('org_address', remove_space),
    '聯絡人': ('contact', strip),
    '聯絡電話': ('tel', tel_conversion),
    '傳真號碼': ('fax', tel_conversion)}

procurement_info_map = {
    # <tr class="award_table_tr_2">
    '標案案號': ('tender_case_no', remove_space),
    '招標方式': ('procurement_type', remove_space),
    '決標方式': ('awarding_type', remove_space),
    '是否依政府採購法施行細則第64條之2辦理': ('is_follow_law_64_2', yesno_conversion),
    '新增公告傳輸次數': ('num_transmit', int_conversion),
    '公告更正序號': ('revision_sn', remove_space),
    '是否依據採購法第106條第1項第1款辦理': ('is_follow_law_106_1_1', yesno_conversion),
    '標案名稱': ('subject_of_procurement', remove_space),
    '決標資料類別': ('attr_of_awarding', remove_space),
    '是否屬共同供應契約採購': ('is_inter_entity_supply_contract', yesno_conversion),
    '是否屬二以上機關之聯合採購(不適用共同供應契約規定)': ('is_joint_procurement', yesno_conversion),
    '是否複數決標': ('is_multiple_award', yesno_conversion),
    '是否共同投標': ('is_joint_tender', yesno_conversion),
    '標的分類': ('attr_of_procurement', unescape_conversion),
    '是否屬統包': ('is_design_build_contract', yesno_conversion),
    '是否應依公共工程專業技師簽證規則實施技師簽證': ('is_engineer_certification_required', yesno_conversion),
    '開標時間': ('opening_date', date_conversion),
    '原公告日期': ('original_publication_date', date_conversion),
    '採購金額級距': ('procurement_money_amount_level', remove_space),
    '辦理方式': ('conduct_procurement', remove_space),
    '限制性招標依據之法條': ('restricted_tendering_law', remove_space),
    '是否適用WTO政府採購協定(GPA)：': ('is_gpa',),  # Special processing required
    '是否適用臺紐經濟合作協定(ANZTEC)：': ('is_anztec',),  # Special processing required
    '是否適用臺星經濟夥伴協定(ASTEP)：': ('is_astep',),  # Special processing required
    '預算金額是否公開': ('is_budget_amount_public', yesno_conversion),
    '預算金額': ('budget_amount', money_conversion),
    '是否受機關補助': ('is_org_subsidy', yesno_conversion),
    '履約地點': ('fulfill_location', strip),
    '履約地點（含地區）': ('fulfill_location_district', strip),
    '是否含特別預算': ('is_special_budget', yesno_conversion),
    '歸屬計畫類別': ('project_type', remove_space),
    '本案採購契約是否採用主管機關訂定之範本': ('is_authorities_template', yesno_conversion)}

tender_map = {
    # <tr class="award_table_tr_3">
    '廠商流水號': ('tender_sn',),  # Special processing required
    '廠商代碼': ('tenderer_id', strip),
    '廠商名稱': ('tenderer_name', strip),
    '廠商名稱(英)': ('tenderer_name_eng', strip),
    '是否得標': ('is_awarded', yesno_conversion),
    '組織型態': ('organization_type', remove_space),
    '廠商業別': ('industry_type', remove_space),
    '廠商地址': ('address', strip),
    '廠商地址(英)': ('address_eng', strip),
    '廠商電話': ('tel', tel_conversion),
    '決標金額': ('award_price', money_conversion),
    '得標廠商國別': ('country', strip),
    '是否為中小企業': ('is_sm_enterprise', yesno_conversion),
    '履約起日': ('fulfill_date_start', date_conversion),  # Special processing required
    '履約迄日': ('fulfill_date_end', date_conversion),  # Special processing required
    '雇用員工總人數是否超過100人': ('is_employee_over_100', yesno_conversion),
    '僱用員工總人數': ('num_employee', int_conversion),
    '已僱用原住民人數': ('num_aboriginal', int_conversion),
    '已僱用身心障礙者人數': ('num_disability', int_conversion)}

tender_award_item_map = {
    # <tr class="award_table_tr_4">
    '品項流水號': ('item_sn',),  # Special processing required
    '廠商流水號': ('tender_sn',),  # Special processing required
    '品項名稱': ('item_name', strip),
    '單位': ('unit', remove_space),
    '是否以單價及預估需求數量之乘積決定最低標': ('is_unit_price_x_qty_lowest', yesno_conversion),
    '得標廠商': ('awarded_tenderer', strip),
    '預估需求數量': ('request_number', int_conversion),
    '決標金額': ('award_price', money_conversion),
    '底價金額': ('base_price', money_conversion),
    '原產地國別': ('source_country', strip),  # Special processing required
    '原產地國別得標金額': ('source_award_price', money_conversion)  # Special processing required
}

evaluation_committee_info_map = {
    # <tr class="award_table_tr_4_1"> <td id="mat_venderArguTd">
    '項次': ('sn',),  # Special processing required
    '出席會議': ('is_attend',),  # Special processing required
    '姓名': ('name',),  # Special processing required
    '職業': ('occupation',)  # Special processing required
}

award_info_map = {
    # <tr class="award_table_tr_6">
    '決標公告序號': ('award_announce_sn', remove_space),
    '公告更正序號': ('revision_sn', remove_space),
    '決標日期': ('awarding_date', date_conversion),
    '原決標公告日期': ('original_awarding_announce_date', date_conversion),
    '決標公告日期': ('awarding_announce_date', date_conversion),
    '是否刊登公報': ('is_post_bulletin', yesno_conversion),
    '底價金額': ('base_price', money_conversion),
    '底價金額是否公開': ('is_base_price_public', yesno_conversion),
    '總決標金額': ('total_award_price', money_conversion),
    '總決標金額是否公開': ('is_total_award_price_public', yesno_conversion),
    '契約是否訂有依物價指數調整價金規定': ('is_price_dynamic_with_cpi', yesno_conversion),
    '未列物價調整規定說明': ('no_price_dynamic_description', remove_space),
    '履約執行機關代碼': ('fulfill_execution_org_id',),  # Special processing required
    '履約執行機關名稱': ('fulfill_execution_org_name',),  # Special processing required
    '附加說明': ('additional_info', strip)}


def get_organization_info_dic():
    if not is_init_ok:
        return None

    returned_dic = {}
    mapper = organization_info_map
    award_table_tr = root_element.findAll('tr', {'class': 'award_table_tr_1'})
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


def get_procurement_info_dic():
    if not is_init_ok:
        return None

    returned_dic = {}
    mapper = procurement_info_map
    award_table_tr = root_element.findAll('tr', {'class': 'award_table_tr_2'})
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


def get_tender_info_dic():
    if not is_init_ok:
        return None

    returned_dic = {}
    mapper = tender_map
    award_table_tr = root_element.findAll('tr', {'class': 'award_table_tr_3'})
    for tr in award_table_tr:
        tb = tr.find('table')
        grp_num = 0
        if tb is not None:
            for r in tb.findAll('tr'):
                th_name = remove_space(r.find('th').text)
                m = re.match(r'投標廠商(\d+)', th_name)
                if m is not None:
                    grp_num = int(m.group(1))
                    returned_dic[grp_num] = {'tender_sn': grp_num}
                else:
                    if th_name in mapper:
                        key = mapper[th_name][0]
                        content = r.find('td').text
                        if len(mapper[th_name]) == 2:
                            returned_dic[grp_num][key] = mapper[th_name][1](content)
                        else:
                            returned_dic[grp_num][key] = content

                    # Special case
                    if th_name == '履約起迄日期':
                        content = remove_space(r.find('td').text)
                        date_range = content.split('－')
                        returned_dic[grp_num]['fulfill_date_start'] = date_conversion(date_range[0])
                        returned_dic[grp_num]['fulfill_date_end'] = date_conversion(date_range[1])

    # Print returned_dic
    if logging.getLogger().isEnabledFor(logging.DEBUG):
        for grp_num in returned_dic:
            for k, v in returned_dic[grp_num].items():
                logger.debug('{}\t{}\t{}'.format(grp_num, k, v))

    return returned_dic


def get_tender_award_item_dic():
    if not is_init_ok:
        return None

    returned_dic = {}
    mapper = tender_award_item_map
    award_table_tr = root_element.findAll('tr', {'class': 'award_table_tr_4'})
    for tr in award_table_tr:
        tb = tr.find('table')
        if tb is not None:
            item_num = 0
            item_name = None
            unit = None
            is_upxql = None
            grp_num = 0
            for r in tb.findAll('tr'):
                if r.find('th') is not None:
                    th_name = remove_space(r.find('th').text)
                    m = re.match(r'第(\d+)品項', th_name)
                    m2 = re.match(r'得標廠商(\d+)', th_name)
                    if m is not None:
                        item_num = int(m.group(1))
                        returned_dic[item_num] = {}
                    elif th_name == '品項名稱':
                        content = r.find('td').text
                        item_name = mapper[th_name][1](content) if len(mapper[th_name]) == 2 else content
                    elif th_name == '單位':
                        content = r.find('td').text
                        if content is not None:
                            unit = mapper[th_name][1](content) if len(mapper[th_name]) == 2 else content
                        else:
                            unit = None
                    elif th_name == '是否以單價及預估需求數量之乘積決定最低標':
                        content = r.find('td').text
                        if content is not None:
                            is_upxql = mapper[th_name][1](content) if len(mapper[th_name]) == 2 else content
                        else:
                            is_upxql = None
                    elif m2 is not None and item_num > 0:
                        grp_num = int(m2.group(1))
                        if grp_num > 0:
                            returned_dic[item_num][grp_num] = {
                                'item_sn': item_num,
                                'tender_sn': grp_num,
                                'item_name': item_name}
                            if unit is not None:
                                returned_dic[item_num][grp_num]['unit'] = unit
                            if is_upxql is not None:
                                returned_dic[item_num][grp_num]['is_unit_price_x_qty_lowest'] = is_upxql
                    elif item_num > 0 and grp_num > 0:
                        if th_name in mapper and th_name != '原產地國別':
                            key = mapper[th_name][0]
                            content = r.find('td').text
                            if len(mapper[th_name]) == 2:
                                returned_dic[item_num][grp_num][key] = mapper[th_name][1](content)
                            else:
                                returned_dic[item_num][grp_num][key] = content

                        # Special case
                        if th_name == '原產地國別':
                            ctable = r.find('table')
                            if ctable is not None:
                                for row in ctable.findAll('tr'):
                                    tds = row.findAll('td')
                                    header = remove_space(tds[0].text)
                                    if header in mapper:
                                        key = mapper[header][0]
                                        content = tds[1].text
                                        if len(mapper[header]) == 2:
                                            returned_dic[item_num][grp_num][key] = mapper[header][1](content)
                                        else:
                                            returned_dic[item_num][grp_num][key] = content

    # Print returned_dic
    if logging.getLogger().isEnabledFor(logging.DEBUG):
        for item_k, item_v in returned_dic.items():
            for tender_k, tender_v in item_v.items():
                for detail_k, detail_v in tender_v.items():
                    logger.debug('Item: {}, tender: {}, {}\t{}'.format(item_k, tender_k, detail_k, detail_v))

    return returned_dic


def get_evaluation_committee_info_list():
    if not is_init_ok:
        return None

    returned_list = []
    mapper = evaluation_committee_info_map
    mat_venderargutd = root_element.find('td', {'id': 'mat_venderArguTd'})
    if mat_venderargutd is not None:
        committee = mat_venderargutd.findAll('td')
        if committee is not None and len(committee) > 0 and len(committee) % 4 == 0:
            for i in range(0, int(len(committee) / 4)):
                rec = {mapper['項次'][0]: int(committee[i * 4].text.strip()),
                       mapper['出席會議'][0]: yesno_conversion(committee[i * 4 + 1].text.strip()),
                       mapper['姓名'][0]: remove_space(committee[i * 4 + 2].text.strip()),
                       mapper['職業'][0]: remove_space(committee[i * 4 + 3].text.strip())}
                returned_list.append(rec)

    # Print returned_dic
    if logging.getLogger().isEnabledFor(logging.DEBUG):
        for c in returned_list:
            for k, v in c.items():
                logger.debug('{}\t{}'.format(k, v))

    return returned_list


def get_award_info_dic():
    if not is_init_ok:
        return None

    returned_dic = {}
    mapper = award_info_map
    award_table_tr = root_element.findAll('tr', {'class': 'award_table_tr_6'})
    for tr in award_table_tr:
        th = tr.find('th')
        if th is not None:
            th_name = remove_space(th.text)
            if th_name in mapper:
                key = mapper[th_name][0]
                content = tr.find('td').text
                returned_dic[key] = mapper[th_name][1](content) if len(mapper[th_name]) == 2 else content

            # Special case
            if th_name == '履約執行機關':
                content = remove_space(tr.find('td').text)
                m_str = r'.*機關代碼：(?P<id>[0-9\.]+).*機關名稱：(?P<name>.+)'
                m = re.match(m_str, content)
                if m is not None:
                    returned_dic['fulfill_execution_org_id'] = \
                        remove_space(m.group('id')) if m.group('id') is not None else content
                    returned_dic['fulfill_execution_org_name'] = \
                        remove_space(m.group('name')) if m.group('name') is not None else content

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
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG)

    options, remainder = parse_args()

    file_name = options.filename.strip()
    if not os.path.isfile(file_name):
        logger.error('File not found: ' + file_name)
        quit(_ERRCODE_FILENAME)

    init(file_name)

    get_organization_info_dic()
    get_procurement_info_dic()
    get_tender_info_dic()
    get_tender_award_item_dic()
    get_evaluation_committee_info_list()
    get_award_info_dic()
