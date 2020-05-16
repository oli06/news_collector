import scrapy
import logging
from scrapy.utils.log import configure_logging
import datetime
from news_collector.items import NewsCollectorItem
from scrapy import signals
from pydispatch import dispatcher


class ZeitSpider(scrapy.Spider):
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

    def start_requests(self):
        urls = [
            "https://www.zeit.de/index"
        ]

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def start_requests2(self):
        urls = [
            # 'https://www.zeit.de/wissen/gesundheit/coronavirus-echtzeit-karte-deutschland-landkreise-infektionen-ausbreitung'
            #'https://www.zeit.de/sport/2020-05/bundesliga-start-fussball-spiele-coronavirus-manager-fans' # pagination test
        
        ]
        allowed_domains = [
            'https://www.zeit.de/'
        ]

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parseArticle)

    def parse(self, response):
        main = response.css('main.main')
        article_divs = main.xpath('.//div[not(@class="ad-container")][contains(@class, "cp-region")]')

        
        for div in article_divs[:3]: #only crawl the first few articles in the first 3 sections. remove these constraints to crawl many articles
            for article in div.css('article a::attr(href)'):
                yield response.follow(article, callback=self.parseArticle)

    def parseArticle(self, response):
        article = response.css('article.article')
        url = response.request.url
        category = url.split('/')[3]

        if not self.isAccessible(response, url):
            return

        self.total_parsed += 1
        logging.debug(f"{self.total_parsed}. {url}")

        body = article.css('div.article-body')
        footer = article.css('div.article-footer')

        # create item and add values
        article_item = NewsCollectorItem()
        article_item['raw'] = response.body.decode('utf-8')
        # what if there is no link or no tags :: TODO
        article_item['tags'] = footer.css('nav.article-tags ul.article-tags__list li a::text').extract()
        article_item['kicker'] = article.xpath('.//h1[contains(@class, "article-heading") or contains(@class, "heading__headline")]/span[contains(@class, "article-heading")]/text()').get().strip('\n').strip()
        article_item['headline'] = article.xpath('.//h1[contains(@class, "article-heading") or contains(@class, "heading__headline")]/span[contains(@class, "article-heading__title")]/text()').get().strip('\n')
        article_item['teaser'] = article.css("div.article__item div.summary::text").get().strip('\n').strip()
        article_item['date'] = article.css('div.article__item div.metadata time::attr(datetime)').get()
        article_item['url'] = url
        article_item['agency'] = self.name
        article_item['category'] = category
        article_item['authors'] = []

        # select all elements without class="ad-container"
        text = body.xpath(
            './div[@class="article-page"]/*[not(@class="ad-container")]')
        article_item['named_references'] = {}
        article_item['text'] = ""

        for t in text:  # the first paragraph is the teaser
            nodes = t.xpath('.//node()')
            article_item['text'] += " "  # space between every paragraph
            t_name = t.xpath('name()').get()
            if t_name is not 'p' and t_name is not 'h1' and t_name is not 'h2':
                # there are other tags the crawler cant process: div, aside, script
                continue

            for node in nodes:
                node_text = node.css('::text').get()
                node_name = node.xpath('name()').get()
                if node_name == 'a':
                    # save reference link in named_references and dont save the link to the text blocks
                    href = node.xpath('@href').get()
                    article_item['named_references'][node.xpath('text()').get().strip('\n').replace('.', '%2E') if node.xpath('text()').get(
                    ) is not None else 'unknown_' + href.replace('.', '%2E')] = href  # dot´s are not allowed in mongodb key names
                    # sometimes there are hidden hyperlinks without any text
                elif node_text is not None:  # spans (used for a tags text)
                    continue
                else:  # if ::text is None, it is already pure text
                    article_item['text'] += node.get().strip("\n").strip('<br>')

        article_item['text'] = article_item['text'].strip()

        for x in article_item['named_references']:
            ref_url = article_item['named_references'][x]

            yield response.follow(article_item['named_references'][x], callback=self.parseArticle)

        # TODO auswerten
        authors = article.css(
            'div.article__item div.byline span a span::text')  # what if there are two authors?
        for a in authors:
            article_item['authors'].append(a.get().strip('\n'))

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

        if len(response.xpath('.//div[contains(@class, "liveblog")]')) > 0:
            # currently no support for liveblogs, e.g. https://www.zeit.de/politik/deutschland/2020-03/thueringen-ministerpraesidentenwahl-bodo-ramelow-bjoern-hoecke-live
            logging.debug(f'not parsing, liveblog {url}')
            return

        if len(response.css('aside.zplus-badge')) > 0 or len(response.css('span.zplus-badge__text')) > 0:
            #z+ content, e.g.https://www.zeit.de/arbeit/2020-05/hausarbeit-maenner-homeoffice-familie-coronavirus
            logging.debug(f'not parsing, z+ content {url}')
            return False

        if url.startswith('https://www.zeit.de/thema'):
            logging.debug('not parsing, theme ' + url)
            return False

        if url.startswith('https://www.zeit.de/autoren'):
            logging.debug('not parsing, authors page ' + url)
            return False

        if url in self.urls_parsed:
            logging.debug(url + " already parsed")
            return False
        else:
            self.urls_parsed.append(url)

        return True
        