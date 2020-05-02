import scrapy

class NewsSpider(scrapy.Spider):
    name = "news"

    def start_requests(self):
        #allowed_domains = ['https://www.n-tv.de/']
        urls = [
            "https://www.n-tv.de/"
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def start_requests_news_page(self):
        urls = [
            'https://www.n-tv.de/politik/Sachsen-Anhalt-lockert-Kontaktbeschraenkungen-article21754435.html'
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
        #print("parse article")
        article = response.xpath('//article[@class="article"]')

        if len(article) == 0:  # there a webpages that are not news articles
            return

        article_wrapper = article.css('div.article__wrapper')
        header = article_wrapper.css('div.article__header')

        text = article_wrapper.xpath('.//div[@class="article__text"]/p')
        named_references = {}
        article_text_blocks = []
        block_index = 0
        for t in text[1:]:  # the first paragraph is normally the teaser_text
            nodes = t.xpath('.//node()')
            article_text_blocks.append([])
            for node in nodes:
                if node.xpath('name()').get() == 'a':
                    # save reference link in named_references and dont save the link to the text blocks
                    href = node.xpath('@href').get()
                    if not href.endswith(".html"):
                        continue
                    named_references[node.xpath('text()').get()] = href

                    yield response.follow(node, callback=self.parseArticle)
                else:
                    article_text_blocks[block_index].append(
                        node.get().strip().lower())

            block_index += 1

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
            a_copy = a.lower()
            if a_copy.startswith('von'):
                a_copy = a_copy[3:].strip()

            author_names = [a.strip() for a in a_copy.split('und')]
            authors.extend(author_names)
            authors.remove(a)

        yield {
            'date': header.css('span.article__date::text').get(),
            'url': response.request.url,
            'teaser': text[0].css("p strong::text").get().strip().lower(),
            'author': authors,
            'is_update': True if header.css(
                'span.article__kicker span:nth-child(1)::text').get() == "Update" else False,  # does not work currently
            'kicker': header.css('span.article__kicker::text').get().strip().lower(),
            'headline': header.css('span.article__headline::text').get().lower(),
            'named_references': named_references,
            'text_segments': article_text_blocks,
            'category': article.css('span.title::text').get().lower(),
            'tags': article_wrapper.css(
                'section.article__tags ul li a::text').getall()
        }
