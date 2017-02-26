from bs4 import BeautifulSoup
from couchpotato.core.helpers.variable import getTitle, tryInt
from couchpotato.core.logger import CPLog
from couchpotato.core.helpers.encoding import simplifyString, tryUrlencode
from couchpotato.core.media._base.providers.torrent.base import TorrentProvider
import cookielib
import re
import traceback
import urllib
import urllib2
import unicodedata
from couchpotato.core.helpers import namer_check
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

log = CPLog(__name__)


class Base(TorrentProvider):
    urls = {
        'site': 'http://www.torrent9.biz/',
        'search': 'http://www.torrent9.biz/search_torrent/',
    }

    def _search(self, movie, quality, results):
        #for title in movie['info']['titles']:
        #    try:
                TitleStringReal = (getTitle(movie['info']) + ' ' + simplifyString(quality['identifier'] )).replace('-',' ').replace(' ',' ').replace(' ',' ').replace(' ',' ').encode("utf-8")

                URL = ((self.urls['search'])+TitleStringReal.replace('.', '-').replace(' ', '-')+'.html,trie-seeds-d').encode('utf-8')

                req = urllib2.Request(URL, headers={'User-Agent' : "Mozilla/5.0"} )
                log.info('opening url %s', URL)
                data = urllib2.urlopen(req,timeout=10)

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
                                log.info('found title %s',title)

                                testname=namer_check.correctName(title.lower(),movie)
                                if testname==0:
                                    continue

                                tmp = result.find("a")['href'].split('/')[-1].replace('.html', '.torrent').strip()
                                download_url = (self.urls['site'] + 'get_torrent/{0}'.format(tmp) + ".torrent")
                                detail_url = (self.urls['site'] + 'torrent/{0}'.format(tmp))

                                if not all([title, download_url]):
                                    continue

                                seeders = int(result.find(class_="seed_ok").get_text(strip=True))
                                leechers = int(result.find_all('td')[3].get_text(strip=True))
                                size = result.find_all('td')[1].get_text(strip=True)
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
        return True

    def download(self, url = '', nzb_id = ''):
        log.debug('download %s',url)
        req = urllib2.Request(url, headers={'User-Agent' : "Mozilla/5.0"} )
        try:
            return urllib2.urlopen(req).read()
        except:
            log.error('Failed downloading from %s: %s', (self.getName(), traceback.format_exc()))

    loginDownload = download

config = [{
    'name': 'torrent9',
    'groups': [
        {
            'tab': 'searcher',
            'list': 'torrent_providers',
            'name': 'torrent9',
            'description': 'See <a href="http://www.torrent9.biz/">Torrent9</a>',
            'icon': 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAIGNIUk0AAHolAACAgwAA+f8AAIDpAAB1MAAA6mAAADqYAAAXb5JfxUYAAAKCSURBVHjafNPdS1NhAMfxg1hiUoYpIhqaL53Nuuiim+iim6CL/AMieqV0qelSp25HhTRcmduc73M7EyUtUwILyxSRDMM0jOwi7cJKzElZrs6oMN2+XRgsQvfA9/bD88DzE0RJdiXobMqeQpsSX9DsT9esJBXalKRiu6IqcSqiJG+US1BLMqPTH5hfcjM9/4mX7xZ49d7F7OIXFpbc5N8eIizLiijJGyaoJVlZ9vxgs2PsGyM43bQZoAiiJCsHrrYRkVvP9b4xAFxuDwfL2xElmX1lraQYHIGB2IJmhFNGDD1PAJj/+p3YvCZ2ZFlJ1jtI0tsJy7QSnG5m5+U6UgwO1CVOPyBKMlszzJT3jgKwsKyglmTiC21E5zUSrW2g7N4IXeNvONPygPBsK4l6O6oSZ2Bg15VG4vIaGZmew7e6ytu5RQBMD8cI0VjY+/8NKu4/A2Dxmwe1JCOcq8L06DkAR4ydCCcqMPdPAHC06g5R2kY/EHShGnP/OAC+tbV14GQlfVOzrK78Rjh7A+H8TUI1FsBH7eMJQjQWPxCT30SatYf6wRcU3R1GJcmEaCxobw0CcK13lGS9HW3HIPi8WAcm2JJh9gP7y1qJyW8i6KKJbZk1iJJMssFBZG49tqHJ9ae5Pcx8/IzX68XQPUzopRo/sFGppU4SiloITjehLm0lPKeO7PYBAI5beojUNgQGUgwOVJLMseouREkmzdLN2uoaA69nCdXUkKJ3BAYSi+1E5dTRNznDz18r4PPS9nSK7dlW4gqaUf/9BwQqsdjOocoOTtsecNjYSXh2LXE6G6mlzvUxiZLs2mSqiijJirrEqezW2ZSI3HolJr9JSTY4/p23688AdGGN9hQwll4AAAAASUVORK5CYII=',
            'wizard': True,
            'options': [
                {
                    'name': 'enabled',
                    'type': 'enabler',
                    'default': False,
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
                    'default': 10,
                    'description': 'Starting score for each release found via this provider.',
                }
            ],
        },
    ],
}]
