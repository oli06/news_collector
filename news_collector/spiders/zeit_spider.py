import scrapy
import logging
from scrapy.utils.log import configure_logging 
import datetime
from news_collector.items import NewsCollectorItem
from scrapy import signals
from pydispatch import dispatcher


class NtvSpider(scrapy.Spider):
    name = "zeit"
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

    def start_requests2s(self):
        urls = [
            "https://www.zeit.de/"
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def start_requests(self):
        urls = [
            'https://www.zeit.de/wirtschaft/2020-05/steuerschaetzung-corona-krise-finanzierung-regierung-wirtschaftshilfen'
            #https://www.zeit.de/wirtschaft/2020-04/rezession-coronavirus-wirtschaftskrise-konsumklima-gfk #text contains <a tags>
            #https://www.zeit.de/2020/20/konjunkturprogramme-abwrackpraemie-corona-checks-konsumgutscheine #text contains other things than text..
        ]

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parseArticle)

    def parse(self, response):
        content = response.xpath(
            '//body/div[@class="metawrapper"]/div[@class="container sitewrapper"]/div[@class="row "]/div')

        top_news = content.xpath(
            '//div[@class="content "]/section[@class="group"]/article')  # NACHRICHTEN

        for article in top_news:
            content = article.xpath('.//div[@class="teaser__content"]')
            href = content.css('div.teaser__content a::attr(href)').get()

            yield response.follow(href, callback=self.parseArticle)

    def parseArticle(self, response):
        article = response.css('article.article')
        url = response.request.url
        category = url.split('/')[3]

        if not self.isAccessible(response, url):
            return

        self.total_parsed += 1
        logging.debug(f"{self.total_parsed}. {url}")

        header = article.css('header.article-header')
        body = article.css('div.article-body')
        footer = article.css('div.article-footer')

        #create item and add values
        article_item = NewsCollectorItem()
        article_item['tags'] = footer.css('nav.article-tags ul.article-tags__list li a::text').extract() #what if there is no link or no tags :: TODO
        article_item['kicker'] = header.css('h1.article-heading span.article-heading__kicker::text').get().strip('\n')
        article_item['headline'] = header.css('h1.article-heading span.article-heading__title::text').get().strip('\n')
        article_item['teaser'] = header.css("div.article__item div.summary::text").get().strip('\n').strip()
        article_item['date'] = header.css('div.article__item div.metadata time::attr(datetime)').get()
        article_item['url'] = url
        article_item['agency'] = self.name
        article_item['category'] = category        
        
        text = body.xpath('./div[@class="article-page"]/*[not(@class="ad-container")]') #select all elements without class="ad-container"
        article_item['named_references'] = {}
        article_item['text'] = ""

        for t in text:  # the first paragraph is the teaser
            nodes = t.xpath('.//node()')
            article_item['text'] += " " #space between every paragraph
            for node in nodes:
                if node.xpath('name()').get() == 'a':
                    # save reference link in named_references and dont save the link to the text blocks
                    href = node.xpath('@href').get()
                    article_item['named_references'][node.xpath('text()').get().strip('\n').replace('.', '%2E') if node.xpath('text()').get(
                    ) is not None else 'unknown_' + href.replace('.', '%2E')] = href  # dot´s are not allowed in mongodb key names
                    # sometimes there are hidden hyperlinks without any text
                else:
                    article_item['text'] += node.get().strip("\n").strip('<br>')

        article_item['text'] = article_item['text'].strip()

        for x in article_item['named_references']:
            ref_url = article_item['named_references'][x]
            
            yield response.follow(article_item['named_references'][x], callback=self.parseArticle)

        #TODO auswerten
        article_item['author'] = header.css(
            'div.article__item div.byline span a span::text').get() #what if there are two authors? 
        
        yield article_item


    def isAccessible(self, response, url):
        if self.total_parsed >= 150:
            #print("done, max reached")
            logging.debug('max reached')
            return False

        if not url.startswith('https://www.zeit.de/'):
            # currently no support for other newspages
            logging.debug('not parsing, other newspage ' + url)
            return False

        if url in self.urls_parsed:
            logging.debug(url + " already parsed")
            return False
        else:
            self.urls_parsed.append(url)

        return True