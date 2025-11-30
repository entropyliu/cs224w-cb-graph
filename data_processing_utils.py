from dotenv import load_dotenv
import os
import io
import json
import requests
import pdfplumber
from tqdm import tqdm
import re

from dateutil import parser

import json
import os
from tqdm import tqdm
import requests
from bs4 import BeautifulSoup
import re

load_dotenv()
fed_prints_api_key = os.getenv("FED_PRINTS_KEY")

def query_fed_prints_by_author(author_name):


    url = f"https://fedinprint.org/api/author/{author_name}/items"
    params = {
        "limit": 10000
    }
    headers = {
        "x-api-key": fed_prints_api_key
    }
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    print("Total Records", len(data["records"]))
    return data

def get_author_short_name(author_name):
    return author_name.split(":")[-1].split("-")[0]


def get_saved_ids(author_name):
    author_short_name = get_author_short_name(author_name)
    if not os.path.exists(f"text_data/{author_short_name}.json"):
        return []
    with open(f"text_data/{author_short_name}.json", "r", encoding="utf-8") as f:
        text_data = json.load(f)
        return list(map(lambda x: x["id"], text_data))

def extract_chicagofed_html(url):

    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # -------- Extract DATE ----------
    raw_date = ""
    iso_date = ""

    date_div = soup.select_one("div.cfedDetail__lastUpdated")
    if date_div:
        txt = date_div.get_text(" ", strip=True)
        # Find mm/dd/yy or mm/dd/yyyy
        m = re.search(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b", txt)
        if m:
            raw_date = m.group(0)
            try:
                iso_date = parser.parse(raw_date).date().isoformat()
            except:
                iso_date = ""

    title = ""
    title_div = soup.select_one("div.cfedDetail__title h1")
    if title_div:
        title = title_div.get_text(" ", strip=True)

    paragraphs = []

    for body in soup.select("div.cfedContent__body"):
        h = body.find("h3")
        if h:
            paragraphs.append(h.get_text(" ", strip=True))

        for txt_div in body.select("div.cfedContent__text"):
            for p in txt_div.find_all("p"):
                t = p.get_text(" ", strip=True)
                if t:
                    paragraphs.append(t)

    full_text = "\n\n".join(paragraphs)

    return {
        "title": title,
        "date": iso_date,
        "text": full_text,
        "length": len(full_text)
    }


def extract_stlouisfed_html(url):
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # ---------- TITLE ----------
    title = ""
    h1 = soup.select_one("div.component.content h1")
    if h1:
        title = h1.get_text(" ", strip=True)

    # ---------- DATE ----------
    raw_date = ""
    iso_date = ""

    # Typically the first <p> after title block is the date
    date_tag = soup.select_one("div.component.content p")
    if date_tag:
        raw_date = date_tag.get_text(" ", strip=True)
        try:
            iso_date = parser.parse(raw_date).date().isoformat()
        except:
            iso_date = ""

    # ---------- MAIN TEXT ----------
    paragraphs = []

    body = soup.select_one("div.field-content div.wrapper")
    if body:
        for tag in body.find_all(["p", "h2", "h3"]):
            t = tag.get_text(" ", strip=True)
            if t:
                paragraphs.append(t)

    full_text = "\n\n".join(paragraphs)

    return {
        "title": title,
        "date": iso_date,
        "text": full_text,
        "length": len(full_text),
    }

def retrieve_remaining_ids(author_name, data):

    ids     = get_saved_ids(author_name)
    records = data["records"]

    idx = 0
    url_links = {}

    for record in records:

        if record["id"] in ids:
            continue

        if "file" not in record:
            continue
        if "fedlwp" in record["id"]:
            continue
        if "fedhwp" in record["id"]:
            continue
        if "fedcwp" in record["id"]:
            continue
        if "fedlrv" in record["id"]:
            continue
        if "fedgfn" in record["id"]:
            continue
        if "fedgfe" in record["id"]:
            continue
        if "fedlre" in record["id"]:
            continue
        if "fedlar" in record["id"]:
            continue
        if "fedcer" in record["id"]:
            continue
        if "fedles" in record["id"]:
            continue
        if "fedlps" in record["id"]:
            continue
        if "fedcwq" in record["id"]:
            continue
        if "fedfci" in record["id"]:
            continue
        if "fedkcc" in record["id"]:
            continue
        if "fedfmo" in record["id"]:
            continue
        if "fedmsr" in record["id"]:
            continue
        if "fedmwp" in record["id"]:
            continue
        if "fedmem" in record["id"]:
            continue
        if "fednls" in record["id"]:
            continue
        if "fedlcb" in record["id"]:
            continue
        if "fedgsq" in record["id"]:
            continue
        if "fedgrb" in record["id"]:
            continue
        if "fedbcp" in record["id"]:
            continue
        if "fedlpr" in record["id"]:
            continue
        if "fedfar" in record["id"]:
            continue
        if "fedaer" in record["id"]:
            continue
        if "fedgpr" in record["id"]:
            continue
        if "fedfel" in record["id"]:
            continue

        for file in record["file"]:

            file_function = file.get("filefunction", "")

            if "Video" in file_function:
                continue
            if "Figures" in file_function:
                continue

            if "Summary" in file_function:
                continue

            url = file["fileurl"]
            print(record["id"], file)

            if url.endswith(".pdf"):
                if "pdf" not in url_links:
                    url_links["pdf"] = {}
                url_links['pdf'][record["id"]] = url

            if "www.newyorkfed.org" in url:
                if "newyorkfed" not in url_links:
                    url_links["newyorkfed"] = {}
                url_links["newyorkfed"][record["id"]] = url

            if "www.federalreserve.gov" in url:
                if "board" not in url_links:
                    url_links["board"] = {}
                url_links['board'][record["id"]] = url

            if "www.dallasfed.org" in url:
                if "dallasfed" not in url_links:
                    url_links["dallasfed"] = {}
                url_links['dallasfed'][record["id"]] = url

            if "www.chicagofed.org" in url:
                if "chicagofed" not in url_links:
                    url_links["chicagofed"] = {}
                url_links['chicagofed'][record["id"]] = url

            if "www.clevelandfed.org" in url:
                if "clevelandfed" not in url_links:
                    url_links["clevelandfed"] = {}
                url_links['clevelandfed'][record["id"]] = url

            if "www.philadelphiafed.org" in url:
                if "philadelphiafed" not in url_links:
                    url_links["philadelphiafed"] = {}
                url_links['philadelphiafed'][record["id"]] = url

            if "www.stlouisfed.org" in url:
                if "stlouisfed" not in url_links:
                    url_links["stlouisfed"] = {}
                url_links['stlouisfed'][record["id"]] = url

            if "www.bostonfed.org" in url:
                if "bostonfed" not in url_links:
                    url_links["bostonfed"] = {}
                url_links['bostonfed'][record["id"]] = url

            idx += 1

    print("Total Remaining Files", idx)
    return url_links, idx


DATE_PATTERNS = [
    r"[A-Z][a-z]+ \d{1,2}, \d{4}",     # October 17, 2019
    r"[A-Z][a-z]+ \d{1,2} \d{4}",      # October 17 2019
    r"\d{1,2} [A-Z][a-z]+ \d{4}",      # 17 October 2019 (ECB-style)
    r"\d{4}-\d{2}-\d{2}",              # 2019-10-17
]

def extract_date(text):
    first_500 = text[:500]  # restrict to beginning (where date always appears)

    for pattern in DATE_PATTERNS:
        match = re.search(pattern, first_500)
        if match:
            try:
                dt = parser.parse(match.group())
                return dt.strftime("%Y-%m-%d")
            except:
                pass

    return None  # fallback if no date found

def download_pdf(url):
    """Download PDF and return bytes (None if fail)."""
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        return io.BytesIO(r.content)
    except Exception as e:
        print(f"[ERROR] Failed downloading {url}: {e}")
        return None


def extract_pdf_text(pdf_bytes):
    """Extract text from PDF bytes using pdfplumber."""
    try:
        all_pages = []
        with pdfplumber.open(pdf_bytes) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                all_pages.append(text)
        return "\n\n".join(all_pages)
    except Exception as e:
        print("[ERROR] Failed parsing PDF:", e)
        return ""

def pdfs_to_json(url_list, output_json="speeches.json"):

    if os.path.exists(output_json):
        with open(output_json, "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
                if not isinstance(existing_data, list):
                    existing_data = []
            except json.JSONDecodeError:
                existing_data = []
    else:
        existing_data = []

    existing_ids = {entry["id"] for entry in existing_data}

    new_entries = []

    for url_id, url in tqdm(url_list.items(), desc="Processing PDFs"):
        if url_id in existing_ids:
            print(f"Skipping {url_id}: already exists in JSON.")
            continue

        pdf_bytes = download_pdf(url)
        if pdf_bytes is None:
            continue

        text = extract_pdf_text(pdf_bytes)

        new_entries.append({
            "id": url_id,
            "url": url,
            "text": text,
            "length": len(text),
            "date": extract_date(text),
            "parsing_from": "pdf"
        })

    combined = existing_data + new_entries

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)

    print(f"\nAppended {len(new_entries)} new entries → {output_json}")
    print(f"Total entries now: {len(combined)}")


def parse_board_html(url):
    """Parse Board of Governors (federalreserve.gov) speech HTML."""
    r = requests.get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # ---- Extract title ----
    # Usually first <h3> or <h4>
    title_tag = soup.find(["h3", "h4"])
    title = title_tag.get_text(" ", strip=True) if title_tag else ""

    # ---- Extract date ----
    # Usually appears as <p class="date">
    date_tag = soup.find("p", class_="date")
    if date_tag:
        date = date_tag.get_text(" ", strip=True)
    else:
        # fallback: date is often the FIRST paragraph before the article section
        p_tags = soup.find_all("p")
        date = p_tags[0].get_text(strip=True) if p_tags else ""

    # ---- Extract main speech text ----
    article_div = soup.find("div", id="article")
    paragraphs = []

    if article_div:
        for p in article_div.find_all("p"):
            txt = p.get_text(" ", strip=True)
            if txt:
                paragraphs.append(txt)

    full_text = "\n\n".join(paragraphs)
    full_text = re.sub(r"\n{2,}", "\n\n", full_text).strip()

    return {
        "title": title,
        "date": date,
        "text": full_text,
        "length": len(full_text)
    }

def parse_nyfed_html(url):
    """Parse New York Fed HTML speech pages."""
    r = requests.get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # Title
    title_div = soup.find("div", class_="ts-title")
    title = title_div.get_text(strip=True) if title_div else ""

    # Date or subtitle block
    date_div = soup.find("div", class_="ts-contact-info")
    date_text = date_div.get_text(" ", strip=True) if date_div else ""

    # Main content container
    article_div = soup.find("div", class_="ts-article-text")

    paragraphs = []
    if article_div:
        for p in article_div.find_all("p"):
            text = p.get_text(" ", strip=True)
            if text:
                paragraphs.append(text)

    full_text = "\n\n".join(paragraphs)
    full_text = re.sub(r"\n{2,}", "\n\n", full_text).strip()

    return {
        "title": title,
        "date": date_text,
        "text": full_text,
        "length": len(full_text)
    }


def extract_bostonfed_html(url):

    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # ---------- TITLE ----------
    title = ""
    t = soup.select_one("div.title-container h1")
    if t:
        title = t.get_text(" ", strip=True)

    # ---------- AUTHOR ----------
    author = ""
    a = soup.select_one("div.author-container")
    if a:
        author = a.get_text(" ", strip=True).replace("By ", "").strip()

    # ---------- DATE ----------
    raw_date = ""
    iso_date = ""

    d = soup.select_one("div.date-container")
    if d:
        raw_date = d.get_text(" ", strip=True)
        try:
            iso_date = parser.parse(raw_date).date().isoformat()
        except:
            iso_date = ""

    # ---------- SPEECH TEXT ----------
    paragraphs = []

    for p in soup.select("div.bodytextlist p"):
        txt = p.get_text(" ", strip=True)
        if txt:
            paragraphs.append(txt)

    full_text = "\n\n".join(paragraphs)

    return {
        "title": title,
        "author": author,
        "date": iso_date,
        "text": full_text,
        "length": len(full_text)
    }

def html_speeches_to_json(url_dict, url_type, output_json="speeches.json"):

    # --- Load existing JSON ---
    if os.path.exists(output_json):
        with open(output_json, "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
                if not isinstance(existing_data, list):
                    existing_data = []
            except json.JSONDecodeError:
                existing_data = []
    else:
        existing_data = []

    existing_ids = {entry["id"] for entry in existing_data}

    new_entries = []

    # --- Loop over HTML URLs ---
    for url_id, url in tqdm(url_dict.items(), desc="Processing HTML Speeches"):

        if url_id in existing_ids:
            print(f"Skipping {url_id}: already in JSON.")
            continue

        if url_type == "newyorkfed":
            parsed = parse_nyfed_html(url)
        elif url_type == "board":
            parsed = parse_board_html(url)
        elif url_type == "dallasfed":
            parsed = extract_dallasfed_html(url)
        elif url_type == "chicagofed":
            parsed = extract_chicagofed_html(url)
        elif url_type == "clevelandfed":
            parsed = extract_clevelandfed_html(url)
        elif url_type == "philadelphiafed":
            parsed = extract_philadelphiafed_html(url)
        elif url_type == "stlouisfed":
            parsed = extract_stlouisfed_html(url)
        elif url_type == "bostonfed":
            parsed = extract_bostonfed_html(url)
        else:
            raise ValueError("Unknown url type")

        new_entries.append({
            "id": url_id,
            "url": url,
            "title": parsed.get("title"),
            "text": parsed.get("text"),
            "length": parsed.get("length"),
            "date": parsed.get("date"),
            "parsing_from": "html"
        })

    # --- Save ---
    combined = existing_data + new_entries

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)

    print(f"\nAppended {len(new_entries)} new HTML entries → {output_json}")
    print(f"Total entries now: {len(combined)}")


def extract_dallasfed_html(url):
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # --- Extract DATE ---
    # Example: "June 23, 2016 New York"
    date_box = soup.select_one("div.dal-inline-list")
    raw_date = ""
    iso_date = ""

    if date_box:
        text = date_box.get_text(" ", strip=True)
        # capture: Month DD, YYYY
        m = re.search(r"[A-Za-z]+\s+\d{1,2},\s+\d{4}", text)
        if m:
            raw_date = m.group(0)
            try:
                iso_date = parser.parse(raw_date).date().isoformat()
            except:
                iso_date = ""

    # --- Extract MAIN SPEECH TEXT ---
    main = soup.select_one("div.dal-main-content")
    parts = []

    if main:
        for tag in main.find_all(["h1", "h2", "h3", "p"]):
            t = tag.get_text(" ", strip=True)
            if t:
                parts.append(t)

    full_text = "\n".join(parts)

    return {
        "date": iso_date,
        "text": full_text,
        "length": len(full_text),
    }


def extract_clevelandfed_html(url):
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # ---------- TITLE ----------
    title = ""
    h1 = soup.select_one("h1.field-title")
    if h1:
        title = h1.get_text(" ", strip=True)

    # ---------- DATE ----------
    raw_date = ""
    iso_date = ""

    date_tag = soup.select_one("span.field-release-date")
    if date_tag:
        raw_date = date_tag.get_text(" ", strip=True)
        raw_date = raw_date.strip()
        try:
            iso_date = parser.parse(raw_date.replace(".", "/")).date().isoformat()
        except:
            iso_date = ""

    # ---------- MAIN TEXT ----------
    paragraphs = []

    # This is the real speech container
    rich_text_blocks = soup.select("div.component.rich-text div.component-content")

    for block in rich_text_blocks:
        for tag in block.find_all(["p", "h2", "h3"]):
            text = tag.get_text(" ", strip=True)
            if text:
                paragraphs.append(text)

    full_text = "\n\n".join(paragraphs)

    return {
        "title": title,
        "date": iso_date,
        "text": full_text,
        "length": len(full_text)
    }

def extract_philadelphiafed_html(url):
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # ---------- TITLE ----------
    title = ""
    h1 = soup.select_one("h1")
    if h1:
        title = h1.get_text(" ", strip=True)

    # ---------- DATE ----------
    raw_date = ""
    iso_date = ""

    date_tag = soup.select_one(".article__meta-date")
    if date_tag:
        raw_date = date_tag.get_text(" ", strip=True).strip()

        # normalize weird apostrophe formats (e.g. "02 Jun ’21")
        raw_date_clean = raw_date.replace("’", "'")
        try:
            iso_date = parser.parse(raw_date_clean).date().isoformat()
        except:
            iso_date = ""

    # ---------- SPEECH TEXT ----------
    paragraphs = []

    body = soup.select_one("div.article-body")
    if body:
        for tag in body.find_all(["p", "h2", "h3"]):
            t = tag.get_text(" ", strip=True)
            if t:
                paragraphs.append(t)

    full_text = "\n\n".join(paragraphs)

    return {
        "title": title,
        "date": iso_date,
        "text": full_text,
        "length": len(full_text),
    }
