# -*- coding: utf-8 -*-
import requests
import urlparse
import logging
import datetime as dt
from optparse import OptionParser
from bs4 import BeautifulSoup
from math import ceil

_ERRCODE_DATE = 2
_ERROR_CODE_FILENAME = 3

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_args():
    p = OptionParser()
    p.add_option('-s', '--date_start', action='store',
                 dest='date_start', type='string', default='')
    p.add_option('-e', '--date_end', action='store',
                 dest='date_end', type='string', default='')
    p.add_option('-f', '--list_filename', action='store',
                 dest='list_filename', type='string', default='bid_list.txt')
    return p.parse_args()


def ad2roc(date, separator=''):
    roc = str(date.year - 1911)
    roc += separator + '{0:02d}'.format(date.month)
    roc += separator + '{0:02d}'.format(date.day)
    return roc


if __name__ == '__main__':
    options, remainder = parse_args()

    date_range = ('', '')
    if options.date_start.strip() and options.date_end.strip():
        try:
            date_range = (dt.datetime.strptime(options.date_start.strip(), '%Y%m%d').date(),
                          dt.datetime.strptime(options.date_end.strip(), '%Y%m%d').date())
            if date_range[0] > date_range[1]:
                logger.error('Start date must be smaller than or equal to end date.')
                quit(_ERRCODE_DATE)
        except ValueError:
            logger.error('Invalid start/end date.')
            quit(_ERRCODE_DATE)

    logger.info('Start date: %s, End date: %s, List filename: %s',
                date_range[0].strftime('%Y-%m-%d'), date_range[1].strftime('%Y-%m-%d'),
                options.list_filename.strip())

    bid_file = open(options.list_filename.strip(), 'w')

    # Limit maximum search date span to be within 3 months (consider Feb. can has only 28 days)
    max_span = 89
    totalDays = (date_range[1] - date_range[0]).days
    for i in range(0, totalDays / max_span + 1):
        s_date = date_range[0] + dt.timedelta(days=i * (max_span - 1) + i)
        e_date = min(date_range[1], s_date + dt.timedelta(days=max_span - 1))

        logger.info('Searching for bids from %s to %s...',
                    s_date.strftime('%Y-%m-%d'), e_date.strftime('%Y-%m-%d'))

        # Search parameters
        payload = {'method': 'search',
                   'searchMethod': 'true',
                   'searchTarget': 'ATM',
                   'orgName': '',
                   'orgId': '',
                   'hid_1': '1',
                   'tenderName': '',
                   'tenderId': '',
                   'tenderStatus': '4,5,21,29',
                   'tenderWay': '',
                   'awardAnnounceStartDate': ad2roc(s_date, '/'),
                   'awardAnnounceEndDate': ad2roc(e_date, '/'),
                   'radProctrgCate': '',
                   'proctrgCate': '',
                   'tenderRange': '',
                   'minBudget': '',
                   'maxBudget': '',
                   'item': '',
                   'hid_2': '1',
                   'gottenVendorName': '',
                   'gottenVendorId': '',
                   'hid_3': '1',
                   'submitVendorName': '',
                   'submitVendorId': '',
                   'location': '',
                   'priorityCate': '',
                   'isReConstruct': '',
                   'btnQuery': '查詢'}

        rs = requests.session()
        user_post = rs.post('http://web.pcc.gov.tw/tps/pss/tender.do?'
                            'searchMode=common&'
                            'searchType=advance',
                            data=payload)
        response_text = user_post.text.encode('utf8')

        soup = BeautifulSoup(response_text, 'lxml')
        rec_number_element = soup.find('span', {'class': 'T11b'})
        rec_number = int(rec_number_element.text)
        page_number = int(ceil(float(rec_number) / 100))

        logger.info('\tTotal number of bids: %d', rec_number)

        page_format = 'http://web.pcc.gov.tw/tps/pss/tender.do?' \
                      'searchMode=common&' \
                      'searchType=advance&' \
                      'searchTarget=ATM&' \
                      'method=search&' \
                      'isSpdt=&' \
                      'pageIndex=%d'
        for page in range(1, page_number + 1):
            logger.info('\tRetrieving bid URLs... (%d / %d)', min(page * 100, rec_number), rec_number)
            bid_list = rs.get(page_format % page)
            bid_response = bid_list.text.encode('utf8')
            bid_soup = BeautifulSoup(bid_response, 'lxml')
            bid_table = bid_soup.find('div', {'id': 'print_area'})
            bid_rows = bid_table.findAll('tr')[1:-1]
            for bid_row in bid_rows:
                link = [tag['href'] for tag in
                        bid_row.findAll('a', {'href': True})][0]
                link_href = urlparse.urljoin('http://web.pcc.gov.tw/tps/pss/tender.do?'
                                             'searchMode=common&'
                                             'searchType=advance',
                                             link)
                bid_file.write(link_href + '\n')
            bid_file.flush()

    bid_file.close()
    logger.info('All done.')
