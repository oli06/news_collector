import scrapy
import logging
import datetime
from news_collector.items import NewsCollectorItem
import news_collector.spiders.base_spider as bs

class ZeitSpider(bs.BaseSpider):
    name = "golem"

    def __init__(self):
        super().__init__(self.name, 200, "https://www.golem.de/", [])

    def start_requests2(self):
        urls = [
            "https://www.golem.de/"
        ]

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def start_requests(self):
        urls = [
            
            'https://www.golem.de/news/kopie-von-rainbow-six-siege-ubisoft-verklagt-apple-und-google-2005-148533.html'
            #'https://www.golem.de/news/bill-gates-corona-verschwoerungstheorien-im-mainstream-2005-148408.html'#pagination
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
        article = response.css('article')
        url = response.request.url        
        if not self.isAccessible(response, url):
            return

        self.total_parsed += 1
        logging.debug(f"{self.total_parsed}. {url}")

        # create item and add values
        article_item = NewsCollectorItem()
        article_item['raw'] = response.body.decode('utf-8')
        article_item['headline'] = article.css('header h1 span.dh1::text').get()
        article_item['kicker'] = article.css('header h1 span.dh2::text').get()
        article_item['category'] = '' #golem does not use categories
        article_item['authors'] = []
        article_item['named_references'] = {}
        article_item['text'] = ""
        article_item['date'] = article.css('header div.authors time.authors__pubdate::attr(datetime)').get()
        article_item['url'] = url
        article_item['agency'] = self.name
        article_item['tags'] = article.css('div.tags ul.tags__list li a::text').extract()
        #teaser could contain a-tag
        article_item['teaser'] = ""
        teaser = article.css("header p")
        for p in teaser:
            nodes = p.xpath('.//node()')
            for node in nodes:
                node_text = node.css('::text').get()
                node_name = node.xpath('name()').get()
                if node_name == 'a':
                    a_text = node.css('::text').get().strip('\n').strip().replace('.', '%2E')
                    article_item['named_references'][a_text] = node.xpath('@href').get()
                else: 
                    article_item['teaser'] += node.get().strip('\n')

        authors = article.css(
            'header div.authors span.authors__name a::text')
        for a in authors:
            article_item['authors'].append(a.get().strip('\n'))

        extract_text_request = scrapy.Request(url, callback=self.pagination)
        extract_text_request.meta['article'] = article_item
        yield extract_text_request

    def pagination(self, response):
        article_item = response.meta['article']

        body = response.css('article div.formatted')

        text, named_ref = self.extract_text_and_named_references(body)
        if article_item['text'] == '':
            article_item['text'] = text
            article_item['named_references'] = named_ref
        else:
            article_item['text'] += text
            article_item['named_references'].update(named_ref)
        
        #get next page
        next_page = response.css('article table td.text1 a::attr(href)').get()
        if next_page is None or next_page == '': #next page does not exist
            print('last page')
            for x in article_item['named_references']:
                ref_url = article_item['named_references'][x]
                yield response.follow(article_item['named_references'][x], callback=self.parseArticle)
            yield article_item
        else:
            print('else')
            if not next_page.startswith('https://www.golem.de'):
                next_page = 'https://www.golem.de' + next_page
            next_page_request = scrapy.Request(next_page, callback=self.pagination)
            next_page_request.meta['article'] = article_item
            yield next_page_request
            print("reaching?")

    def extract_text_and_named_references(self, body_selector):
        #select all elements without class="ad-container"
        article_text = ""
        named_references = {}
        text = body_selector.xpath('./node()')
    
        for t in text: 
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
                    article_text += node.get().strip().strip("\n").strip('<br>')

        return article_text, named_references


    def isAccessible(self, response, url):
        if not url.startswith('https://www.golem.de/news'):
            # currently no support for other newspages
            logging.debug('not parsing, other newspage or subpage ' + url)
            return False

        return super().isAccessible(response, url)
