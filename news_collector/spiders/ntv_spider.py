import scrapy
import logging
from scrapy.utils.log import configure_logging 
import datetime
from news_collector.items import NewsCollectorItem

class NtvSpider(scrapy.Spider):
    name = "n-tv"
    total_parsed = 0
    urls_parsed = []

    configure_logging(install_root_handler=False)
    logging.basicConfig(
        filename=f'n-tv_{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.log',
        format='%(levelname)s: %(message)s',
        level=logging.INFO
    )

    def start_requests(self):
        urls = [
            "https://www.n-tv.de/"
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def start_requests2(self):
        urls = [
            'https://www.n-tv.de/ratgeber/Freiwillige-Beitraege-fuer-die-Rente-article17244951.html'
        ]

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parseArticle)

    def parse(self, response):
        # n-tv.de
        content = response.xpath(
            '//body/div[@class="metawrapper"]/div[@class="container sitewrapper"]/div[@class="row "]/div')

        top_news = content.xpath(
            '//div[@class="content "]/section[@class="group"]/article')  # NACHRICHTEN

        for article in top_news:
            content = article.xpath('.//div[@class="teaser__content"]')
            href = content.css('div.teaser__content a::attr(href)').get()

            yield response.follow(href, callback=self.parseArticle)

    def parseArticle(self, response):
        article = response.xpath('//article[@class="article"]')
        url = response.request.url

        if not self.isAccessible(response, url):
            return

        if len(article) == 0:  # there a webpages that are not news articles
            logging.debug(f"not a news article: {url}")
            return

        self.total_parsed += 1
        logging.debug(f"{self.total_parsed}. {url}")

        article_wrapper = article.css('div.article__wrapper')
        header = article_wrapper.css('div.article__header')
        text = article_wrapper.xpath('.//div[@class="article__text"]/p')

        #create item and add values
        article_item = NewsCollectorItem()
        article_item['date'] = header.css('span.article__date::text').get()
        article_item['url'] = url
        article_item['agency'] = 'n-tv'
        # n-tv interviews use <em> tags for the teaser instead of bold tags. And sometimes there is even no (!) teaser... -> https://www.n-tv.de/wissen/Die-Eisheiligen-kommen-zu-fuenft-article21759625.html
        article_item['teaser'] = text[0].css("p strong::text").get().strip('\n') if text[0].css("p strong::text").get() is not None else text[0].css("p em::text").get().strip('\n') if text[0].css('p em::text').get() is not None else ''
        article_item['is_update'] = True if header.css(
                'span.article__kicker span:nth-child(1)::text').get() == "Update" else False # does not work
        article_item['kicker'] = header.css('span.article__kicker::text').get().strip('\n')
        article_item['headline'] = header.css('span.article__headline::text').get().strip('\n')
        article_item['category'] = article.css('span.title::text').get()
        # old articles dont have tags
        article_item['tags'] = article_wrapper.css(
                'section.article__tags ul li a::text').getall() if article_wrapper.css('section.article__tags ul li a::text') is not None else []  
        article_item['named_references'] = {}
        article_item['text'] = ""

        for t in text[1:]:  # the first paragraph is the teaser
            nodes = t.xpath('.//node()')
            article_item['text'] += " " #space between every paragraph
            for node in nodes:
                if node.xpath('name()').get() == 'a':
                    # save reference link in named_references and dont save the link to the text blocks
                    href = node.xpath('@href').get()
                    if not href.endswith(".html"):
                        continue
                    article_item['named_references'][node.xpath('text()').get().strip('\n').replace('.', '%2E') if node.xpath('text()').get(
                    ) is not None else 'unknown_' + href.replace('.', '%2E')] = href  # dot´s are not allowed in mongodb key names
                    # sometimes there are hidden hyperlinks without any text

                    yield response.follow(node, callback=self.parseArticle)
                else:

                    article_item['text'] += node.get().strip("\n")

        article_item['text'] = article_item['text'].strip()

        authors = header.css(
            'span.article__author::text').getall()
        if len(authors) == 0:
            # maybe it´s a newer styling, where the author is linked with a <a> tag
            # maybe there´s no author
            author_name = header.css('span.article__author a::text').get()
            if author_name is not None:
                authors.append(author_name.strip())

        for a in authors:
            # e.g. "Von Max Maier und Sabine Braun" -> ["Max Maier", "Sabine Braun"]
            a_copy = a
            if a_copy.startswith('von'):
                a_copy = a_copy[3:].strip()

            author_names = [a.strip() for a in a_copy.split('und')]
            authors.extend(author_names)
            authors.remove(a)

        article_item['author'] = authors
        yield article_item


    def isAccessible(self, response, url):
        if self.total_parsed >= 150:
            #print("done, max reached")
            logging.debug('max reached')
            return False

        if not url.startswith('https://www.n-tv.de/'):
            # currently no support for other newspages
            logging.debug('not parsing, other newspage ' + url)
            return False

        if url.startswith('https://www.n-tv.de/mediathek'):
            # currently no support for videos / audio
            logging.debug('not parsing, mediathek ' + url)
            return False

        if url in self.urls_parsed:
            logging.debug(url + " already parsed")
            return False
        else:
            self.urls_parsed.append(url)

        return True