from datetime import datetime


class ArticlePipeline(object):
    def process_item(self, item, spider):
        for attr in item.keys():
            if attr == 'date':
                if item['agency'] == 'zeit':
                    #1968-11-29T08:00:00+01:00 isoformat
                    date = datetime.fromisoformat(item[attr])
                elif item['agency'] == 'n-tv':
                    #Sonntag, 24. August 2014
                    date_string = item[attr].split(',')[1]
                    date = datetime.strptime(date_string, '%d. %B %Y')
                elif item['agency'] == 'spiegel':
                    #2020-05-07 11:41:32
                    date = datetime.strptime(item[attr], '%Y-%m-%d %H:%M:%S')
                elif item['agency'] == 'tagesschau':
                    #11.05.2020 14:26 Uhr
                    date = datetime.strptime(date_string, '%d.%m.%Y %H:%M Uhr')
                else:
                    raise NotImplementedError('ArticlePipeline, no date-formatter implemented')

                item[attr] = date.timestamp()
            elif attr == 'is_update':
                item[attr] = 1 if item[attr] else 0
            elif attr == 'raw':
                pass
            elif type(item[attr]) == type(''):
                item[attr] = item[attr].strip().strip('\n').strip()

        return item
