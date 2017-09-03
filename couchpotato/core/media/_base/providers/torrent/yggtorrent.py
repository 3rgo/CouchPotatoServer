import traceback
import urlparse
import urllib
import re
import unicodedata
import cookielib
import urllib2
from datetime import datetime
from bs4 import BeautifulSoup
from couchpotato.core.helpers import namer_check
from couchpotato.core.helpers.encoding import toUnicode, simplifyString, tryUrlencode
from couchpotato.core.helpers.variable import getTitle, tryInt
from couchpotato.core.logger import CPLog
from couchpotato.core.media._base.providers.torrent.base import TorrentProvider
from StringIO import StringIO
import gzip
import re

log = CPLog(__name__)


class Base(TorrentProvider):
    urls = {
        'download': 'https://yggtorrent.com/engine/download_torrent?id=',
        'search': 'https://yggtorrent.com/engine/search?q=',
    }

    http_time_between_calls = 1 #seconds
    cat_backup_id = None
    cj = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

    def _search(self, movie, quality, results):
                info = movie['info']
                if(movie['originalName'] == True):
                            info = movie
                TitleStringReal = (getTitle(info) + " "+ simplifyString(quality['identifier'])).replace('-','+').replace(' ','+').replace(' ','+').replace(' ','+').encode("utf-8")

                URL = ((self.urls['search'])+TitleStringReal.replace('.', '-').replace(' ', '-')).encode('utf-8')

                req = urllib2.Request(URL, headers={'User-Agent' : "Mozilla/5.0"} )
                log.info('opening url %s', URL)
                data = urllib2.urlopen(req,timeout=500)

                id = 1000

                if data:
                    try:
                        html = BeautifulSoup(data)
                        torrent_rows = html.findAll('tr')

                        for result in torrent_rows:
                            try:
                                if not result.find('a'):
                                    continue

                                title = result.find('a').get_text(strip=False)


                                if simplifyString(quality['identifier']) not in title.lower():
                                    continue

                                testname=namer_check.correctName(title.lower(),movie)
                                if testname==0:
                                    continue

                                log.info('found title %s', title)
                                tmp = result.find("a")['href'].split('/film/')[1].split('-')[0]
                                download_url = (self.urls['download'] + tmp)
                                detail_url = result.find("a")['href']

                                if not all([title, download_url]):
                                    continue
                                allTd = html.findAll('td')
                                seeders = int(allTd[4].get_text(strip=True))
                                leechers = int(allTd[5].get_text(strip=True))
                                size = allTd[3].get_text(strip=True)
                                size = size.lower()
                                size = size.replace("go", "gb")
                                size = size.replace("mo", "mb")
                                size = size.replace("ko", "kb")
                                size=size.replace(' ','')
                                size=self.parseSize(str(size))

                                def extra_check(item):
                                    return True

                                new={}
                                new['id'] = id
                                new['name'] = title.strip()
                                new['url'] = download_url
                                new['detail_url'] = detail_url
                                new['size'] = size
                                new['seeders'] = seeders
                                new['leechers'] = leechers
                                new['extra_check'] = extra_check
                                new['download'] = self.loginDownload
                                id = id + 1
                                results.append(new)
                            except StandardError, e:
                                log.info('boum %s',e)
                    except AttributeError:
                        log.debug('No search results found.')
                else:
                    log.debug('No search results found.')
            #except:
            #    continue
        #return

    def login(self):

        self.opener.addheaders = [
            ('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko)'),
            ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
            ('Accept-Language', 'en-US,en;q=0.8'),
            ('Accept-Charset', 'ISO-8859-1,utf-8;q=0.7,*;q=0.7'),
            ('Keep-Alive', '115'),
            ('Connection', 'keep-alive'),
            ('Cache-Control', 'max-age=0'),
        ]

        data = urllib.urlencode({'id': self.conf('username'), 'pass': self.conf('password'), 'submit': ''})

        r = self.opener.open('https://yggtorrent.com/user/login?', data)

        for index, cookie in enumerate(self.cj):
            if (cookie.name == "ci_session"): login_done = True

        if not login_done:
            log.error('Login to yggtorrent failed')
            return False

        content= r.read()

        if login_done and self.loginSuccess(content):
            log.debug('Login HTTP yggtorrent status 200; seems successful')
            self.last_login_check = self.opener
            return True

    def loginDownload(self, url='', nzb_id=''):
        if not self.login():
            return
        try:
            request = urllib2.Request(url)

            response = self.last_login_check.open(request)
            # unzip if needed
            if response.info().get('Content-Encoding') == 'gzip':
                buf = StringIO(response.read())
                f = gzip.GzipFile(fileobj=buf)
                data = f.read()
                f.close()
            else:
                data = response.read()
            response.close()
            return data
        except:
            return 'try_next'

    def loginSuccess(self, output):
        return  output == ''

    loginCheckSuccess = loginSuccess


config = [{
    'name': 'yggtorrent',
    'groups': [
        {
            'tab': 'searcher',
            'list': 'torrent_providers',
            'name': 'yggtorrent',
            'description': 'See <a href="https://yggtorrent.com">yggtorrent</a>',
            'wizard': True,
            'icon': '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',
            'options': [
                {
                    'name': 'enabled',
                    'type': 'enabler',
                    'default': False,
                },
                {
                    'name': 'username',
                    'default': '',
                },
                {
                    'name': 'password',
                    'default': '',
                    'type': 'password',
                },
                {
                    'name': 'seed_ratio',
                    'label': 'Seed ratio',
                    'type': 'float',
                    'default': 1,
                    'description': 'Will not be (re)moved until this seed ratio is met.',
                },
                {
                    'name': 'seed_time',
                    'label': 'Seed time',
                    'type': 'int',
                    'default': 40,
                    'description': 'Will not be (re)moved until this seed time (in hours) is met.',
                },
                {
                    'name': 'extra_score',
                    'advanced': True,
                    'label': 'Extra Score',
                    'type': 'int',
                    'default': 20,
                    'description': 'Starting score for each release found via this provider.',
                }
            ],
        },
    ],
}]
