import scrapy
import logging
from scrapy.utils.log import configure_logging
from scrapy import Item, Field
import datetime 
from news_collector.items import NewsCollectorItem
from scrapy.mail import MailSender
from scrapy import signals
from pydispatch import dispatcher

class SpiegelSpider(scrapy.Spider):
    name = "spiegel"
    total_parsed = 0
    urls_parsed = []

    configure_logging(install_root_handler=False)
    logging.basicConfig(
        filename=f'{name}_{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.log',
        format='%(levelname)s: %(message)s',
        level=logging.INFO
    )

    def __init__(self):
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
        logging.info(f'total parsed: {self.total_parsed}')

    def start_requests(self):
        allowed_domains = ['www.spiegel.de/']
        urls = [
            "https://www.spiegel.de/"
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def start_requests2(self):
        allowed_domains = ['www.spiegel.de/']
        urls = [
            #'https://www.spiegel.de/politik/deutschland/corona-und-die-gesellschaft-zersplitterte-normalitaet-a-0efb9a97-7cbb-442e-b25e-fdaa95bf7874'

            # noch zu testen: (siehe todos)
            # 'https://www.spiegel.de/politik/ausland/oesterreich-sebastian-kurz-regiert-mit-den-gruenen-in-wien-a-1303414.html'
        ]

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parseArticle)

    def parse(self, response):
        main_section = response.css(
            'html body main section[data-area="block>topic"]')

        for article in main_section.xpath('.//article'):
            href = article.css('header a::attr(href)').get()

            yield response.follow(href, callback=self.parseArticle)

    def parseArticle(self, response):
        url = response.request.url

        if not self.isAccessible(response, url):
            return

        category = url.split('/')[3] # bad style...

        if category == 'video':
            logging.debug(f'not parsing, video: {url}')
            return

        self.total_parsed += 1
        logging.debug(f"{self.total_parsed}. {url}")

        article = response.xpath('//html/body/div/div/div/main/article')

        #create item and add values
        article_item = NewsCollectorItem()
        article_item['raw'] = response.body.decode('utf-8')
        article_item['date'] = article.css('header time.timeformat::attr(datetime)').get()
        article_item['url'] = url
        article_item['authors'] = [a.strip('\n') for a in article.xpath('//header/div/div/div[2]/a/text()').extract()]
        article_item['agency'] = self.name
        # teaser could be empty
        article_item['teaser'] = article.css('header div div div.RichText::text').get().strip('\n') if article.css('header div div div.RichText::text').get() is not None else '__unknown__'
        # sometimes kicker is inside h1, but mostly inside h2
        # sometimes only one div is used for the kicker: https://www.spiegel.de/gesundheit/diagnose/coronavirus-kinder-nicht-mehr-zu-oma-und-opa-bringen-wie-schuetze-ich-gefaehrdete-personen-a-57989487-5608-4a4d-ac40-52d01ffe0233
        article_item['kicker'] = article.xpath('//header/div/div/*[self::h1 or self::h2]/span[1]/text()').get().strip('\n') if article.xpath('//header/div/div/*[self::h1 or self::h2]/span[1]/text()').get() is not None else '__unknown__'
        #see kicker (only one div instead of two)
        article_item['headline'] = article.xpath('//header/div/div/*[self::h1 or self::h2]/span[2]/span/text()').get().strip('\n') if article.xpath('//header/div/div/*[self::h1 or self::h2]/span[2]/span/text()').get() is not None else '__unknown__'
        article_item['named_references'] = {}
        article_item['text'] = ""
        article_item['category'] = category

        text_divs = [x for x in article.xpath(
            './/div/section[contains(@class, "relative")]/div[contains(@class, "clearfix")]/div') if len(x.css('::attr(data-advertisement)')) == 0]
        for div in text_divs:
            content = div.css('::text')
            links = div.css('a')
            for c in content:
                c = c.get().strip('\n')

                if c is not '' and c != 'icon: der spiegel':  # spiegel texts end with S - icon
                    article_item['text'] += c
            for l in links:
                href = l.css('::attr(href)').get()
                
                # dot´s are not allowed in mongodb key names
                # sometimes there are hidden hyperlinks without any text
                article_item['named_references'][l.css('::text').get().strip('\n').replace(
                    '.', '%2E') if l.css('::text').get() is not None else f'unknown_{href.replace(".", "%2E")}'] = href


        for x in article_item['named_references']:
            # print("now parsing: x: " + x + " and link is: " + article_item['named_references'][x])
            ref_url = article_item['named_references'][x]
            if ref_url.startswith('https://www.spiegel.de/'):
                yield response.follow(article_item['named_references'][x], callback=self.parseArticle)

        yield article_item


    def isAccessible(self, response, url):
        if self.total_parsed >= 100:
            return False

        if url in self.urls_parsed:
            logging.debug(f"{url} already parsed")
            return False
        else:
            self.urls_parsed.append(url)

        if not url.startswith('https://www.spiegel.de/'):
            # currently no support for other newspages
            logging.debug(f"not parsing, other newspage: {url}")
            return False
        
        if url.startswith('https://www.spiegel.de/backstage') or url.startswith('https://www.spiegel.de/extras'):
            #backstage and extra are spiegel pages where no news content exists
            logging.debug(f'backstage with: {url}')
            return False

        if len(response.xpath('//div[@data-component="Paywall"]')) != 0:
            # we dont want paywalls --> spiegel+
            logging.debug(f"spiegel+ content: {url}")
            return False

        if len(response.css('section[data-area=article-teaser-list]')) != 0:
            # we dont want spiegel-themes --> e.g. https://www.spiegel.de/thema/...
            logging.debug("not parsing, theme")
            return False

        return True