"""
Contentstack API Client for Content Freshness Dashboard
"""

import os
import time
import requests
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("CONTENTSTACK_BASE_URL", "https://api.contentstack.io")
API_KEY = os.getenv("CONTENTSTACK_API_KEY")
MANAGEMENT_TOKEN = os.getenv("CONTENTSTACK_MANAGEMENT_TOKEN")


def get_headers() -> dict:
    """Returns headers required for Contentstack Management API requests."""
    return {
        "api_key": API_KEY,
        "authorization": MANAGEMENT_TOKEN,
        "Content-Type": "application/json"
    }


def get_content_types() -> list[dict]:
    """
    Fetch all content types from the stack.
    Returns list of dicts with 'uid', 'title', and 'schema'.
    """
    url = f"{BASE_URL}/v3/content_types"
    content_types = []
    skip = 0
    limit = 100
    
    while True:
        params = {"skip": skip, "limit": limit, "include_count": "true"}
        response = requests.get(url, headers=get_headers(), params=params)
        response.raise_for_status()
        data = response.json()
        
        batch = data.get("content_types", [])
        content_types.extend([
            {
                "uid": ct["uid"],
                "title": ct.get("title", ct["uid"]),
                "schema": ct.get("schema", [])
            }
            for ct in batch
        ])
        
        total = data.get("count", len(batch))
        skip += limit
        if skip >= total:
            break
        time.sleep(0.1)
    
    return content_types


def get_entries(content_type_uid: str, locale: Optional[str] = None, include_publish_details: bool = True) -> list[dict]:
    """
    Fetch all entries for a given content type.
    Handles pagination automatically.
    Returns list of entry dicts with metadata.
    """
    url = f"{BASE_URL}/v3/content_types/{content_type_uid}/entries"
    entries = []
    skip = 0
    limit = 100
    
    while True:
        params = {
            "skip": skip,
            "limit": limit,
            "include_count": "true",
            "include_publish_details": str(include_publish_details).lower()
        }
        if locale:
            params["locale"] = locale
        
        response = requests.get(url, headers=get_headers(), params=params)
        
        if response.status_code == 404:
            break
        response.raise_for_status()
        
        data = response.json()
        batch = data.get("entries", [])
        
        for entry in batch:
            entry["_content_type_uid"] = content_type_uid
        
        entries.extend(batch)
        
        total = data.get("count", len(batch))
        skip += limit
        if skip >= total:
            break
        time.sleep(0.1)
    
    return entries


def get_environments() -> list[dict]:
    """
    Fetch all environments from the stack.
    Returns list of dicts with 'uid', 'name'.
    """
    url = f"{BASE_URL}/v3/environments"
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()
    data = response.json()
    
    return [
        {
            "uid": env.get("uid", env.get("name")),
            "name": env.get("name", "")
        }
        for env in data.get("environments", [])
    ]


def get_locales() -> list[dict]:
    """
    Fetch all languages/locales from the stack.
    Returns list of dicts with 'code', 'name'.
    """
    url = f"{BASE_URL}/v3/locales"
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()
    data = response.json()
    
    return [
        {
            "code": loc.get("code", ""),
            "name": loc.get("name", loc.get("code", ""))
        }
        for loc in data.get("locales", [])
    ]


def get_taxonomies() -> list[dict]:
    """
    Fetch all taxonomies from the stack.
    Returns list of dicts with 'uid', 'name'.
    """
    url = f"{BASE_URL}/v3/taxonomies"
    response = requests.get(url, headers=get_headers())
    
    if response.status_code == 404:
        return []
    
    response.raise_for_status()
    data = response.json()
    
    return [
        {
            "uid": tax.get("uid", ""),
            "name": tax.get("name", tax.get("uid", ""))
        }
        for tax in data.get("taxonomies", [])
    ]


def get_all_entries(content_type_uids: Optional[list[str]] = None, locale: Optional[str] = None) -> list[dict]:
    """
    Fetch entries for multiple content types.
    If content_type_uids is None, fetches for all content types.
    """
    if content_type_uids is None:
        content_types = get_content_types()
        content_type_uids = [ct["uid"] for ct in content_types]
    
    all_entries = []
    for ct_uid in content_type_uids:
        entries = get_entries(ct_uid, locale=locale)
        all_entries.extend(entries)
    
    return all_entries


def extract_tags_from_entries(entries: list[dict]) -> list[str]:
    """
    Extract all unique tags from a list of entries.
    """
    tags = set()
    for entry in entries:
        entry_tags = entry.get("tags", [])
        if isinstance(entry_tags, list):
            tags.update(entry_tags)
    return sorted(list(tags))


def extract_taxonomies_from_entries(entries: list[dict]) -> list[str]:
    """
    Extract all unique taxonomy terms from entries.
    """
    taxonomy_terms = set()
    for entry in entries:
        taxonomies = entry.get("taxonomies", [])
        if isinstance(taxonomies, list):
            for tax in taxonomies:
                if isinstance(tax, dict):
                    term_uid = tax.get("term_uid", "")
                    if term_uid:
                        taxonomy_terms.add(term_uid)
    return sorted(list(taxonomy_terms))


if __name__ == "__main__":
    print("Testing Contentstack API Client...")
    
    print("\n1. Fetching content types...")
    cts = get_content_types()
    print(f"   Found {len(cts)} content types")
    for ct in cts[:5]:
        print(f"   - {ct['title']} ({ct['uid']})")
    
    print("\n2. Fetching environments...")
    envs = get_environments()
    print(f"   Found {len(envs)} environments")
    for env in envs:
        print(f"   - {env['name']}")
    
    print("\n3. Fetching locales...")
    locales = get_locales()
    print(f"   Found {len(locales)} locales")
    for loc in locales:
        print(f"   - {loc['name']} ({loc['code']})")
    
    print("\n4. Fetching taxonomies...")
    taxes = get_taxonomies()
    print(f"   Found {len(taxes)} taxonomies")
    for tax in taxes:
        print(f"   - {tax['name']} ({tax['uid']})")
    
    if cts:
        print(f"\n5. Fetching entries for '{cts[0]['title']}'...")
        entries = get_entries(cts[0]["uid"])
        print(f"   Found {len(entries)} entries")
