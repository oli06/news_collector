from datetime import datetime
import locale

class ArticlePipeline(object):
    def process_item(self, item, spider):
        for attr in item.keys():
            if attr == 'date':
                if item['agency'] == 'zeit' or item['agency'] == 'golem':
                    #1968-11-29T08:00:00+01:00 isoformat
                    date = datetime.fromisoformat(item[attr])
                elif item['agency'] == 'n-tv':
                    #Sonntag, 24. August 2014
                    date_string = item[attr].split(',')[1]
                    date = getLocalizedMonth(date_string, ' %d. %B %Y', 'de_DE.UTF-8') #de_DE.UTF-8 is the german local for linux ubuntu systems. On Windows it is something like 'deu_deu'
                elif item['agency'] == 'spiegel':
                    #2020-05-07 11:41:32
                    date = datetime.strptime(item[attr], '%Y-%m-%d %H:%M:%S')
                elif item['agency'] == 'tagesschau':
                    #11.05.2020 14:26 Uhr
                    date = datetime.strptime(item[attr], '%d.%m.%Y %H:%M Uhr')
                else:
                    raise NotImplementedError('ArticlePipeline, no date-formatter implemented for this spider')

                item[attr] = date.timestamp()
            elif attr == 'authors':
                item[attr] = [stripString(a) for a in item[attr] if not stripString(a)]
            elif attr == 'raw':
                pass #dont do anything
            elif type(item[attr]) == type(''):
                item[attr] = item[attr].strip().strip('\n').strip()

        return item

#https://stackoverflow.com/questions/17902413/localized-month-name-in-python
def getLocalizedMonth(date_string, format_string, locale_value):
    locale.setlocale(locale.LC_ALL, locale_value)
    date = datetime.strptime(date_string, format_string)
    locale.setlocale(locale.LC_ALL, locale.getdefaultlocale())

    return date

def stripString(s):
    if s.startswith('\n') or s.endswith('\n'):
        return stripString(s.strip('\n'))
    if s.startswith('\t') or s.endswith('\t'):
        return stripString(s.strip('\t'))
    if s.startswith('Von ') or s.startswith('von '):
        return stripString(s[4:])
    if s.startswith('und ') or s.startswith('Und '):
        return stripString(s[4:])

    return s.strip()
        
