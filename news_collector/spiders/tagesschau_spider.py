
import scrapy
import logging
import datetime
from news_collector.items import NewsCollectorItem
import news_collector.spiders.base_spider as bs


class TagesschauSpider(bs.BaseSpider):
    name = "tagesschau"

    def __init__(self):
        super().__init__(self.name, 500, "https://www.tagesschau.de/", ['multimedia', '100sekunden', 'regional', 'thema'])

    def start_requests(self):
        urls = [
            "https://www.tagesschau.de/"
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def start_requests2(self):
        urls = [
            'https://www.tagesschau.de/inland/bundeskabinett-klimaschutzgesetz-101.html'
        ]

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parseArticle)

    def parse(self, response):
        for section in response.css("div.container div.teasergroup"):
            for a in section.css('a'):
                yield response.follow(a, callback=self.parseArticle)

    def parseArticle(self, response):
        url = response.request.url
        category = url.split('/')[3]

        if category == 'newsticker':
            #currently not parsing newsticker
            logging.debug(f'newsticker not parsing: {url}')
            return

        if not self.can_process(response, url):
            return

        self.total_parsed += 1
        logging.info(f"{self.total_parsed}. {url}")

        article = response.css('article.container')
        header = article.css('div.meldungskopf')
        content = article

        #create item and add values
        article_item = NewsCollectorItem()
        article_item['raw'] = response.body.decode('utf-8')
        # article_item['headline'] = header.css('div.meldungskopf__title span.meldungskopf__headline--text::text').get().strip('\n').strip()

        article_item["headline"] = ""
        for span in header.xpath('//span[@class="meldungskopf__headline--text"]//text()'):
            if(span):
                article_item["headline"] += span.get()

        article_item["headline"] = article_item["headline"].strip('\n').strip()

        article_item['kicker'] = header.css('div.meldungskopf__title span.meldungskopf__topline::text').get().strip('\n').strip()
        article_item['date'] = header.css('div.meldungskopf__title p.meldungskopf__datetime::text').get().strip('\n').replace('Stand:', '').strip()
        article_item['agency'] = self.name
        article_item['url'] = url
        article_item['category'] = category
        article_item['is_update'] = False
        article_item['named_references'] = {}
        article_item['text'] = ""
        article_item['teaser'] = ""
        
        article_item['tags'] = []
        for tag in content.css("div.meldungsfooter ul.taglist li.taglist__element a::text"):
            article_item['tags'].append(tag.get())
        
        article_item["subheadlines"] = []
        for subtitle in content.css("h2.meldung__subhead::text"):
            article_item["subheadlines"].append(subtitle.get())
        
        #every tag holding text is marked with "textabsatz". Inside these tags we want the whole text (from all children)
        plain_texts = content.xpath('//*[contains(@class, "textabsatz")]//text()')
        for t in plain_texts: 
            article_item['text'] += t.get().strip().strip('\n').strip() + " "

        text_refs = content.xpath('//*[contains(@class, "textabsatz")]/a')
        for ref in text_refs:
            href = ref.xpath("@href").get()
            article_item['named_references'][ref.xpath("text()").get().strip().strip('\n').strip().replace('.', '%2E') if ref.xpath("text()").get() is not None else 'unknown_' + href.replace('.', '%2E')] = href

        for x in article_item['named_references']:
            # print("now parsing: x: " + x + " and link is: " + article_item['named_references'][x])
            ref_url = article_item['named_references'][x]
            
            yield response.follow(article_item['named_references'][x], callback=self.parseArticle)

        article_item['text'] = article_item['text'].strip()

        yield article_item