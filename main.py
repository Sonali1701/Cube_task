import os
import time
import json
import yaml
import pandas as pd
import requests
from tqdm import tqdm
from itertools import islice
from pytrends.request import TrendReq
from bs4 import BeautifulSoup
from google import genai  # official Gemini SDK

# -------- Config load --------
def read_config(path="config.yaml"):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    else:
        return {}

# -------- Website scraping for seed keyword extraction --------
def scrape_website_text(url):
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        texts = []

        if soup.title:
            texts.append(soup.title.get_text())

        desc = soup.find('meta', attrs={'name':'description'})
        if desc and desc.get('content'):
            texts.append(desc['content'])

        for header_tag in ['h1', 'h2']:
            headers = soup.find_all(header_tag)
            for h in headers:
                texts.append(h.get_text())

        return "\n".join(texts)

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return ""

# -------- Gemini Flash API call helper using google-genai SDK --------
def generate_with_gemini(client, prompt_text, model="gemini-2.0-flash"):
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt_text
        )
        return response.text
    except Exception as e:
        print(f"Gemini Flash API request failed: {e}")
        return ""

# -------- Extract seed keywords from website text using Gemini Flash --------
def extract_seed_keywords_from_text(client, text, max_keywords=10):
    prompt = (
        "Extract the top seed keywords for SEM campaigns from the following website text:\n"
        f"{text}\n\n"
        "List them as a bulleted list."
    )
    response_text = generate_with_gemini(client, prompt)
    if not response_text:
        return []

    keywords = []
    for line in response_text.splitlines():
        line = line.strip()
        if line.startswith("- ") or line.startswith("* "):
            kw = line[2:].strip()
            if kw and kw not in keywords:
                keywords.append(kw)
            if len(keywords) >= max_keywords:
                break
    return keywords

# -------- Gemini Flash keyword expansion --------
def expand_keywords_gemini_flash(client, seed_keywords, max_expansions=5):
    prompt_text = (
        "Given the following seed keywords, generate a list of related keyword phrases for SEM campaigns.\n"
        "Seed keywords:\n" + "\n".join(f"- {kw}" for kw in seed_keywords) + "\n"
        "Return only the expanded keywords as a bulleted list."
    )
    response_text = generate_with_gemini(client, prompt_text)
    if not response_text:
        return seed_keywords  # fallback

    expanded_keywords = []
    for line in response_text.splitlines():
        line = line.strip()
        if line.startswith("- ") or line.startswith("* "):
            kw = line[2:].strip()
            if kw and kw not in expanded_keywords and kw not in seed_keywords:
                expanded_keywords.append(kw)
            if len(expanded_keywords) >= max_expansions * len(seed_keywords):
                break
    return list(set(seed_keywords + expanded_keywords))

# -------- Helper to batch keywords --------
def batch(iterable, n=1):
    it = iter(iterable)
    while True:
        batch_iter = list(islice(it, n))
        if not batch_iter:
            break
        yield batch_iter

# -------- Google Trends fetch with retries and backoff --------
def fetch_google_trends(keywords, geo="IN", retries=3, backoff=5, batch_size=5, delay=15):
    pytrends = TrendReq(hl='en-US', tz=360, retries=1, backoff_factor=0)
    trends_data = []

    total_batches = (len(keywords) + batch_size - 1) // batch_size
    print(f"Total keywords: {len(keywords)}, querying in {total_batches} batches of {batch_size}.")

    for i, kw_batch in enumerate(batch(keywords, batch_size), start=1):
        attempt = 0
        while attempt < retries:
            try:
                print(f"[Batch {i}/{total_batches}] Fetching keywords: {kw_batch}")
                pytrends.build_payload(kw_batch, cat=0, timeframe='today 12-m', geo=geo, gprop='')
                data = pytrends.interest_over_time()

                if data.empty:
                    raise ValueError("Empty dataframe returned")

                if 'isPartial' in data.columns:
                    data = data.drop(columns=['isPartial'])

                for kw in kw_batch:
                    if kw in data.columns:
                        score = data[kw].mean()
                        trends_data.append({"keyword": kw, "trends_score": score})
                    else:
                        print(f"Warning: Keyword '{kw}' missing in data columns.")

                print(f"Batch {i} successful. Sleeping for {delay} seconds to avoid rate limits...")
                time.sleep(delay)
                break

            except Exception as e:
                attempt += 1
                print(f"Attempt {attempt} failed for batch {i}: {e}")
                if attempt < retries:
                    wait = backoff * attempt
                    print(f"Retrying batch {i} after {wait} seconds...")
                    time.sleep(wait)
                else:
                    print(f"Skipping batch {i} after {retries} failed attempts.")
                    break

    return trends_data

