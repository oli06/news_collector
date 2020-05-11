import scrapy
import logging
import datetime
logging.basicConfig(
    filename=f'tagesschau_{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.log',
    format='%(levelname)s: %(message)s',
    level=logging.INFO
)

from scrapy.utils.log import configure_logging 

from news_collector.items import NewsCollectorItem
from scrapy import signals
from pydispatch import dispatcher


class TagesschauSpider(scrapy.Spider):
    name = "tagesschau"
    total_parsed = 0
    urls_parsed = []

    configure_logging(install_root_handler=False)

    def __init__(self):
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
        logging.info(f'total parsed: {self.total_parsed}')
        

    def start_requests(self):
        urls = [
            "https://www.tagesschau.de/"
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def start_requests2(self):
        urls = [
            'https://www.tagesschau.de/wirtschaft/coronavirus-fleischbetrieb-103.html'
        ]

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parseArticle)

    def parse(self, response):
        for section in response.css('div.sectionA'): #first article is tagesthemen video
            for a in section.css('div.con div.modCon div.modA div.boxCon div.box div.teaser div.mediaCon a.mediaLink'):
                yield response.follow(a, callback=self.parseArticle)
                
        
            

    def parseArticle(self, response):
        url = response.request.url
        category = url.split('/')[3]

        if category == 'newsticker':
            #currently not parsing newsticker
            logging.debug(f'newsticker not parsing: {url}')
            return

        if not self.isAccessible(response, url):
            return

        self.total_parsed += 1
        logging.debug(f"{self.total_parsed}. {url}")

        article = response.css('div.storywrapper')
        header = article.css('div.sectionA')
        content = article.css('div.sectionZ')

        #create item and add values
        article_item = NewsCollectorItem()
        article_item['headline'] = header.css('div.meldungHead span.headline::text').get().strip('\n').strip()
        article_item['kicker'] = header.css('div.meldungHead span.dachzeile::text').get().strip('\n').strip()
        article_item['date'] = header.css('div.meldungHead p.text span.stand::text').get().strip('\n').replace('Stand:', '').strip()
        article_item['agency'] = self.name
        article_item['url'] = url
        article_item['category'] = category
        article_item['is_update'] = False
        article_item['named_references'] = {}
        article_item['text'] = ""
        article_item['teaser'] = ""
        article_item['tags'] = []

        text_div = content.css('div.con div.modCon div.modParagraph')
        for tag in text_div:
            nodes = tag.xpath('./node()')
            nodes_name = nodes.xpath('name()').get()
            if nodes_name == 'div':
                #divs contain other resources, advertisement, etc
                #while text is in p-tags
                continue

            for node in nodes:
                #some <p> are used for other things than text
                class_attributes = node.xpath('@class').get()
                if class_attributes is not None and 'autorenzeile' in class_attributes:
                    #tagesschau doesnt use authors very well, therefore we dont rely on this data
                    #e.g. https://www.tagesschau.de/ausland/belarus-militaerparade-105.html
                    continue

                child_nodes = node.xpath('./node()')                
                for c in child_nodes:
                    #print("before")
                    node_name = c.xpath('name()').get()
                    #print("after")
                    if node_name == 'a':
                        href = c.xpath('@href').get() #relative href
                        article_item['named_references'][c.xpath('text()').get().strip('\n').replace('.', '%2E') if c.xpath('text()').get() is not None else 'unknown_' + href.replace('.', '%2E')] = href
                        print(href)
                        #yield response.follow(href, callback=self.parseArticle)
                    elif node_name == None:
                        article_item['text'] += c.get().strip('\n')
                    elif node_name == 'h2': #subtitle
                        article_item['text'] += c.get().strip('\n')
                    elif node_name == 'strong':
                        article_item['teaser'] += c.css('::text').get().strip('\n')

        for x in article_item['named_references']:
            # print("now parsing: x: " + x + " and link is: " + article_item['named_references'][x])
            ref_url = article_item['named_references'][x]
            
            yield response.follow(article_item['named_references'][x], callback=self.parseArticle)

        article_item['text'] = article_item['text'].strip()

        yield article_item


    def isAccessible(self, response, url):
        if self.total_parsed >= 150:
            #print("done, max reached")
            logging.debug('max reached')
            return False

        if not url.startswith('https://www.tagesschau.de/'):
            # currently no support for other newspages
            logging.debug('not parsing, other newspage ' + url)
            return False

        if url.startswith('https://www.tagesschau.de/multimedia'):
            logging.debug('not parsing, multimedia ' + url)
            return False

        if url in self.urls_parsed:
            logging.debug(url + " already parsed")
            return False
        else:
            self.urls_parsed.append(url)

        return True