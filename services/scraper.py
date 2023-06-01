import json
import re

from bs4 import BeautifulSoup
import requests


def scrape(title_id):
    url = f'https://www.imdb.com/title/{title_id}/reviews?spoiler=hide&sort=curated&dir=desc&ratingFilter=0'
    page = requests.get(url)

    soup = BeautifulSoup(page.content, "html.parser")
    lister = soup.find(class_="lister")
    lister_items = lister.find_all("div", class_="lister-item-content")
    reviews = []

    for item in lister_items:
        review = {
            "imdbID": title_id,
            "author": None,
            "rating": None,
            "helpfulness": 0,
            "upvotes": 0,
            "downvotes": 0,
            "title": "",
            "content": "",
            "spoilers": False,
            "submittedOn": "",
        }

        rating_div = item.find("span", class_="rating-other-user-rating")
        if rating_div is not None:
            rating = rating_div.find("span").text
            review['rating'] = int(rating)

        title: str = item.find("a", class_="title").text
        review['title'] = title.strip().replace("\n", "")

        author_span = item.find("span", class_="display-name-link")
        author = author_span.find("a").text
        review['author'] = author

        submitted_on = item.find("span", class_="review-date").text
        review['submittedOn'] = submitted_on

        content = item.find("div", class_="text").text
        review['content'] = content

        actions = item.find("div", class_="actions").text
        text = actions.replace(",", "")
        matched = re.findall(r"[0-9]+", text)
        if len(matched) == 2:
            upvotes = int(matched[0])
            total = int(matched[1])
            downvotes = total - upvotes
            helpfulness = upvotes / total
            review['upvotes'] = upvotes
            review['downvotes'] = downvotes
            review['helpfulness'] = helpfulness
        reviews.append(review)
    return json.dumps(reviews)