# -------- Dummy CPC stub -------- (for now as i don't have access to actual CPC data)
def get_cpc_from_ubersuggest(keyword):
    return round(0.5 + 0.1 * len(keyword.split()), 2)

# -------- Main pipeline --------
def main():
    config = read_config()

    api_key = config.get("gemini_api_key")
    brand_url = config.get("brand_website")
    competitor_url = config.get("competitor_website")

    if not api_key:
        print("Error: Gemini API key not provided in config.yaml")
        return
    if not brand_url or not competitor_url:
        print("Error: Brand or Competitor website URL missing in config.yaml")
        return

    genai_client = genai.Client(api_key=api_key)

    print(f"Scraping brand website: {brand_url}")
    brand_text = scrape_website_text(brand_url)
    print(f"Scraping competitor website: {competitor_url}")
    competitor_text = scrape_website_text(competitor_url)

    combined_text = (brand_text + "\n" + competitor_text)[:1000]  # truncate to 1000 chars

    print("Extracting seed keywords from website content using Gemini Flash LLM...")
    seed_keywords = extract_seed_keywords_from_text(genai_client, combined_text)
    print(f"Seed keywords extracted ({len(seed_keywords)}): {seed_keywords}")

    if not seed_keywords:
        print("No seed keywords extracted, falling back to dummy seed keywords.")
        seed_keywords = [
            "muscle blaze protein",
            "vegan protein powder",
            "whey protein",
            "mass gainer",
            "creatine supplement"
        ]

    print("Expanding seed keywords using Gemini Flash LLM...")
    expanded_keywords = expand_keywords_gemini_flash(genai_client, seed_keywords)
    print(f"Total expanded keywords: {len(expanded_keywords)}")

    print("Fetching Google Trends data...")
    trends_data = fetch_google_trends(
        expanded_keywords,
        geo=config.get("geo", "IN"),
        retries=config.get("retries", 3),
        backoff=config.get("backoff", 5),
        batch_size=config.get("batch_size", 5),
        delay=config.get("delay", 15)
    )

    if not trends_data:
        print("No Google Trends data fetched. Using all keywords for next steps.")
        trends_df = pd.DataFrame({"keyword": expanded_keywords})
    else:
        trends_df = pd.DataFrame(trends_data)
        min_score = config.get("min_trends_score", 0)
        trends_df = trends_df[trends_df["trends_score"] >= min_score]

    if trends_df.empty:
        print("No keywords to scrape CPC for. Skipping CPC scraping.")
        cpc_df = pd.DataFrame(columns=["keyword", "cpc_usd"])
    else:
        print("Scraping CPC data from Ubersuggest (dummy data)...")
        cpc_data = []
        for kw in tqdm(trends_df["keyword"], desc="Scraping CPC"):
            cpc = get_cpc_from_ubersuggest(kw)
            cpc_data.append({"keyword": kw, "cpc_usd": cpc})
        cpc_df = pd.DataFrame(cpc_data)

    if not trends_df.empty and not cpc_df.empty:
        final_df = pd.merge(trends_df, cpc_df, on="keyword", how="left")
    else:
        final_df = trends_df

    print(f"Final keywords count: {len(final_df)}")
    print(final_df.head())

    output_dir = config.get("output_dir", "output")
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "sem_keywords_final.csv")
    json_path = os.path.join(output_dir, "sem_keywords_final.json")

    final_df.to_csv(csv_path, index=False)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(final_df.to_dict(orient="records"), f, indent=2)

    print(f"Saved CSV: {csv_path}")
    print(f"Saved JSON: {json_path}")

if __name__ == "__main__":
    main()
