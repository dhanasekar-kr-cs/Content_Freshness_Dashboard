"""
Utility functions for Content Freshness Dashboard
"""

from datetime import datetime, timedelta
from typing import Optional
import pandas as pd


FRESHNESS_THRESHOLDS = {
    "fresh": 30,
    "aging": 90
}


def parse_date(iso_string: Optional[str]) -> Optional[datetime]:
    """
    Parse ISO format date string to datetime object.
    Handles various ISO formats from Contentstack API.
    """
    if not iso_string:
        return None
    
    try:
        if "." in iso_string:
            iso_string = iso_string.split(".")[0] + "Z"
        
        iso_string = iso_string.replace("Z", "+00:00")
        return datetime.fromisoformat(iso_string.replace("+00:00", ""))
    except (ValueError, AttributeError):
        try:
            return datetime.strptime(iso_string[:19], "%Y-%m-%dT%H:%M:%S")
        except (ValueError, AttributeError):
            return None


def calculate_freshness(updated_at: Optional[str], reference_date: Optional[datetime] = None) -> str:
    """
    Calculate freshness category based on last updated date.
    
    Returns:
        - "Fresh": Updated within last 30 days
        - "Aging": Updated 30-90 days ago
        - "Stale": Not updated in 90+ days
        - "Unknown": No date available
    """
    if not updated_at:
        return "Unknown"
    
    updated_date = parse_date(updated_at)
    if not updated_date:
        return "Unknown"
    
    if reference_date is None:
        reference_date = datetime.now()
    
    days_since_update = (reference_date - updated_date).days
    
    if days_since_update < FRESHNESS_THRESHOLDS["fresh"]:
        return "Fresh"
    elif days_since_update < FRESHNESS_THRESHOLDS["aging"]:
        return "Aging"
    else:
        return "Stale"


def get_days_since_update(updated_at: Optional[str], reference_date: Optional[datetime] = None) -> Optional[int]:
    """
    Calculate the number of days since the entry was last updated.
    """
    if not updated_at:
        return None
    
    updated_date = parse_date(updated_at)
    if not updated_date:
        return None
    
    if reference_date is None:
        reference_date = datetime.now()
    
    return (reference_date - updated_date).days


def filter_by_date_range(
    entries: list[dict],
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    date_field: str = "updated_at"
) -> list[dict]:
    """
    Filter entries by date range based on specified date field.
    """
    if start_date is None and end_date is None:
        return entries
    
    filtered = []
    for entry in entries:
        entry_date = parse_date(entry.get(date_field))
        if entry_date is None:
            continue
        
        if start_date and entry_date < start_date:
            continue
        if end_date and entry_date > end_date:
            continue
        
        filtered.append(entry)
    
    return filtered


def get_time_period_dates(period: str) -> tuple[Optional[datetime], datetime]:
    """
    Convert time period string to start and end dates.
    
    Returns (start_date, end_date) tuple.
    """
    end_date = datetime.now()
    
    period_days = {
        "Last 7 days": 7,
        "Last 30 days": 30,
        "Last 90 days": 90,
        "Last 180 days": 180,
        "Last 1 year": 365,
        "All time": None
    }
    
    days = period_days.get(period)
    if days is None:
        return (None, end_date)
    
    start_date = end_date - timedelta(days=days)
    return (start_date, end_date)


def is_entry_published(entry: dict, environment: Optional[str] = None) -> bool:
    """
    Check if an entry is published.
    If environment is specified, checks if published to that specific environment.
    """
    publish_details = entry.get("publish_details", [])
    
    if not publish_details:
        return False
    
    if isinstance(publish_details, dict):
        publish_details = [publish_details]
    
    if environment is None:
        return len(publish_details) > 0
    
    for pd in publish_details:
        if pd.get("environment") == environment:
            return True
    
    return False


def get_publish_state(entry: dict) -> str:
    """
    Determine the publish state of an entry.
    Returns "Published", "Draft", or "Unpublished".
    """
    publish_details = entry.get("publish_details", [])
    
    if publish_details:
        return "Published"
    
    if entry.get("_version", 1) > 0:
        return "Draft"
    
    return "Unpublished"


def filter_by_publish_state(entries: list[dict], states: list[str]) -> list[dict]:
    """
    Filter entries by publish state.
    """
    if not states:
        return entries
    
    return [e for e in entries if get_publish_state(e) in states]


