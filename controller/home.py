import http.client
import json

from services.db import get_random_keywords, get_top_keywords


# Homepage data


async def movie_search(query, page):
    conn = http.client.HTTPConnection("omdbapi.com")
    url = f"/?apikey=d49b3253&type=movie&plot=full&s={query}&page={page}"
    conn.request("GET", url)
    res_data = conn.getresponse().read()
    conn.close()
    results = json.loads(res_data.decode("utf-8"))
    if "Search" in results:
        search_results = results["Search"]
        return {"count": int(results["totalResults"]), "search": json.dumps([{
            "title": item["Title"],
            "releaseYear": item["Year"],
            "imdbID": item["imdbID"],
            "type": item["Type"],
            "poster": item["Poster"]
        } for item in search_results])}
    return False


def landing_keywords(count=16):
    kw_rand = get_random_keywords(count)
    kw_top = get_top_keywords()
    return {"random": kw_rand, "top": json.loads(kw_top)}
