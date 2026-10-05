#!/usr/bin/env python3
"""Static site generator for completesourcing.com.

Content lives in src/content/{pages,posts}/*.html. Each file starts with a JSON header inside
<!--meta ... --> (title, slug, description, h1, date, faq, ...). This script wraps every file in the
shared layout (header, nav, quote form, footer, JSON-LD schema) and writes the result to the repo
root, which Netlify publishes as-is. Posts dated in the future are skipped, so a weekly rebuild +
push is all it takes to publish scheduled posts.

Usage: python3 src/build.py [--today YYYY-MM-DD]
"""
import datetime as dt
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'
SITE = 'https://completesourcing.com'
BRAND = 'Complete Sourcing'
EMAIL = 'hello@completesourcing.com'

today = dt.date.today()
if '--today' in sys.argv:
    today = dt.date.fromisoformat(sys.argv[sys.argv.index('--today') + 1])

NAV = [('/custom-clamshell-packaging/', 'Clamshells'), ('/blister-packaging/', 'Blister Packaging'),
       ('/custom-rigid-boxes/', 'Rigid Boxes'), ('/custom-bottles-and-jars/', 'Bottles & Jars'),
       ('/packaging-sourcing-agent/', 'How We Work'), ('/blog/', 'Blog')]


def read(path):
    raw = path.read_text(encoding='utf-8')
    m = re.match(r'\s*<!--meta\s*(\{.*?\})\s*-->', raw, re.S)
    if not m:
        raise SystemExit(f'{path}: missing <!--meta {{...}} --> header')
    meta = json.loads(m.group(1))
    meta['body'] = raw[m.end():].strip()
    meta['src'] = path.name
    return meta


def esc(s):
    return html.escape(s, quote=True)


def header():
    links = ''.join(f'<a href="{u}">{t}</a>' for u, t in NAV)
    return f'''<header class="site-header">
      <a class="brand" href="/" aria-label="{BRAND} home">
        <span class="brand-icon" aria-hidden="true"><span></span></span>
        <span class="brand-text">Complete<br>Sourcing</span>
      </a>
      <button class="nav-toggle" type="button" aria-label="Open menu" aria-expanded="false" aria-controls="primaryNav"><span></span><span></span><span></span></button>
      <nav class="nav" id="primaryNav" aria-label="Primary navigation">{links}<a class="nav-quote" href="/free-packaging-quote/">Free Quote</a></nav>
      <a class="button header-button" href="/free-packaging-quote/">Free Quote <span aria-hidden="true">&rarr;</span></a>
    </header>'''


def quote_form(heading='Get a free packaging quote', note=''):
    return f'''<form class="quote-card" name="sourcing-inquiry" method="POST" action="/thanks/" data-netlify="true" netlify-honeypot="bot-field">
      <input type="hidden" name="form-name" value="sourcing-inquiry">
      <p class="hidden-field"><label>Do not fill this out if you are human <input name="bot-field"></label></p>
      <h2>{heading}</h2>
      {f'<p class="form-note">{note}</p>' if note else ''}
      <div class="form-grid">
        <label><span>Full Name</span><input type="text" name="name" autocomplete="name" placeholder="Full Name" required></label>
        <label><span>Email Address</span><input type="email" name="email" autocomplete="email" placeholder="Email Address" required></label>
        <label><span>Company / Brand</span><input type="text" name="company" autocomplete="organization" placeholder="Company / Brand"></label>
        <label><span>Phone Number</span><input type="tel" name="phone" autocomplete="tel" placeholder="Phone (optional)"></label>
      </div>
      <label><span>What do you need?</span>
        <select name="project-type" required>
          <option value="">What are you looking to source?</option>
          <option>Clamshell / blister packaging</option>
          <option>Rigid or magnetic boxes</option>
          <option>Folding cartons / printed boxes</option>
          <option>Bottles / jars</option>
          <option>Something else</option>
        </select>
      </label>
      <label><span>Quantity per order</span>
        <select name="quantity">
          <option value="">Approx. quantity per order</option>
          <option>Under 5,000</option><option>5,000 – 25,000</option><option>25,000 – 100,000</option><option>100,000+</option>
        </select>
      </label>
      <label><span>Project Details</span><textarea name="message" rows="4" required placeholder="Product size, current supplier and price (if you have one), timeline"></textarea></label>
      <button class="button primary form-button" type="submit">Send for a Free Quote <span aria-hidden="true">&rarr;</span></button>
      <p class="secure-note">Free, no obligation. We reply within 1 business day.</p>
    </form>'''


