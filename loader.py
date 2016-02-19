#!/usr/bin/python
#  -*- coding: utf-8 -*-
""" Loader for Taiwan government e-procurement website"""

import os
import logging
import mysql.connector
import extractor as et
from datetime import datetime, date
from mysql.connector import errorcode
from optparse import OptionParser

__author__ = "Yu-chun Huang"
__version__ = "1.0.0b"

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

trantab = str.maketrans(
    {'\'': '\\\'',
     '\"': '\\\"',
     '\b': '\\b',
     '\n': '\\n',
     '\r': '\\r',
     '\t': '\\t',
     '\\': '\\\\',})


def gen_insert_sql(table, data_dict):
    sql_template = u'INSERT INTO {} ({}) VALUES ({}) ON DUPLICATE KEY UPDATE {}'
    columns = ''
    values = ''
    dup_update = ''

    for k, v in data_dict.items():
        if v is not None:
            if values != '':
                columns += ','
                values += ','
                dup_update += ','

            columns += k

            if isinstance(v, str):
                vstr = '\'' + v.translate(trantab) + '\''
            elif isinstance(v, bool):
                vstr = '1' if v else '0'
            elif isinstance(v, datetime) or isinstance(v, date):
                vstr = '\'' + str(v) + '\''
            else:
                vstr = str(v)

            values += vstr
            dup_update += k + '=' + vstr

    sql_str = sql_template.format(table, columns, values, dup_update)
    logger.debug(sql_str)
    return sql_str


def load(cnx, file_name):
    pk_atm_main, tender_case_no, root_element = et.init(file_name)
    if root_element is None \
            or pk_atm_main is None or tender_case_no is None \
            or pk_atm_main == '' or tender_case_no == '':
        logger.error('Fail to extract data from file: ' + file_name)
        return

    pk = {'pk_atm_main': pk_atm_main, 'tender_case_no': tender_case_no}
    logger.info('Updating database (pkAtmMain: {}, tenderCaseNo: {})'.format(pk_atm_main, tender_case_no))

    try:
        cur = cnx.cursor(buffered=True)

        data = et.get_organization_info_dic(root_element)
        data.update(pk)
        cur.execute(gen_insert_sql('organization_info', data))

        data = et.get_procurement_info_dic(root_element)
        data.update(pk)
        cur.execute(gen_insert_sql('procurement_info', data))

        data = et.get_tender_info_dic(root_element)
        for tender in data.values():
            tender.update(pk)
            cur.execute(gen_insert_sql('tender_info', tender))

        data = et.get_tender_award_item_dic(root_element)
        for item in data.values():
            for tender in item.values():
                tender.update(pk)
                cur.execute(gen_insert_sql('tender_award_item', tender))

        data = et.get_evaluation_committee_info_list(root_element)
        for committee in data:
            committee.update(pk)
            cur.execute(gen_insert_sql('evaluation_committee_info', committee))

        data = et.get_award_info_dic(root_element)
        data.update(pk)
        cur.execute(gen_insert_sql('award_info', data))

        cnx.commit()
    except mysql.connector.Error as err:
        logger.warn('Fail to update database (pkAtmMain: {}, tenderCaseNo: {})\n\t{}'.format(pk_atm_main,
                                                                                             tender_case_no,
                                                                                             err))


def parse_args():
    p = OptionParser()
    p.add_option('-f', '--filename', action='store',
                 dest='filename', type='string', default='')
    p.add_option('-d', '--directory', action='store',
                 dest='directory', type='string', default='')
    p.add_option('-u', '--user', action='store',
                 dest='user', type='string', default='')
    p.add_option('-p', '--password', action='store',
                 dest='password', type='string', default='')
    p.add_option('-i', '--host', action='store',
                 dest='host', type='string', default='')
    p.add_option('-b', '--database', action='store',
                 dest='database', type='string', default='')
    return p.parse_args()


if __name__ == '__main__':
    options, remainder = parse_args()

    user = options.user.strip()
    password = options.password.strip()
    host = options.host.strip()
    database = options.database.strip()
    if user == '' or password == '' or host == '' or database == '':
        logger.error('Database connection information is incomplete.')
        quit()

    db_config = {'user': user,
                 'password': password,
                 'host': host,
                 'database': database
                 }
    try:
        db_connection = mysql.connector.connect(**db_config)
        db_connection.autocommit = False

        f = options.filename.strip()
        if f != '':
            if not os.path.isfile(f):
                logger.error('File not found: ' + f)
            else:
                load(db_connection, f)

        d = options.directory.strip()
        if d != '':
            if not os.path.isdir(d):
                logger.error('Directory not found: ' + d)
            else:
                for root, dirs, files in os.walk(d):
                    for f in files:
                        load(db_connection, os.path.join(root, f))
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            logger.error("Something is wrong with your user name or password.")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            logger.error("Database does not exist.")
        else:
            logger.error(err)
    else:
        db_connection.close()
