"""
Energy-AI Infrastructure News Monitor - Rapid Prototype
Collects news from RSS feeds and filters for Stargate/AI infrastructure relevance
"""
import feedparser
import csv
from datetime import datetime
import re

# === CONFIGURATION ===
FEEDS = {
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "Data Center Dynamics": "https://www.datacenterdynamics.com/en/rss/",
    "Utility Dive": "https://www.utilitydive.com/feeds/news/",
    "FERC News": "https://www.ferc.gov/news-events/rss",
    "World Nuclear News": "https://www.world-nuclear-news.org/rss",
}

# === FILTERING LOGIC ===
def is_relevant(title, description):
    """
    Determines if an article is relevant to Energy-AI infrastructure.
    Returns: (is_relevant: bool, reason: str)
    """
    text = (title + " " + description).lower()
    
    # Negative filters (TV show, crypto)
    negative_keywords = [
        "tv show", "sci-fi", "sg-1", "atlantis", "television",
        "cryptocurrency", "$stg", "defi", "token", "blockchain"
    ]
    
    for keyword in negative_keywords:
        if keyword in text:
            return False, f"Filtered: {keyword}"
    
    # Positive filters (AI infrastructure + energy)
    stargate_terms = ["stargate project", "stargate ai", "openai data center"]
    ai_terms = ["ai data center", "artificial intelligence infrastructure", "hyperscale"]
    energy_terms = ["grid capacity", "power demand", "electricity", "nuclear restart"]
    
    # High priority: Stargate mentions
    if any(term in text for term in stargate_terms):
        return True, "Stargate project mention"
    
    # Medium priority: AI + Energy
    has_ai = any(term in text for term in ai_terms) or re.search(r"\bai\b", text)
    has_energy = any(term in text for term in energy_terms)
    
    if has_ai and has_energy:
        return True, "AI + Energy nexus"
    
    # Low priority: Just energy infrastructure
    if any(term in text for term in ["data center", "grid", "capacity"]):
        return True, "Infrastructure mention"
    
    return False, "No relevant keywords"

# === MAIN COLLECTION LOOP ===
def collect_articles():
    """Fetch articles from all RSS feeds."""
    all_articles = []
    
    print("Starting news collection...")
    print("=" * 60)
    
    for source_name, feed_url in FEEDS.items():
        print(f"\n📡 Fetching: {source_name}")
        try:
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:  # Feed parsing error
                print(f"   ⚠️  Warning: Feed may have issues")
            
            count = 0
            for entry in feed.entries[:20]:  # Limit to 20 most recent
                title = entry.get('title', 'No title')
                link = entry.get('link', '')
                published = entry.get('published', 'Unknown date')
                summary = entry.get('summary', entry.get('description', ''))
                
                # Clean summary (remove HTML tags)
                summary_clean = re.sub('<[^<]+?>', '', summary)[:300]
                
                # Check relevance
                relevant, reason = is_relevant(title, summary_clean)
                
                article = {
                    'source': source_name,
                    'title': title,
                    'link': link,
                    'published': published,
                    'summary': summary_clean,
                    'relevant': relevant,
                    'reason': reason
                }
                
                all_articles.append(article)
                count += 1
            
            print(f"   ✅ Collected {count} articles")
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    return all_articles

# === SAVE RESULTS ===
def save_results(articles):
    """Save articles to CSV file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"articles_{timestamp}.csv"
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['source', 'title', 'link', 'published', 'relevant', 'reason', 'summary']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(articles)
    
    print(f"\n💾 Results saved to: {filename}")
    return filename

# === STATISTICS ===
def print_stats(articles):
    """Print collection statistics."""
    total = len(articles)
    relevant = sum(1 for a in articles if a['relevant'])
    filtered = total - relevant
    
    print("\n" + "=" * 60)
    print("COLLECTION STATISTICS")
    print("=" * 60)
    print(f"Total articles collected: {total}")
    print(f"Relevant articles:        {relevant} ({relevant/total*100:.1f}%)")
    print(f"Filtered out:             {filtered} ({filtered/total*100:.1f}%)")
    print("=" * 60)
    
    # Show sample of relevant articles
    print("\n📋 SAMPLE RELEVANT ARTICLES:")
    relevant_articles = [a for a in articles if a['relevant']][:5]
    for i, article in enumerate(relevant_articles, 1):
        print(f"\n{i}. {article['title']}")
        print(f"   Source: {article['source']}")
        print(f"   Reason: {article['reason']}")

# === MAIN EXECUTION ===
if __name__ == "__main__":
    print("⚡ Energy-AI Infrastructure News Monitor")
    print("   Prototype v1.0\n")
    
    # Collect articles
    articles = collect_articles()
    
    # Save to CSV
    csv_file = save_results(articles)
    
    # Print statistics
    print_stats(articles)
    
    print(f"\n✅ Complete! Open '{csv_file}' to view all results.")