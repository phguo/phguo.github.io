# generate_publications.py (APA Style, Sorted by Year and Month)

import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import homogenize_latex_encoding

# =====================================================================================
#  配置部分
# =====================================================================================

URL = "https://guo.ph"
BIB_FILE = 'pub.bib'
OUTPUT_HTML = 'index.html'
PAGE_TITLE = "Publications"

# 月份缩写到数字的映射
MONTH_MAP = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
}

# =====================================================================================
#  脚本主体 (这部分函数不变)
# =====================================================================================

def clean_bibtex_str(text):
    """清理 BibTeX 字符串中的多余大括号。"""
    return text.replace('{', '').replace('}', '')

def format_authors_apa(author_string):
    """将 'Last, First and Last, First' 格式的作者字符串转换为 APA 风格。"""
    authors = [a.strip() for a in author_string.split(' and ')]
    formatted_authors = []
    
    for author in authors:
        if ',' in author:  # "Last, First" 格式
            parts = [p.strip() for p in author.split(',')]
            last_name = parts[0]
            first_names = parts[1].split()
            initials = "".join([f"{name[0]}." for name in first_names])
            formatted_authors.append(f"{last_name}, {initials}")
        else:  # "First Last" 格式 (作为备用)
            parts = author.split()
            last_name = parts[-1]
            initials = "".join([f"{part[0]}." for part in parts[:-1]])
            formatted_authors.append(f"{last_name}, {initials}")

    if not formatted_authors:
        return ""
    if len(formatted_authors) > 1:
        return ", ".join(formatted_authors[:-1]) + f" & {formatted_authors[-1]}"
    else:
        return formatted_authors[0]

def format_apa_citation(entry):
    """根据 bibtex entry 生成 APA 样式的 HTML 字符串。"""
    authors_apa = format_authors_apa(entry.get('author', ''))
    year_apa = f"({entry.get('year', '')})"
    title_apa = clean_bibtex_str(entry.get('title', 'No Title'))
    
    publication_info = ""
    if entry['ENTRYTYPE'] == 'article':
        journal = f"<em>{clean_bibtex_str(entry.get('journal', ''))}</em>"
        volume = entry.get('volume', '')
        number = entry.get('number', '')
        pages = entry.get('pages', '').replace('--', '–')
        
        if volume: journal += f", <em>{volume}</em>"
        if number: journal += f"({number})"
        if pages: journal += f", {pages}"
        
        publication_info = journal + "."
    elif entry['ENTRYTYPE'] == 'inproceedings':
        publication_info = f"<em>{clean_bibtex_str(entry.get('booktitle', ''))}</em>."

    doi_apa = ""
    if 'doi' in entry:
        doi_url = f"https://doi.org/{entry['doi']}"
        doi_apa = f'<a href="{doi_url}" target="_blank">{doi_url}</a>'
        
    citation_parts = [part for part in [authors_apa, year_apa, title_apa + '.', publication_info, doi_apa] if part]
    return " ".join(citation_parts)

def generate_html_from_bib():
    base_url = URL
    
    with open(BIB_FILE, 'r', encoding='utf-8') as bibfile:
        parser = BibTexParser(common_strings=True)
        parser.customization = homogenize_latex_encoding
        bib_database = bibtexparser.load(bibfile, parser=parser)

    # ⭐ 核心修改：按年份和月份排序
    bib_database.entries.sort(
        key=lambda entry: (
            int(entry.get('year', 0)),
            # .get('month', ''): 如果月份不存在，返回空字符串
            # .lower(): 转换为小写，以便与 MONTH_MAP 匹配
            # .get(..., 0): 如果月份无效或不存在，默认为0，排在当年最后
            MONTH_MAP.get(entry.get('month', '').lower()[:3], 0)
        ),
        reverse=True  # 从新到旧排序
    )
    
    # CSS 和 HTML head部分 (不变)
    html_head = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{PAGE_TITLE}</title>
    <style>
        p.citation {{ margin-bottom: 1.5em; line-height: 1.6; text-indent: -2em; padding-left: 2em;}}
        a.pdf-link {{ font-weight: bold; margin-left: 0.5em; }}
    </style>
"""
    html_body_start = f"""
</head>
<body>
    <h1>{PAGE_TITLE}</h1>
"""
    meta_tags_all = ""
    publication_blocks = ""

    # 循环生成内容 (逻辑不变)
    for entry in bib_database.entries:
        entry_id = entry.get('ID')
        if not entry_id:
            print(f"⚠️ Warning: Entry is missing an ID, skipping. Title: {entry.get('title', 'N/A')}")
            continue

        # Google Scholar meta 标签
        meta_tags_all += f"\n    <!-- Metadata for citation: {entry_id} -->\n"
        title_meta = clean_bibtex_str(entry.get("title", ""))
        meta_tags_all += f'    <meta name="citation_title" content="{title_meta}">\n'
        meta_tags_all += f'    <meta name="citation_publication_date" content="{entry.get("year", "")}/{entry.get("month", "01")}">\n' # Google Scholar可以接受更精确的日期
        if 'author' in entry:
            authors = [clean_bibtex_str(author.strip()) for author in entry['author'].split(' and ')]
            for author in authors:
                meta_tags_all += f'    <meta name="citation_author" content="{author}">\n'
        pdf_url = f"{base_url}/pub/{entry_id}.pdf"
        meta_tags_all += f'    <meta name="citation_pdf_url" content="{pdf_url}">\n'
        if 'journal' in entry:
            meta_tags_all += f'    <meta name="citation_journal_title" content="{clean_bibtex_str(entry.get("journal", ""))}">'

        # APA 样式的 HTML 内容块
        apa_citation_html = format_apa_citation(entry)
        
        publication_blocks += f"""    <p class="citation">
        {apa_citation_html}
        <a href="./pub/{entry_id}.pdf" target="_blank" class="pdf-link">[PDF]</a>
    </p>\n"""

    html_body_end = """</body>
</html>"""

    final_html = html_head + meta_tags_all + html_body_start + publication_blocks + html_body_end
    
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(final_html)

    print(f"✅ Successfully generated '{OUTPUT_HTML}' with APA style, sorted by date (year and month).")


if __name__ == "__main__":
    generate_html_from_bib()
