# -*- coding: utf-8 -*-
""" Extractor
Some English translation is found in https://www.pcc.gov.tw/epaper/10207/abc.htm"""

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


def yesno_conversion(element):
    m = re.match(ur'.*是.*', element.strip())
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


def phone_conversion(element):
    m = re.match(r'(\((?P<area>\d+)\))?(?P<number>\d+)', element.strip())
    return m.group('area') + '-' + m.group('number') if m.group('area') is not None else m.group('number')


organization_info_map = {
    # <tr class="award_table_tr_1">
    '機關代碼': ('org_id', remove_space),
    '機關名稱': ('org_name', remove_space),
    '單位名稱': ('unit_name', remove_space),
    '機關地址': ('org_address', remove_space),
    '聯絡人': ('contact', strip),
    '聯絡電話': ('phone', phone_conversion),
    '傳真號碼': ('fax', phone_conversion)}

procurement_info_map = {
    # <tr class="award_table_tr_2">
    '標案案號': ('job_number', remove_space),
    '招標方式': ('procurement_type', remove_space),
    '決標方式': ('awarding_type', remove_space),
    '是否依政府採購法施行細則第64條之2辦理': ('is_follow_law_64_2', yesno_conversion),
    '新增公告傳輸次數': ('num_transmit', int_conversion),
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
    '本案採購契約是否採用主管機關訂定之範本': ('is_authorities_template', yesno_conversion),
    'pkAtmMain': ('pkAtmMain', strip)}

tender_award_item_map = {
    '得標廠商': 'awarded_tenderer',
    '預估需求數量': 'request_number',
    '決標金額': 'awarding_value',
    '底價金額': 'base_price'}

tenderer_map = {
    '廠商代碼': 'tenderer_code',
    '廠商名稱': 'tenderer_name',
    '是否得標': 'is_awarded',
    '組織型態': 'organization_type'}

evaluation_committee_info_map = {
    # <tr class="award_table_tr_4_1"> <td id="mat_venderArguTd">
    '評選委員': ('evaluation_committee',)  # Special processing required
}

award_info_map = {
    # <tr class="award_table_tr_6">
    '決標公告序號': ('award_announce_sn', remove_space),
    '決標日期': ('awarding_date', date_conversion),
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


def get_organization_info_dic(element):
    returned_dic = {}
    mapper = organization_info_map
    award_table_tr = element.findAll('tr', {'class': 'award_table_tr_1'})
    for tr in award_table_tr:
        th = tr.find('th')
        if th is not None:
            th_name = remove_space(th.text.encode('utf-8'))
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
            th_name = remove_space(th.text.encode('utf-8'))
            if th_name in mapper:
                key = mapper[th_name][0]
                content = tr.find('td').text
                returned_dic[key] = mapper[th_name][1](content) if len(mapper[th_name]) == 2 else content
                continue

            # Special case
            if th_name == '是否適用條約或協定之採購':
                content = remove_space(tr.find('td').text)
                m_str = ur'.*\(GPA\)：(?P<gpa>[是否]).*\(ANZTEC\)：(?P<anztec>[是否]).*\(ASTEP\)：(?P<astep>[是否]).*'
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
        for k, v in returned_dic.iteritems():
            logger.debug(u'{}\t{}'.format(k, v))

    return returned_dic


def get_evaluation_committee_info_list(element):
    returned_list = []
    mat_venderargutd = element.find('td', {'id': 'mat_venderArguTd'})
    if mat_venderargutd is not None:
        committee = mat_venderargutd.findAll('td')
        if committee is not None and len(committee) > 0 and len(committee) % 4 == 0:
            for i in range(0, len(committee) / 4):
                rec = [int(committee[i * 4].text.strip()),  # 項次
                       yesno_conversion(committee[i * 4 + 1].text.strip()),  # 出席會議
                       remove_space(committee[i * 4 + 2].text.strip()),  # 姓名
                       remove_space(committee[i * 4 + 3].text.strip())  # 職業
                       ]
                returned_list.append(rec)

    # Print returned_dic
    if logging.getLogger().isEnabledFor(logging.DEBUG):
        for c in returned_list:
            logger.debug(u'{}\t{}\t{}\t{}'.format(c[0], c[1], c[2], c[3]))

    return returned_list


def get_award_info_dic(element):
    returned_dic = {}
    mapper = award_info_map
    award_table_tr = element.findAll('tr', {'class': 'award_table_tr_6'})
    for tr in award_table_tr:
        th = tr.find('th')
        if th is not None:
            th_name = remove_space(th.text.encode('utf-8'))
            if th_name in mapper:
                key = mapper[th_name][0]
                content = tr.find('td').text
                returned_dic[key] = mapper[th_name][1](content) if len(mapper[th_name]) == 2 else content

            # Special case
            if th_name == '履約執行機關':
                content = remove_space(tr.find('td').text)
                m_str = ur'.*機關代碼：(?P<id>[0-9\.]+).*機關名稱：(?P<name>.+)'
                m = re.match(m_str, content)
                if m is not None:
                    returned_dic['fulfill_execution_org_id'] = \
                        remove_space(m.group('id')) if m.group('id') is not None else content
                    returned_dic['fulfill_execution_org_name'] = \
                        remove_space(m.group('name')) if m.group('name') is not None else content

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

    response_element = get_response_element(directory + '/' + 'with_committee_51759078_MOTC-IOT-104-IEB048.txt')
    # response_element = get_response_element(directory + '/' + 'many_items_51772417_YL1041215P1.txt')
    # response_element = get_response_element(directory + '/' + '51744761_09.txt')

    get_organization_info_dic(response_element)
    get_procurement_info_dic(response_element)
    get_tenderer_info_dic(response_element)
    get_tender_award_item_dic(response_element)
    get_evaluation_committee_info_list(response_element)
    get_award_info_dic(response_element)
