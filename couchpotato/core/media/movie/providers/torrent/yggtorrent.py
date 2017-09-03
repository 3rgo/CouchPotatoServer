from couchpotato.core.logger import CPLog
from couchpotato.core.media._base.providers.torrent.yggtorrent import Base
from couchpotato.core.media.movie.providers.base import MovieProvider

log = CPLog(__name__)

autoload = 'yggtorrent'

class yggtorrent(MovieProvider, Base):
    pass
