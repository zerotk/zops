from zerotk.appliance import Appliance


@Appliance.define
class Caches(Appliance):
    """
    Cache service.
    """

    _caches = {}

    def get(self, cache_name: str, *args) -> str:
        cache_key = tuple(args)
        cache_data = self._caches.setdefault(cache_name, {})
        value = cache_data.get(cache_key, None)
        return cache_key, value

    def set(self, cache_name: str, cache_key: tuple, value: any) -> str:
        cache_data = self._caches.setdefault(cache_name, {})
        cache_data[cache_key] = value
        return cache_key