def footer():
    cols = ''.join(f'<li><a href="{u}">{t}</a></li>' for u, t in NAV)
    return f'''<footer class="site-footer">
      <div class="footer-grid">
        <div><p class="footer-brand">{BRAND}</p><p>Custom packaging sourced from vetted overseas factories &mdash; clamshells, blister packs, rigid boxes and bottles, inspected and delivered to your U.S. warehouse.</p>
        <p><a href="mailto:{EMAIL}">{EMAIL}</a></p></div>
        <div><p class="footer-head">Packaging</p><ul>{cols}</ul></div>
        <div><p class="footer-head">Start here</p><ul><li><a href="/free-packaging-quote/">Free packaging quote</a></li><li><a href="/blog/clamshell-packaging-cost/">Clamshell cost guide</a></li><li><a href="/blog/">All articles</a></li></ul></div>
      </div>
      <p class="footer-copy">&copy; {today.year} {BRAND}. All rights reserved.</p>
    </footer>'''


def org_schema():
    return {
        '@type': 'Organization', '@id': f'{SITE}/#org', 'name': BRAND, 'url': SITE + '/',
        'logo': f'{SITE}/assets/favicon.svg', 'email': EMAIL,
        'description': 'Packaging sourcing company: custom clamshells, blister packaging, rigid boxes and bottles '
                       'made by vetted overseas factories, inspected and delivered DDP to the United States.',
        'areaServed': 'US',
        'knowsAbout': ['clamshell packaging', 'blister packaging', 'rigid boxes', 'magnetic gift boxes',
                       'folding cartons', 'plastic bottles', 'pre-shipment inspection', 'DDP freight from China'],
    }


def page(meta, body, schema, crumbs, canonical, noindex=False, og_type='website'):
    title = meta['title']
    desc = meta['description']
    graph = [org_schema(), {'@type': 'WebSite', '@id': f'{SITE}/#site', 'url': SITE + '/', 'name': BRAND, 'publisher': {'@id': f'{SITE}/#org'}}]
    if crumbs:
        graph.append({'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': SITE + u} for i, (n, u) in enumerate(crumbs)]})
    graph += schema
    ld = json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False, indent=1)
    crumb_html = ''
    if crumbs and len(crumbs) > 1:
        crumb_html = '<nav class="crumbs" aria-label="Breadcrumb">' + ' <span>/</span> '.join(
            f'<a href="{u}">{esc(n)}</a>' if i < len(crumbs) - 1 else f'<span aria-current="page">{esc(n)}</span>'
            for i, (n, u) in enumerate(crumbs)) + '</nav>'
    img = SITE + meta.get('image', '/assets/hero-port.png')
    return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{esc(title)}</title>
    <meta name="description" content="{esc(desc)}">
    <link rel="canonical" href="{canonical}">
    {'<meta name="robots" content="noindex">' if noindex else '<meta name="robots" content="index, follow, max-image-preview:large">'}
    <meta property="og:type" content="{og_type}">
    <meta property="og:site_name" content="{BRAND}">
    <meta property="og:title" content="{esc(title)}">
    <meta property="og:description" content="{esc(desc)}">
    <meta property="og:url" content="{canonical}">
    <meta property="og:image" content="{img}">
    <meta name="twitter:card" content="summary_large_image">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
    <link rel="alternate" type="application/rss+xml" title="{BRAND} blog" href="/feed.xml">
    <link rel="stylesheet" href="/styles.css">
    <script type="application/ld+json">
{ld}
    </script>
  </head>
  <body>
    {header()}
    <main id="top">
      {crumb_html}
      {body}
    </main>
    {footer()}
    <script src="/script.js" defer></script>
  </body>
