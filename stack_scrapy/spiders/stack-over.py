import scrapy
from bs4 import BeautifulSoup  # Install with: pip install beautifulsoup4

class StackOverSpider(scrapy.Spider):
    name = "stack"

    def start_requests(self):
        urls = [
            "https://stackoverflow.com/questions?tab=frequent&pagesize=50"
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):

        for q in response.css('div.s-post-summary'):
            votes = q.css('div.s-post-summary--stats-item__emphasized span.s-post-summary--stats-item-number::text').get()
            answers = q.css('div.s-post-summary--stats-item:nth-child(2) span.s-post-summary--stats-item-number::text').get()
            views = q.css('div.s-post-summary--stats-item:nth-child(3) span.s-post-summary--stats-item-number::text').get()
            main_title = q.css('div.s-post-summary--content h3.s-post-summary--content-title a.s-link::text').get()
            link = response.urljoin(q.css('div.s-post-summary--content h3.s-post-summary--content-title a.s-link::attr(href)').get())
            tags = q.css('div.s-post-summary--meta li.js-post-tag-list-item a.s-tag::text').getall()

            if link:
                yield response.follow(link, self.parse_detail, meta={
                    'votes': votes,
                    'answers': answers,
                    'views': views,
                    'title': main_title,
                    'tags': tags,
                    'link': link
                })

        next_page = response.css('div.s-pagination.float-left a.s-pagination--item::attr(href)').get()
        if next_page:
            next_page_url = response.urljoin(next_page)
            yield response.follow(next_page_url, callback=self.parse)

    def parse_detail(self, response):
        data_list  = []
        viewed_time = ''.join(response.css('div[title^="Viewed"]::text').getall()).strip()
        question_score = response.css('div.question::attr(data-score)').get()
        questions = ''.join(response.css("div.question.js-question p::text").getall())
        answers_div = response.css('div.answer.js-answer')
        for answer in answers_div:
            ans_dict = {}
            verified = 'No'
            score = answer.css('div.js-vote-count::attr(data-value)').get()
            answers = answer.css('div.js-post-body p::text').getall()
            answers = self.clean_html(' '.join(answers))

            if answer.css('div.accepted-answer'):
                verified = 'Yes'

            ans_dict['answers'] = answers
            ans_dict['score'] = score
            ans_dict['Verified'] = verified
            data_list.append(ans_dict)

        try:
            yield {
            "link": response.meta['link'],
            "title": response.meta['title'],
            "questions": questions,
            "votes": response.meta['votes'],
            "answers_count": response.meta['answers'],
            "views": response.meta['views'],
            "tags": response.meta['tags'],
            "viewed_time": viewed_time.strip() if viewed_time else None,
            "question_score": question_score,
            "ans_dict": data_list
        }

        except Exception as e:
            self.logger.error(f"Error parsing {response.url}: {e}")


    @staticmethod
    def clean_html(html_content):
        """
        Remove HTML tags and return plain text.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        for a_tag in soup.find_all('a'):
            a_tag.decompose()  # Removes the <a> tag completely
        strong_text = ' '.join(strong.get_text(strip=True) for strong in soup.find_all('strong'))
        plain_text = soup.get_text(separator=' ', strip=True)
        return plain_text