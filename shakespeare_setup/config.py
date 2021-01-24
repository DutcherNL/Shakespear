class SetupConfig:
    name = None
    url_keyword = None
    namespace = None

    def get_urls(self):
        """ Builds a list of urls """
        raise NotImplementedError

    @property
    def urls(self):
        return self.get_urls(), None, None
