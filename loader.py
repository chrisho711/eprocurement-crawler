#!/usr/bin/python
#  -*- coding: utf-8 -*-
""" Loader for Taiwan government e-procurement website"""

import os
import logging
import six
import mysql.connector
import extractor as et
from datetime import datetime, date
from mysql.connector import errorcode
from optparse import OptionParser

__author__ = "Yu-chun Huang"
__version__ = "1.0.0b"

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

db_connection = None


def connect_db():
    db_config = {'user': 'procurement',
                 'password': 'procurement',
                 'host': 'localhost',
                 'database': 'TW_PROCUREMENT'
                 }
    try:
        global db_connection
        db_connection = mysql.connector.connect(**db_config)
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            logger.error("Something is wrong with your user name or password.")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            logger.error("Database does not exist")
        else:
            logger.error(err)


def close_db():
    if db_connection is not None:
        db_connection.close()


def gen_insert_sql(table, data_dict):
    sql_template = u'INSERT INTO {} ({}) VALUES ({}) ON DUPLICATE KEY UPDATE {}'
    columns = ''
    values = ''
    dup_update = ''

    for k, v in data_dict.iteritems():
        if v is not None:
            if values != '':
                columns += ','
                values += ','
                dup_update += ','

            columns += k

            if isinstance(v, six.string_types):
                vstr = '"' + v + '"'
            elif isinstance(v, bool):
                vstr = '1' if v else '0'
            elif isinstance(v, datetime) or isinstance(v, date):
                vstr = '"' + str(v) + '"'
            else:
                vstr = str(v)

            values += vstr
            dup_update += k + '=' + vstr

    sql_str = sql_template.format(table, columns, values, dup_update)
    logger.debug(sql_str)
    return sql_str


def load(cnx, file_name):
    if not et.init(file_name):
        logger.error('Fail to extract data from file: ' + file_name)
        return

    cur = cnx.cursor(buffered=True)

    pk = et.get_primary_key()

    data = et.get_organization_info_dic()
    data.update(pk)
    cur.execute(gen_insert_sql('organization_info', data))

    data = et.get_procurement_info_dic()
    data.update(pk)
    cur.execute(gen_insert_sql('procurement_info', data))

    data = et.get_tender_info_dic()
    for tender in data.values():
        tender.update(pk)
        cur.execute(gen_insert_sql('tender_info', tender))

    data = et.get_tender_award_item_dic()
    for item in data.values():
        for tender in item.values():
            tender.update(pk)
            cur.execute(gen_insert_sql('tender_award_item', tender))

    et.get_evaluation_committee_info_list()
    et.get_award_info_dic()

    cnx.commit()


def parse_args():
    p = OptionParser()
    p.add_option('-f', '--filename', action='store',
                 dest='filename', type='string', default='')
    p.add_option('-d', '--directory', action='store',
                 dest='directory', type='string', default='')
    return p.parse_args()


if __name__ == '__main__':
    options, remainder = parse_args()

    connect_db()

    f = options.filename.strip()
    if f != '' and not os.path.isfile(f):
        logger.error('File not found: ' + f)
    else:
        load(db_connection, f)

    d = options.directory.strip()
    if d != '' and not os.path.isdir(d):
        logger.error('Directory not found: ' + d)

    close_db()
    print 'done'
