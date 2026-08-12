#!/usr/bin/env python3
"""
Aktualisiert data/nav.json ohne API-Key.

Strategie:
1) Historie über die finanzen.net-Historienseite mit Playwright auslesen.
2) Aktuellen NAV zusätzlich aus öffentlich sichtbaren Seiten lesen.
3) Neue Werte mit vorhandener JSON-Historie zusammenführen.

Wenn eine Quelle ihre HTML-Struktur ändert, bleibt die bereits gespeicherte Historie
erhalten; der Workflow schlägt nur dann hart fehl, wenn überhaupt kein Wert vorhanden ist.
"""
from __future__ import annotations
import json, re, sys, time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"nav.json"
ISIN="LU2936783674"
HIST_URL="https://www.finanzen.net/fonds/historisch/santander-santander-target-maturity-euro-iv-ad-income-lu2936783674"
DETAIL_URL="https://www.dasinvestment.com/fonds/detail/LU2936783674"
FIN_URL="https://www.finanzen.net/fonds/santander-santander-target-maturity-euro-iv-ad-income-lu2936783674"

def de_num(s:str)->float:
    s=s.replace("\xa0"," ").strip().replace(".","").replace(",",".")
    return float(re.sub(r"[^0-9.\-]","",s))

def norm_date(s:str)->str|None:
    s=s.strip()
    for fmt in ("%d.%m.%Y","%d.%m.%y"):
        try:return datetime.strptime(s,fmt).date().isoformat()
        except ValueError:pass
    return None

def http_text(url:str)->str:
    req=Request(url,headers={"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"})
    with urlopen(req,timeout=30) as r:
        return r.read().decode("utf-8","ignore")

def parse_current_from_text(text:str):
    flat=" ".join(BeautifulSoup(text,"html.parser").stripped_strings)
    # DAS INVESTMENT: NAV ... 101,44 EUR ... 10.08.2026
    patterns=[
      r"NAV.{0,180}?(\d{2,3},\d{2,4})\s*EUR.{0,180}?(\d{2}\.\d{2}\.\d{4})",
      r"(\d{2,3},\d{2,4})\s*EUR.{0,100}?(\d{2}\.\d{2}\.\d{2,4}).{0,60}?NAV",
      r"Nettoinventarwert.{0,160}?(\d{2,3},\d{2,4})\s*EUR.{0,160}?(\d{2}\.\d{2}\.\d{2,4})"
    ]
    for pat in patterns:
        m=re.search(pat,flat,re.I)
        if m:
            d=norm_date(m.group(2))
            try:v=de_num(m.group(1))
            except:continue
            if d and 70<v<140:return {"date":d,"close":round(v,4)}
    return None

def fetch_current():
    for name,url in [("DAS INVESTMENT",DETAIL_URL),("finanzen.net",FIN_URL)]:
        try:
            item=parse_current_from_text(http_text(url))
            if item:
                print("Aktuell:",name,item)
                return item,name
        except Exception as e:
            print("Aktuell-Quelle fehlgeschlagen:",name,e)
    return None,None

def parse_tables(html:str):
    soup=BeautifulSoup(html,"html.parser")
    found={}
    for tr in soup.select("tr"):
        cells=[" ".join(c.stripped_strings) for c in tr.select("th,td")]
        if not cells:continue
        di=None; d=None
        for i,c in enumerate(cells):
            mm=re.search(r"\b(\d{2}\.\d{2}\.(?:\d{2}|\d{4}))\b",c)
            if mm:
                d=norm_date(mm.group(1));di=i;break
        if not d:continue
        nums=[]
        for c in cells[di+1:]:
            for m in re.finditer(r"(?<!\d)(\d{2,3}[.,]\d{2,4})(?!\d)",c):
                try:
                    v=de_num(m.group(1))
                    if 70<v<140: nums.append(v)
                except: pass
        if nums:
            # Bei Fonds-Historie ist der erste plausible NAV-Wert der Zeile relevant.
            found[d]=round(nums[0],4)
    return [{"date":d,"close":v} for d,v in sorted(found.items())]

