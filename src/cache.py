import json
import logging
import fakeredis

logger = logging.getLogger(__name__)


class MovieCache:
    def __init__(self):
        self.client = fakeredis.FakeRedis(decode_responses=True)


    def make_key(self, limit):
        return f"movies:limit:{limit}"


    def get(self, limit):
        """Return the cached response dictionary, or None."""

        key = self.make_key(limit)
        cached_data = self.client.get(key)
        if cached_data is not None:
            logger.debug(f"Cache HIT: {key}")
            return json.loads(cached_data)
        else:
            logger.debug(f"Cache MISS: {key}")
            return None


    def set(self, limit, response):
        """Cache the response dictionary for 90 seconds."""
       
        key = self.make_key(limit)
        response_dict = json.dumps(response)
        self.client.setex(key, 90, response_dict)


    def invalidate(self):
        """Remove all cached movie retrievals."""
        
        self.client.flushdb()
        logger.debug("Cached movie retrievals cleared")