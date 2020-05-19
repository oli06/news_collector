import scrapy
import logging
import datetime
from news_collector.items import NewsCollectorItem
import news_collector.spiders.base_spider as bs


class ZeitSpider(bs.BaseSpider):
    name = "zeit"

    def __init__(self):
        super().__init__(self.name, 200, "https://www.zeit.de/", ['thema', 'autoren', 'suche'])

    def start_requests(self):
        urls = [
            "https://www.zeit.de/index"
        ]

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def start_requests2(self):
        urls = [
            'https://www.zeit.de/wissen/gesundheit/coronavirus-echtzeit-karte-deutschland-landkreise-infektionen-ausbreitung'
            #'https://www.zeit.de/sport/2020-05/bundesliga-start-fussball-spiele-coronavirus-manager-fans' # pagination test
        
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
        category = response.css('nav.nav__ressorts ul li a.nav__ressorts-link--current span::text').get()
        if category is None:
            category = url.split('/')[3]

        if not self.isAccessible(response, url):
            return

        self.total_parsed += 1
        logging.debug(f"{self.total_parsed}. {url}")

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
        article_item['named_references'] = {}
        article_item['text'] = ""

        authors = article.css(
            'div.article__item div.byline span a span::text')  # what if there are two authors?
        for a in authors:
            article_item['authors'].append(a.get().strip('\n'))

        extract_text_request = scrapy.Request(url, callback=self.pagination)
        extract_text_request.meta['article'] = article_item
        yield extract_text_request

    def pagination(self, response):
        article_item = response.meta['article']

        body = response.css('article.article div.article-body')

        text, named_ref = self.extract_text_and_named_references(body)
        if article_item['text'] == '':
            article_item['text'] = text
            article_item['named_references'] = named_ref
        else:
            article_item['text'] += text
            article_item['named_references'].update(named_ref)
        
        #get next page
        next_page = body.css('nav.article-pagination a.article-pagination__link::attr(href)').get()
        if next_page is None or next_page == 'https://www.zeit.de/index' or next_page == '': #next page does not exist
            print('last page')
            for x in article_item['named_references']:
                ref_url = article_item['named_references'][x]
                yield response.follow(article_item['named_references'][x], callback=self.parseArticle)
            yield article_item
        else:
            print('else')
            next_page_request = scrapy.Request(next_page, callback=self.pagination)
            next_page_request.meta['article'] = article_item
            yield next_page_request
            print("reaching?")

    def extract_text_and_named_references(self, body_selector):
        #select all elements without class="ad-container"
        article_text = ""
        named_references = {}
        text = body_selector.xpath('./div[@class="article-page"]/*[not(@class="ad-container")]')
    
        for t in text:  # the first paragraph is the teaser
            nodes = t.xpath('.//node()')
            article_text += " "  # space between every paragraph
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
                    # dot´s are not allowed in mongodb key names
                    # sometimes there are hidden hyperlinks without any text
                    named_references[node.xpath('text()').get().strip('\n').replace('.', '%2E') if node.xpath('text()').get() is not None else 'unknown_' + href.replace('.', '%2E')] = href  
                elif node_text is not None:  # spans (used for a tags text)
                    continue
                else:  # if ::text is None, it is already pure text
                    article_text += node.get().strip("\n").strip('<br>')

        return article_text, named_references


    def isAccessible(self, response, url):
        if len(response.xpath('.//div[contains(@class, "liveblog")]')) > 0:
            # currently no support for liveblogs, e.g. https://www.zeit.de/politik/deutschland/2020-03/thueringen-ministerpraesidentenwahl-bodo-ramelow-bjoern-hoecke-live
            logging.debug(f'not parsing, liveblog {url}')
            return

        if len(response.css('aside.zplus-badge')) > 0 or len(response.css('span.zplus-badge__text')) > 0:
            #z+ content, e.g.https://www.zeit.de/arbeit/2020-05/hausarbeit-maenner-homeoffice-familie-coronavirus
            logging.debug(f'not parsing, z+ content {url}')
            return False

        return super().isAccessible(response, url)