def fetch_history_playwright():
    from playwright.sync_api import sync_playwright
    start=(datetime.now().date()-timedelta(days=50)).strftime("%d.%m.%Y")
    end=datetime.now().date().strftime("%d.%m.%Y")
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        page=browser.new_page(viewport={"width":1400,"height":1000},locale="de-DE")
        page.goto(HIST_URL,wait_until="domcontentloaded",timeout=90000)
        time.sleep(2)
        # Cookie-Dialoge best effort schließen
        for txt in ["Alle akzeptieren","Akzeptieren","Zustimmen","Accept all"]:
            try:
                b=page.get_by_role("button",name=re.compile(txt,re.I))
                if b.count(): b.first.click(timeout=1500); break
            except: pass

        filled=False
        # zuerst semantische IDs/Namen
        starts=page.locator('input[name*="start" i],input[id*="start" i],input[placeholder*="start" i]')
        ends=page.locator('input[name*="end" i],input[id*="end" i],input[placeholder*="end" i]')
        try:
            if starts.count() and ends.count():
                starts.first.fill(start);ends.first.fill(end);filled=True
        except: pass

        # Fallback: Form suchen, dessen Text Historische Kurse enthält
        if not filled:
            for i in range(page.locator("form").count()):
                form=page.locator("form").nth(i)
                try: txt=form.inner_text(timeout=1000)
                except: continue
                if "Historische" not in txt and "Startdatum" not in txt: continue
                inputs=form.locator('input:not([type="hidden"]):not([type="submit"]):not([type="button"])')
                if inputs.count()>=2:
                    try:
                        inputs.nth(0).fill(start);inputs.nth(1).fill(end);filled=True;break
                    except: pass

        # Letzter Fallback: sichtbare Datumsfelder
        if not filled:
            candidates=page.locator('input[type="text"],input[type="date"]')
            vis=[]
            for i in range(candidates.count()):
                try:
                    if candidates.nth(i).is_visible():vis.append(candidates.nth(i))
                except:pass
            if len(vis)>=2:
                try:
                    vis[0].fill(start);vis[1].fill(end);filled=True
                except:pass

        # Submit
        clicked=False
        for selector in [
            'button:has-text("Historische Kurse anzeigen")',
            'input[type="submit"][value*="Historische"]',
            'button:has-text("Suchen")',
            'input[type="submit"]'
        ]:
            try:
                loc=page.locator(selector)
                if loc.count() and loc.first.is_visible():
                    loc.first.click(timeout=5000);clicked=True;break
            except:pass
        if clicked:
            try: page.wait_for_load_state("networkidle",timeout=30000)
            except: time.sleep(4)
        else:
            time.sleep(3)

        html=page.content()
        browser.close()
    values=parse_tables(html)
    print("Historie:",len(values),"Werte")
    return values

def load_existing():
    try:return json.loads(DATA.read_text(encoding="utf-8"))
    except:return {"values":[]}

def main():
    old=load_existing()
    merged={x["date"]:float(x["close"]) for x in old.get("values",[]) if x.get("date") and x.get("close") is not None}
    sources=[]

    try:
        hist=fetch_history_playwright()
        if len(hist)>=5:
            for x in hist: merged[x["date"]]=x["close"]
            sources.append("finanzen.net Historie")
    except Exception as e:
        print("Historienabruf fehlgeschlagen:",repr(e))

    cur,src=fetch_current()
    if cur:
        merged[cur["date"]]=cur["close"];sources.append(src)

    if not merged:
        raise SystemExit("Kein NAV-Wert verfügbar.")

    cutoff=(datetime.now().date()-timedelta(days=120)).isoformat()
    vals=[{"date":d,"close":v} for d,v in sorted(merged.items()) if d>=cutoff]
    payload={
      "isin":ISIN,
      "wkn":"A40US6",
      "source":" + ".join(dict.fromkeys(sources)) if sources else old.get("source","gespeicherte NAV-Daten"),
      "updated_at":datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z"),
      "values":vals
    }
    DATA.parent.mkdir(parents=True,exist_ok=True)
    DATA.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Gespeichert:",len(vals),"Werte; letzter:",vals[-1])

if __name__=="__main__":
    main()
