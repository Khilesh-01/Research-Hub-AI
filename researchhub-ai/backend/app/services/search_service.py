"""
search_service.py – Query arXiv (via feedparser) and PubMed APIs.

ArXiv API
  Base URL : http://export.arxiv.org/api/query
  Method   : GET
  Key params: search_query, start, max_results
  No API key required — publicly accessible.
  Example  : http://export.arxiv.org/api/query?search_query=all:machine+learning&start=0&max_results=5

PubMed API
  Base URL : https://eutils.ncbi.nlm.nih.gov/entrez/eutils
  API key loaded from PUBMED_API_KEY env variable.
"""
import os
import xml.etree.ElementTree as ET
from typing import List, Optional

import feedparser
import requests
from dotenv import load_dotenv

load_dotenv()

_PUBMED_API_KEY: Optional[str] = os.getenv("PUBMED_API_KEY")


# ── arXiv  (feedparser) ───────────────────────────────────────────────────────
class ArXivService:
    """
    Fetches research papers from the arXiv public API.

    Endpoint : http://export.arxiv.org/api/query
    No authentication required.
    Returns  : Atom feed parsed by feedparser.
    """

    BASE_URL = "http://export.arxiv.org/api/query"

    def search(self, query: str, max_results: int = 10) -> List[dict]:
        """
        Search arXiv for papers matching *query*.

        Parameters
        ----------
        query       : free-text search string
        max_results : maximum number of results to return (default 10)

        GET parameters sent to arXiv:
          search_query → e.g. all:transformer attention
          start        → starting result index (0-based)
          max_results  → number of results
        """
        url = (
            f"{self.BASE_URL}"
            f"?search_query=all:{requests.utils.quote(query)}"
            f"&start=0"
            f"&max_results={max_results}"
            f"&sortBy=relevance"
            f"&sortOrder=descending"
        )
        try:
            feed = feedparser.parse(url)
            if feed.get("bozo") and not feed.get("entries"):
                print(f"[ArXiv] Feed parse warning: {feed.get('bozo_exception')}")
            return self._parse_feed(feed)
        except Exception as exc:
            print(f"[ArXiv] Search error: {exc}")
            return []

    # ── Parser ─────────────────────────────────────────────────────────────
    @staticmethod
    def _parse_feed(feed) -> List[dict]:
        papers: List[dict] = []

        for entry in feed.get("entries", []):
            # Title — strip leading/trailing whitespace and newlines
            title = entry.get("title", "").replace("\n", " ").strip()

            # Abstract (feedparser key: summary)
            abstract = entry.get("summary", "").replace("\n", " ").strip()

            # Authors — feedparser returns a list of dicts with 'name'
            authors = ", ".join(
                a.get("name", "") for a in entry.get("authors", [])
                if a.get("name")
            )

            # Published date — ISO 8601, take first 10 chars (YYYY-MM-DD)
            published_date = entry.get("published", "")[:10]

            # arXiv ID → build PDF link
            # entry.id looks like: http://arxiv.org/abs/2103.01234v1
            arxiv_id_url: str = entry.get("id", "")
            arxiv_id = arxiv_id_url.split("/abs/")[-1] if "/abs/" in arxiv_id_url else ""

            # Prefer explicit PDF link from feed, fall back to constructed URL
            pdf_url: Optional[str] = None
            for link in entry.get("links", []):
                if link.get("type") == "application/pdf":
                    pdf_url = link.get("href")
                    break
            if pdf_url is None and arxiv_id:
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

            # Abstract page link
            abs_url = arxiv_id_url if arxiv_id_url.startswith("http") else None

            papers.append(
                {
                    "title": title,
                    "abstract": abstract,
                    "authors": authors,
                    "published_date": published_date,
                    "source": "arxiv",
                    "doi": None,
                    "pdf_url": pdf_url,
                    "abs_url": abs_url,
                }
            )

        return papers


# ── PubMed ────────────────────────────────────────────────────────────────────
class PubMedService:
    """
    Fetches research papers from NCBI PubMed E-utilities.
    Uses PUBMED_API_KEY from environment (higher rate limit when provided).
    """

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def _base_params(self) -> dict:
        """Common params injected into every E-utilities request."""
        p: dict = {"tool": "ResearchHubAI", "email": "researchhub@example.com"}
        if _PUBMED_API_KEY:
            p["api_key"] = _PUBMED_API_KEY
        return p

    def search(self, query: str, max_results: int = 10) -> List[dict]:
        try:
            ids = self._fetch_ids(query, max_results)
            if not ids:
                return []
            return self._fetch_details(ids)
        except Exception as exc:
            print(f"[PubMed] Search error: {exc}")
            return []

    def _fetch_ids(self, query: str, max_results: int) -> List[str]:
        params = {
            **self._base_params(),
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "sort": "relevance",
        }
        resp = requests.get(
            f"{self.BASE_URL}/esearch.fcgi", params=params, timeout=30
        )
        resp.raise_for_status()
        return resp.json().get("esearchresult", {}).get("idlist", [])

    def _fetch_details(self, ids: List[str]) -> List[dict]:
        params = {
            **self._base_params(),
            "db": "pubmed",
            "id": ",".join(ids),
            "retmode": "xml",
            "rettype": "abstract",
        }
        resp = requests.get(
            f"{self.BASE_URL}/efetch.fcgi", params=params, timeout=30
        )
        resp.raise_for_status()
        return self._parse(resp.text)

    def _parse(self, xml_text: str) -> List[dict]:
        papers: List[dict] = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return papers

        for article in root.findall(".//PubmedArticle"):
            medline = article.find("MedlineCitation")
            if medline is None:
                continue
            art = medline.find("Article")
            if art is None:
                continue

            title_el = art.find("ArticleTitle")
            title = "".join(title_el.itertext()) if title_el is not None else ""

            abstract_el = art.find(".//AbstractText")
            abstract = "".join(abstract_el.itertext()) if abstract_el is not None else ""

            authors: List[str] = []
            for au in art.findall(".//Author"):
                last = au.find("LastName")
                fore = au.find("ForeName")
                if last is not None:
                    name = last.text or ""
                    if fore is not None:
                        name = f"{fore.text} {name}"
                    authors.append(name)

            pub_date = art.find(".//PubDate")
            published_date = ""
            if pub_date is not None:
                year_el = pub_date.find("Year")
                month_el = pub_date.find("Month")
                if year_el is not None:
                    published_date = year_el.text or ""
                    if month_el is not None:
                        published_date = f"{year_el.text}-{month_el.text}"

            doi: Optional[str] = None
            for aid in article.findall(".//ArticleId"):
                if aid.get("IdType") == "doi":
                    doi = aid.text

            pmid_el = medline.find("PMID")
            pmid = pmid_el.text if pmid_el is not None else None
            pdf_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None

            papers.append(
                {
                    "title": title,
                    "abstract": abstract,
                    "authors": ", ".join(authors),
                    "published_date": published_date,
                    "source": "pubmed",
                    "doi": doi,
                    "pdf_url": pdf_url,
                }
            )
        return papers


# ── Unified facade ────────────────────────────────────────────────────────────
class SearchService:
    def __init__(self):
        self._arxiv = ArXivService()
        self._pubmed = PubMedService()

    def search(
        self,
        query: str,
        source: str = "all",
        max_results: int = 10,
    ) -> List[dict]:
        results: List[dict] = []
        if source in ("all", "arxiv"):
            results.extend(self._arxiv.search(query, max_results))
        if source in ("all", "pubmed"):
            results.extend(self._pubmed.search(query, max_results))
        return results


search_service = SearchService()