def filter_by_tags(entries: list[dict], tags: list[str]) -> list[dict]:
    """
    Filter entries that have at least one of the specified tags.
    """
    if not tags:
        return entries
    
    filtered = []
    for entry in entries:
        entry_tags = entry.get("tags", [])
        if isinstance(entry_tags, list) and any(t in entry_tags for t in tags):
            filtered.append(entry)
    
    return filtered


def filter_by_content_types(entries: list[dict], content_type_uids: list[str]) -> list[dict]:
    """
    Filter entries by content type UIDs.
    """
    if not content_type_uids:
        return entries
    
    return [e for e in entries if e.get("_content_type_uid") in content_type_uids]


def entries_to_dataframe(entries: list[dict], content_type_map: Optional[dict] = None) -> pd.DataFrame:
    """
    Convert list of entries to a pandas DataFrame for display.
    """
    if not entries:
        return pd.DataFrame()
    
    rows = []
    for entry in entries:
        ct_uid = entry.get("_content_type_uid", "")
        ct_name = content_type_map.get(ct_uid, ct_uid) if content_type_map else ct_uid
        
        updated_at = entry.get("updated_at", "")
        created_at = entry.get("created_at", "")
        
        rows.append({
            "Title": entry.get("title", "Untitled"),
            "UID": entry.get("uid", ""),
            "Content Type": ct_name,
            "Status": get_publish_state(entry),
            "Freshness": calculate_freshness(updated_at),
            "Days Since Update": get_days_since_update(updated_at),
            "Last Updated": parse_date(updated_at).strftime("%Y-%m-%d %H:%M") if parse_date(updated_at) else "N/A",
            "Created": parse_date(created_at).strftime("%Y-%m-%d %H:%M") if parse_date(created_at) else "N/A",
            "Tags": ", ".join(entry.get("tags", [])) if entry.get("tags") else "",
            "Locale": entry.get("locale", ""),
        })
    
    df = pd.DataFrame(rows)
    return df


def calculate_freshness_stats(entries: list[dict]) -> dict:
    """
    Calculate freshness statistics for a list of entries.
    """
    total = len(entries)
    if total == 0:
        return {
            "total": 0,
            "fresh": 0,
            "aging": 0,
            "stale": 0,
            "unknown": 0,
            "fresh_pct": 0,
            "aging_pct": 0,
            "stale_pct": 0
        }
    
    fresh = sum(1 for e in entries if calculate_freshness(e.get("updated_at")) == "Fresh")
    aging = sum(1 for e in entries if calculate_freshness(e.get("updated_at")) == "Aging")
    stale = sum(1 for e in entries if calculate_freshness(e.get("updated_at")) == "Stale")
    unknown = total - fresh - aging - stale
    
    return {
        "total": total,
        "fresh": fresh,
        "aging": aging,
        "stale": stale,
        "unknown": unknown,
        "fresh_pct": round(fresh / total * 100, 1),
        "aging_pct": round(aging / total * 100, 1),
        "stale_pct": round(stale / total * 100, 1)
    }


def calculate_freshness_by_content_type(entries: list[dict], content_type_map: Optional[dict] = None) -> pd.DataFrame:
    """
    Calculate freshness breakdown by content type.
    """
    ct_stats = {}
    
    for entry in entries:
        ct_uid = entry.get("_content_type_uid", "Unknown")
        ct_name = content_type_map.get(ct_uid, ct_uid) if content_type_map else ct_uid
        
        if ct_name not in ct_stats:
            ct_stats[ct_name] = {"Fresh": 0, "Aging": 0, "Stale": 0, "Unknown": 0}
        
        freshness = calculate_freshness(entry.get("updated_at"))
        ct_stats[ct_name][freshness] += 1
    
    rows = []
    for ct_name, stats in ct_stats.items():
        total = sum(stats.values())
        rows.append({
            "Content Type": ct_name,
            "Total": total,
            "Fresh": stats["Fresh"],
            "Aging": stats["Aging"],
            "Stale": stats["Stale"],
            "Unknown": stats["Unknown"]
        })
    
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("Total", ascending=False)
    
    return df


if __name__ == "__main__":
    print("Testing utility functions...")
    
    test_date = "2024-01-15T10:30:00.000Z"
    print(f"\nParse date: {test_date}")
    print(f"Result: {parse_date(test_date)}")
    
    print(f"\nFreshness for {test_date}: {calculate_freshness(test_date)}")
    
    recent_date = datetime.now().isoformat()
    print(f"Freshness for today: {calculate_freshness(recent_date)}")
    
    print("\nTime period dates:")
    for period in ["Last 7 days", "Last 30 days", "Last 90 days", "All time"]:
        start, end = get_time_period_dates(period)
        print(f"  {period}: {start} to {end}")
