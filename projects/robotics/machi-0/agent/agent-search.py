import argparse
from duckduckgo_search import DDGS

def test_search(query):
    print(f"--- Looi searching DuckDuckGo for: '{query}' ---")
    
    try:
        with DDGS() as ddgs:
            # text() is the standard search method
            results = list(ddgs.text(query, max_results=10))
            
            if not results:
                print("No results found.")
                return

            for i, r in enumerate(results, 1):
                print(f"[{i}] {r['title']}")
                print(f"    Link: {r['href']}")
                print(f"    Snippet: {r['body'][:120]}...")
                print("-" * 30)
                
    except Exception as e:
        print(f"Search failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--search-text", type=str, required=True)
    args = parser.parse_args()
    test_search(args.search_text)