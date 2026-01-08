from pathlib import Path
import xml.etree.ElementTree as ET

DUMP_PATH = Path("../backend/data/raw/bioshock_pages_current.xml").resolve()

# Remove all non-articles from the corpus
BLOCKED_PREFIXES = (
    "User:",
    "User talk:",
    "Talk:",
    "Forum:",
    "Message Wall:",
    "Blog:",
)


def classify_page(ns: int, title: str) -> str:
    """
    Return 'article' for main canon pages,
    'forum' for talk/user/forum/etc.
    """
    if ns != 0:
        return "forum"
    if title.startswith(BLOCKED_PREFIXES):
        return "forum"
    return "article"


def main():
    # confirm that DUMP_PATH leads to raw data files
    if not DUMP_PATH.exists():
        raise FileNotFoundError(f"Dump not found at: {DUMP_PATH.absolute()}")

    # load .xml database dump and parse
    print(f"Loading dump: {DUMP_PATH}")
    tree = ET.parse(DUMP_PATH)
    root = tree.getroot()

    pages = root.findall(".//{*}page")
    print(f"Total <page> elements found: {len(pages)}")

    article_pages = []
    forum_pages = []

    for page in pages:
        title_el = page.find("./{*}title")
        ns_el = page.find("./{*}ns")
        text_el = page.find(".//{*}text")

        title = title_el.text if title_el is not None else "<NO TITLE>"
        ns = int(ns_el.text) if ns_el is not None and ns_el.text.isdigit() else -1
        text = text_el.text if text_el is not None else ""

        kind = classify_page(ns, title)

        record = {
            "title": title,
            "ns": ns,
            "text": text,
        }

        if kind == "article":
            article_pages.append(record)
        else:
            forum_pages.append(record)

    print(f"\nArticle-like pages (canon-ish): {len(article_pages)}")
    print(f"Forum/discussion-like pages:   {len(forum_pages)}")

    print("\nSample article pages:")
    for rec in article_pages[:5]:
        preview = (rec["text"][:120] + "...") if len(rec["text"]) > 120 else rec["text"]
        print("--------------------------------------------------")
        print(f"Title: {rec['title']} (ns={rec['ns']})")
        print(f"Preview: {preview!r}")

    print("\nSample forum/discussion pages:")
    for rec in forum_pages[:5]:
        preview = (rec["text"][:120] + "...") if len(rec["text"]) > 120 else rec["text"]
        print("--------------------------------------------------")
        print(f"Title: {rec['title']} (ns={rec['ns']})")
        print(f"Preview: {preview!r}")


if __name__ == "__main__":
    main()
