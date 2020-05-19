import scrapy.utils.log as logger

class MyTopLevelFormatter(logger.TopLevelFormatter):
    def __init__(self, loggers=None, name=None):
        super(MyTopLevelFormatter, self).__init__()
        self.loggers = loggers or []
        self.name = name

    def filter(self, record):
        if self.name in record.name:
            return True
        if hasattr(record, 'spider'):
            if record.spider.name == self.name:
                return True
            record.name = record.spider.name + "." + record.name
        elif hasattr(record, 'crawler') and hasattr(record.crawler, 'spidercls'):
            if record.crawler.spidercls.name == self.name:
                return True
            record.name = record.crawler.spidercls.name + "." + record.name
        elif any(record.name.startswith(l + '.') for l in self.loggers):
            record.name = record.name.split('.', 1)[0]
        return False