from lxml import html
from scrapy import Spider, Request
from scrapy.crawler import CrawlerProcess
from scrapy.http import Response
from scrapy.settings.default_settings import LOG_ENABLED


class GoogleSpider(Spider):
    name = 'google'
    custom_settings = {LOG_ENABLED: False}
    headers = {'Agent-User': 'Mozilla/3.0'}
    params = dict()

    def start_requests(self):
        yield Request(self.start_urls[0], headers=self.headers, callback=self.parse)

    def parse(self, response: Response, **kwargs):
        tree = html.fromstring(response.body)
        results = tree.xpath('//div[@class="ZINbbc xpd O9g5cc uUPGi"]')
        print(results)


        # soup = BeautifulSoup(response.body, 'lxml', from_encoding='ANSI')
        # print(soup.prettify())
        # articles = soup.find_all('div', class_='ZINbbc xpd O9g5cc uUPGi')
        # print(articles)


def search(url: str):
    process = CrawlerProcess()
    process.crawl()

#
#
# def search_(queue: Queue, url: str):
#     try:
#         runner = CrawlerRunner()
#         deferred = runner.crawl(GoogleSpider)
#         deferred.addBoth(lambda _: reactor.stop())
#         reactor.run()
#         queue.put(None)
#     except Exception as e:
#         queue.put(e)
#
#
# def search(keyword: str):
#     url = 'https://google.com/search?q=' + quote(keyword)
#     queue = Queue()
#     p = Process(target=search_, args=(queue, url))
#     p.start()
#     result = queue.get()
#     p.join()
#     if result is not None:
#         raise result
