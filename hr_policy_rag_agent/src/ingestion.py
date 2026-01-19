import json
import re
import requests

from urllib.parse import urljoin

import trafilatura

from bs4 import BeautifulSoup

from hr_policy_rag_agent.config.ingestion import DEFAULT_INGESTION_SETTINGS


# ---------------------------------------------------------------------------- #
#                        Scraping + Fetching Policy Text                       #
# ---------------------------------------------------------------------------- #


def create_session(custom_headers=None):
    """
    Creates a requests Session with headers that mimic a real browser.
    Returns a session object that can be used for all HTTP requests.
    """
    session = requests.Session()
    if custom_headers is not None:
        session.headers.update(custom_headers)
    return session


def get_all_links(session, url):
    resp = session.get(url, timeout=10)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    links = []

    # Find all <a> tags in the policy list
    for a in soup.select("a[href]"):
        href = urljoin(url, a["href"])
        title = a.get_text(strip=True)
        links.append((title, href))
    return links


def remove_non_policy_links(
    links,
    policy_pattern,
):
    policy_links = []
    # Filter out navigation or unrelated links
    for title, href in links:
        if re.match(policy_pattern, href) and title:
            policy_links.append((title, href))
    return policy_links


# ---------------------------------------------------------------------------- #
#                   Policy Content Extraction + Cleaning.                      #
# ---------------------------------------------------------------------------- #


def extract_policy_body(html):
    body = trafilatura.extract(html, include_comments=False, include_tables=True)
    return body


def fetch_policy(session, url):
    resp = session.get(url, timeout=10)
    resp.raise_for_status()
    return resp.text


def remove_disclaimer(disclaimer_pattern, text: str) -> str:
    cleaned = re.sub(disclaimer_pattern, "", text)
    return cleaned.strip()


# ---------------------------------------------------------------------------- #
#                   Write raw policy data to local jsonl file                  #
# ---------------------------------------------------------------------------- #


def write_to_jsonl_file(path, policy_docs):
    # Write list of dicts to JSONL
    with open(path, "w", encoding="utf-8") as f:
        for doc in policy_docs:
            json_line = json.dumps(
                doc, ensure_ascii=False
            )  # ensure_ascii=False keeps Unicode readable
            f.write(json_line + "\n")


# ---------------------------------------------------------------------------- #
#                                   Wrappers                                   #
# ---------------------------------------------------------------------------- #


def get_policy_links(session, url, policy_pattern):
    links = get_all_links(session=session, url=url)
    policy_links = remove_non_policy_links(links=links, policy_pattern=policy_pattern)
    return policy_links


def clean_policy_content(policy_html, disclaimer_pattern=None):
    body = extract_policy_body(html=policy_html)
    cleaned = remove_disclaimer(text=body, disclaimer_pattern=disclaimer_pattern)
    return cleaned


def scrape_all_policies(session, url, policy_pattern, disclaimer_pattern):
    policies = []
    links = get_policy_links(session, url, policy_pattern)
    for title, url in links:
        html = fetch_policy(session=session, url=url)
        cleaned_content = clean_policy_content(
            policy_html=html, disclaimer_pattern=disclaimer_pattern
        )
        policies.append(
            {
                "title": title,
                "url": url,
                "content": cleaned_content,
            }
        )
    return policies


def run_ingestion_pipeline():
    headers = DEFAULT_INGESTION_SETTINGS.get("headers")
    base_url = DEFAULT_INGESTION_SETTINGS.get("base_url")
    policy_pattern = DEFAULT_INGESTION_SETTINGS.get("policy_pattern")
    disclaimer_pattern = DEFAULT_INGESTION_SETTINGS.get("disclaimer_pattern")

    session = create_session(custom_headers=headers)
    policies = scrape_all_policies(
        session=session,
        url=base_url,
        policy_pattern=policy_pattern,
        disclaimer_pattern=disclaimer_pattern,
    )
    write_to_jsonl_file(
        path="data/raw/policies.jsonl", policy_docs=policies
    )  # TODO: Write this to mongodb
    return policies