</html>
'''


def faq_html(faq):
    if not faq:
        return ''
    items = ''.join(f'<details><summary>{esc(q)}</summary><p>{a}</p></details>' for q, a in faq)
    return f'<section class="faq"><h2>Frequently asked questions</h2>{items}</section>'


def faq_schema(faq):
    return [{'@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': re.sub('<[^>]+>', '', a)}} for q, a in faq]}] if faq else []


def write(rel, text):
    out = ROOT / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding='utf-8')


def fmt_date(d):
    return dt.date.fromisoformat(d).strftime('%B %-d, %Y')


def main():
    pages = [read(p) for p in sorted((SRC / 'content' / 'pages').glob('*.html'))]
    posts = [read(p) for p in sorted((SRC / 'content' / 'posts').glob('*.html'))]
    live = sorted([p for p in posts if dt.date.fromisoformat(p['date']) <= today], key=lambda p: p['date'], reverse=True)
    staged = [p for p in posts if p not in live]
    urls = []

    # ---- pages ----
    for p in pages:
        slug = p['slug']
        url = '/' if slug == '' else f'/{slug}/'
        canonical = SITE + url
        crumbs = [('Home', '/')] + ([(p.get('crumb', p['h1']), url)] if slug else [])
        schema = faq_schema(p.get('faq'))
        if p.get('service'):
            schema.append({'@type': 'Service', 'name': p['service'], 'serviceType': p['service'], 'provider': {'@id': f'{SITE}/#org'},
                           'areaServed': 'US', 'description': p['description'], 'url': canonical})
        body = p['body'].replace('{{QUOTE_FORM}}', quote_form(p.get('form_heading', 'Get a free packaging quote'), p.get('form_note', '')))
        body = body.replace('{{LATEST_POSTS}}', ''.join(
            f'<a class="post-card" href="/blog/{x["slug"]}/"><span class="post-date">{fmt_date(x["date"])}</span><strong>{esc(x["h1"])}</strong><span>{esc(x["description"])}</span></a>'
            for x in live[:3]))
        body += faq_html(p.get('faq'))
        if p.get('cta', True):
            body += '<section class="cta-band"><div><h2>Paying too much for packaging?</h2><p>Send us your current spec and price. We will come back with a factory-direct, landed (DDP) quote &mdash; free.</p></div><a class="button primary" href="/free-packaging-quote/">Get my free quote <span aria-hidden="true">&rarr;</span></a></section>'
        write(('index.html' if slug == '' else '404.html' if slug == '404' else f'{slug}/index.html'),
              page(p, body, schema, crumbs if slug else [], canonical, noindex=p.get('noindex', False)))
        if not p.get('noindex'):
            urls.append((canonical, p.get('updated', p.get('date', today.isoformat())), '1.0' if slug == '' else '0.9'))

    # ---- posts ----
    for x in live:
        url = f'/blog/{x["slug"]}/'
        canonical = SITE + url
        crumbs = [('Home', '/'), ('Blog', '/blog/'), (x['h1'], url)]
        related = [r for r in live if r is not x][:3]
        rel_html = ''.join(f'<li><a href="/blog/{r["slug"]}/">{esc(r["h1"])}</a></li>' for r in related)
        body = f'''<article class="article">
        <header class="article-head"><p class="section-kicker">{esc(x.get('kicker', 'Packaging sourcing'))}</p><h1>{esc(x['h1'])}</h1>
        <p class="article-meta">By the {BRAND} team &middot; <time datetime="{x['date']}">{fmt_date(x['date'])}</time>{f' &middot; Updated <time datetime="{x["updated"]}">{fmt_date(x["updated"])}</time>' if x.get('updated') else ''}</p>
        <p class="article-lede">{x['description']}</p></header>
        <div class="prose">{x['body']}</div>
        {faq_html(x.get('faq'))}
        <aside class="article-cta">{quote_form('Want these numbers for your product?', 'Send your spec and current price &mdash; we will quote factory-direct, landed at your warehouse.')}</aside>
        {f'<nav class="related"><h2>Keep reading</h2><ul>{rel_html}</ul></nav>' if rel_html else ''}
        </article>'''
        schema = faq_schema(x.get('faq')) + [{
            '@type': 'BlogPosting', 'headline': x['h1'], 'description': x['description'], 'datePublished': x['date'],
            'dateModified': x.get('updated', x['date']), 'mainEntityOfPage': canonical, 'url': canonical,
            'image': SITE + x.get('image', '/assets/hero-port.png'), 'keywords': ', '.join(x.get('keywords', [])),
            'author': {'@type': 'Organization', 'name': BRAND, 'url': SITE + '/'}, 'publisher': {'@id': f'{SITE}/#org'}}]
        write(f'blog/{x["slug"]}/index.html', page(x, body, schema, crumbs, canonical, og_type='article'))
        urls.append((canonical, x.get('updated', x['date']), '0.7'))

    # ---- blog index ----
    cards = ''.join(f'<a class="post-card" href="/blog/{x["slug"]}/"><span class="post-date">{fmt_date(x["date"])}</span><strong>{esc(x["h1"])}</strong><span>{esc(x["description"])}</span></a>' for x in live)
    blog_meta = {'title': 'Packaging Sourcing Blog: Costs, Materials & Shipping | Complete Sourcing',
                 'description': 'Real numbers on clamshell, blister, rigid box and bottle costs, plus how factory-direct sourcing, inspection and DDP freight from China actually work.', 'h1': 'Blog'}
    body = f'<section class="page-hero"><p class="section-kicker">Blog</p><h1>Packaging sourcing, with real numbers</h1><p>{blog_meta["description"]}</p></section><section class="post-grid">{cards}</section>'
    write('blog/index.html', page(blog_meta, body, [{'@type': 'Blog', 'name': f'{BRAND} blog', 'url': SITE + '/blog/', 'publisher': {'@id': f'{SITE}/#org'}}],
                                  [('Home', '/'), ('Blog', '/blog/')], SITE + '/blog/'))
    urls.append((SITE + '/blog/', live[0]['date'] if live else today.isoformat(), '0.8'))

    # ---- sitemap / robots / rss ----
    sm = ''.join(f'<url><loc>{u}</loc><lastmod>{d}</lastmod><priority>{pr}</priority></url>' for u, d, pr in urls)
    write('sitemap.xml', f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>\n')
    write('robots.txt', f'User-agent: *\nAllow: /\nDisallow: /thanks/\n\nSitemap: {SITE}/sitemap.xml\n')
    items = ''.join(f'<item><title>{esc(x["h1"])}</title><link>{SITE}/blog/{x["slug"]}/</link><guid>{SITE}/blog/{x["slug"]}/</guid>'
                    f'<pubDate>{dt.datetime.combine(dt.date.fromisoformat(x["date"]), dt.time(14)).strftime("%a, %d %b %Y %H:%M:%S +0000")}</pubDate>'
                    f'<description>{esc(x["description"])}</description></item>' for x in live)
    write('feed.xml', f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>{BRAND} blog</title><link>{SITE}/blog/</link>'
                      f'<description>Packaging sourcing with real numbers</description>{items}</channel></rss>\n')

    print(f'built {len(pages)} pages, {len(live)} live posts, {len(staged)} scheduled: ' +
          ', '.join(f'{p["slug"]}@{p["date"]}' for p in sorted(staged, key=lambda p: p['date'])))


if __name__ == '__main__':
    main()
