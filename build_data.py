#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RACEHUB data builder.
Fetches public endpoints, normalises them into data.json / data.js.
Run:  python build_data.py
"""
from __future__ import annotations

import json
import os
import re
import ssl
import sys
import time as _time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
CST = timezone(timedelta(hours=8))
# 每日自动构建时以实际日期为准；本地也可用 RACEHUB_TODAY 固定快照日期。
TODAY = date.fromisoformat(os.environ["RACEHUB_TODAY"]) if os.environ.get("RACEHUB_TODAY") else datetime.now(CST).date()

TEAM_COLORS = {
    "mercedes": "#27F4D2", "ferrari": "#E8002D", "red_bull": "#3671C6",
    "mclaren": "#FF8000", "rb": "#6692FF", "alpine": "#FF87BC",
    "haas": "#B6BABD", "audi": "#52E252", "williams": "#64C4FF",
    "aston_martin": "#229971", "cadillac": "#C6C6C6", "sauber": "#52E252",
}


def log(msg: str) -> None:
    print(msg, flush=True)


def http(url: str, payload=None, headers=None, tries: int = 3):
    h = {"User-Agent": UA, "Accept": "*/*"}
    if headers:
        h.update(headers)
    body = None
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        h["Content-Type"] = "application/json;charset=UTF-8"
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, data=body, headers=h)
            with urllib.request.urlopen(req, timeout=45,
                                        context=ssl.create_default_context()) as r:
                return r.read()
        except Exception as exc:  # noqa: BLE001
            last = exc
            if attempt < tries - 1:
                _time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"GET failed: {url} :: {last}")


def get_text(url: str, headers=None) -> str:
    return http(url, headers=headers).decode("utf-8", "replace")


def get_json(url: str):
    return json.loads(get_text(url))


def clean(text) -> str:
    if text is None:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------- F1
def build_f1():
    base = "https://api.jolpi.ca/ergast/f1/current"
    races = get_json(f"{base}/races.json?limit=100")["MRData"]["RaceTable"]["Races"]
    ds = get_json(f"{base}/driverstandings.json?limit=100")["MRData"]["StandingsTable"]["StandingsLists"][0]["DriverStandings"]
    cs = get_json(f"{base}/constructorstandings.json?limit=100")["MRData"]["StandingsTable"]["StandingsLists"][0]["ConstructorStandings"]
    last = get_json(f"{base}/last/results.json?limit=100")["MRData"]["RaceTable"]["Races"][0]

    # All completed race results, paginated: used by the detail drawer.
    all_results = {}
    offset = 0
    while True:
        page = get_json(f"{base}/results.json?limit=100&offset={offset}")
        meta = page["MRData"]
        for race in meta["RaceTable"]["Races"]:
            rows = []
            for res in race.get("Results", []):
                rows.append({
                    "pos": int(res.get("position", 0)),
                    "driver": f'{res["Driver"]["givenName"]} {res["Driver"]["familyName"]}',
                    "code": res["Driver"].get("code", ""),
                    "team": res["Constructor"]["name"],
                    "grid": int(res.get("grid", 0)),
                    "points": float(res.get("points", 0)),
                    "laps": int(res.get("laps", 0)),
                    "status": res.get("status", ""),
                    "time": (res.get("Time") or {}).get("time", ""),
                    "fastest": (res.get("FastestLap") or {}).get("rank") == "1",
                })
            all_results[int(race["round"])] = rows
        offset += 100
        if offset >= int(meta.get("total", 0)):
            break


    out_races = []
    for r in races:
        d = r["date"]
        t = r.get("time", "14:00:00Z")
        dt = datetime.fromisoformat(d + "T" + t.replace("Z", "+00:00"))
        out_races.append({
            "round": int(r["round"]),
            "name": r["raceName"],
            "circuit": r["Circuit"]["circuitName"],
            "locality": r["Circuit"]["Location"].get("locality", ""),
            "country": r["Circuit"]["Location"].get("country", ""),
            "date": d,
            "time": t,
            "datetime": iso(dt),
            "sprint": "Sprint" in r,
            "past": date.fromisoformat(d) < TODAY,
            "results": all_results.get(int(r["round"]), []),
        })

    nxt = next((r for r in out_races if not r["past"]), out_races[-1] if out_races else None)

    drivers = []
    for d in ds:
        ctor = (d.get("Constructors") or [{}])[0]
        drivers.append({
            "rank": int(d["position"]),
            "name": f'{d["Driver"]["givenName"]} {d["Driver"]["familyName"]}',
            "lastName": d["Driver"]["familyName"],
            "code": d["Driver"].get("code", ""),
            "nationality": d["Driver"].get("nationality", ""),
            "team": ctor.get("name", ""),
            "teamId": ctor.get("constructorId", ""),
            "color": TEAM_COLORS.get(ctor.get("constructorId", ""), "#8a8f98"),
            "points": float(d["points"]),
            "wins": int(d["wins"]),
        })

    constructors = []
    for c in cs:
        ctor = c["Constructor"]
        constructors.append({
            "rank": int(c["position"]),
            "name": ctor["name"],
            "id": ctor.get("constructorId", ""),
            "color": TEAM_COLORS.get(ctor.get("constructorId", ""), "#8a8f98"),
            "nationality": ctor.get("nationality", ""),
            "points": float(c["points"]),
            "wins": int(c["wins"]),
        })

    results = last.get("Results", [])
    podium = []
    for res in results[:3]:
        podium.append({
            "pos": int(res["position"]),
            "driver": f'{res["Driver"]["givenName"]} {res["Driver"]["familyName"]}',
            "code": res["Driver"].get("code", ""),
            "team": res["Constructor"]["name"],
            "teamId": res["Constructor"].get("constructorId", ""),
            "color": TEAM_COLORS.get(res["Constructor"].get("constructorId", ""), "#8a8f98"),
            "time": (res.get("Time") or {}).get("time") or res.get("status", ""),
            "grid": int(res.get("grid", 0)),
            "points": float(res.get("points", 0)),
            "laps": int(res.get("laps", 0)),
        })
    fastest = next((r for r in results if (r.get("FastestLap") or {}).get("rank") == "1"), None)
    fl = None
    if fastest:
        fl = {"driver": f'{fastest["Driver"]["givenName"]} {fastest["Driver"]["familyName"]}',
              "time": fastest["FastestLap"].get("Time", {}).get("time", "")}

    return {
        "season": races[0]["season"] if races else "2026",
        "next": nxt,
        "last": {
            "round": int(last["round"]),
            "name": last["raceName"],
            "locality": last["Circuit"]["Location"].get("locality", ""),
            "country": last["Circuit"]["Location"].get("country", ""),
            "date": last["date"],
            "podium": podium,
            "fastestLap": fl,
        },
        "drivers": drivers,
        "constructors": constructors,
        "races": out_races,
    }


# ---------------------------------------------------------------- FE
def build_fe():
    html = get_text("https://www.fiaformulae.com/en/calendar")
    m = re.search(r'<script type="application/ld\+json" id="calendar-schema">(.*?)</script>', html, re.S)
    if not m:
        raise RuntimeError("FE calendar schema not found")
    schema = json.loads(m.group(1))
    items = schema.get("itemListElement", [])
    races = []
    weekend_id = 0
    prev = None
    for it in items:
        ev = it.get("item", {})
        loc = ev.get("location", {}) or {}
        start = ev.get("startDate") or ev.get("endDate") or ""
        end = ev.get("endDate") or start
        if prev is None or loc.get("name") != prev.get("location") or (
                start and prev.get("start") and
                (date.fromisoformat(start) - date.fromisoformat(prev["start"])).days > 4):
            weekend_id += 1
        races.append({
            "round": int(it.get("position") or len(races) + 1),
            "name": ev.get("name", ""),
            "location": loc.get("name", ""),
            "country": (loc.get("address") or {}).get("addressCountry", ""),
            "start": start,
            "end": end,
            "weekend": weekend_id,
            "past": bool(start) and date.fromisoformat(start) < TODAY,
        })
        prev = {"location": loc.get("name", ""), "start": start}

    races.sort(key=lambda r: r["start"])
    for i, r in enumerate(races, 1):
        r["round"] = i
    nxt = next((r for r in races if not r["past"]), races[-1] if races else None)
    return {
        "season": "13",
        "total": len(races),
        "completed": sum(1 for r in races if r["past"]),
        "next": nxt,
        "races": races,
    }


# ---------------------------------------------------------------- scoregg (LoL)
def scoregg(tid: str):
    html = get_text(f"https://www.scoregg.com/match_pc?tournamentID={tid}")
    m = re.search(r"var\s+t_data\s*=\s*", html)
    if not m:
        raise RuntimeError(f"scoregg t_data not found for {tid}")
    data, _ = json.JSONDecoder().raw_decode(html[m.end():])
    return data


def build_worlds():
    d = scoregg("1023")
    meta = (d.get("tournament_list") or [{}])[0]
    stats = d.get("statistics") or {}
    groups = (d.get("team_point_list") or {}).get("2262") or []
    teams_raw = groups[0].get("list", []) if groups else []
    teams = []
    for i, t in enumerate(teams_raw):
        w, l = int(t.get("match_win", 0) or 0), int(t.get("match_lose", 0) or 0)
        rw, rl = int(t.get("result_win", 0) or 0), int(t.get("result_lose", 0) or 0)
        if w >= 3:
            status = "晋级"
        elif l >= 3:
            status = "淘汰"
        else:
            status = "争夺中"
        teams.append({
            "rank": i + 1,
            "name": t.get("team_short_name") or t.get("team_name", ""),
            "logo": t.get("team_image", ""),
            "w": w, "l": l, "rw": rw, "rl": rl,
            "diff": rw - rl,
            "rate": round(w / (w + l) * 100) if w + l else 0,
            "status": status,
        })

    t_start = meta.get("start_date") or stats.get("start_date") or "2026-10-16"
    t_end = meta.get("end_date") or stats.get("end_date") or "2026-11-16"
    logo_map = {t["name"]: t["logo"] for t in teams}
    matches = []
    for m in d.get("this_week_match") or []:
        raw = clean(m.get("start_time", ""))
        dt = None
        mm = re.match(r"(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{2})", raw)
        if mm:
            month, day, hour, minute = map(int, mm.groups())
            year = int(t_start[:4])
            if month < 6:
                year += 1
            dt = datetime(year, month, day, hour, minute, tzinfo=CST)
        a, b = int(m.get("team_a_win", 0) or 0), int(m.get("team_b_win", 0) or 0)
        finished = bool(m.get("status") in (2, "2")) or (a or b)
        ta, tb = m.get("team_a_name", ""), m.get("team_b_name", "")
        if not ta or not tb or "待定" in (ta, tb):
            continue
        stage_name = m.get("stage_name") or "瑞士轮"
        matches.append({
            "date": dt.isoformat() if dt else raw,
            "dateLabel": raw,
            "teamA": ta,
            "teamB": tb,
            "logoA": m.get("team_a_image") or logo_map.get(ta, ""),
            "logoB": m.get("team_b_image") or logo_map.get(tb, ""),
            "scoreA": a, "scoreB": b,
            # game_count 是单场上限，不等于系列赛制；瑞士轮固定 BO3。
            "bo": "3" if "瑞士" in stage_name else "5",
            "status": "已结束" if finished else "未开始",
            "stage": stage_name,
        })
    matches.sort(key=lambda x: x["date"])

    return {
        "id": "1023",
        "name": d.get("tournament_name") or meta.get("name") or "S16 全球总决赛",
        "start": t_start,
        "end": t_end,
        "stage": "瑞士轮",
        "format": "16 队瑞士轮 · BO3 · 前 8 晋级淘汰赛",
        "teams": teams,
        "matches": matches,
        "stats": {
            "games": int(stats.get("game_count", 0) or 0),
            "avgGame": stats.get("avg_game_time", ""),
            "blueWin": stats.get("blue_win_rate", ""),
            "redWin": stats.get("red_win_rate", ""),
            "penta": stats.get("pentaKills", "0"),
        },
    }


def build_lpl():
    d = scoregg("1007")
    meta = (d.get("tournament_list") or [{}])[0]
    stats = d.get("statistics") or {}
    rounds = (d.get("team_point_list") or {}).get("2223") or []
    groups = []
    for g in rounds:
        teams = []
        for i, t in enumerate(g.get("list", [])):
            w, l = int(t.get("match_win", 0) or 0), int(t.get("match_lose", 0) or 0)
            rw, rl = int(t.get("result_win", 0) or 0), int(t.get("result_lose", 0) or 0)
            teams.append({
                "rank": i + 1,
                "name": t.get("team_short_name") or t.get("team_name", ""),
                "logo": t.get("team_image", ""),
                "w": w, "l": l, "rw": rw, "rl": rl,
                "diff": rw - rl,
                "rate": round(w / (w + l) * 100) if w + l else 0,
                "points": t.get("match_points", ""),
            })
        groups.append({"name": g.get("letter") or "积分榜", "teams": teams})
    groups.sort(key=lambda x: 0 if "登峰" in x["name"] else 1)
    return {
        "id": "1007",
        "name": d.get("tournament_name") or meta.get("name") or "2026 LPL 第三赛段",
        "start": meta.get("start_date") or stats.get("start_date") or "2026-07-22",
        "end": meta.get("end_date") or stats.get("end_date") or "2026-09-13",
        "groups": groups,
    }


# ---------------------------------------------------------------- VCT (vlr.gg)
def _vlr_datetime(date_label: str, time_label: str):
    date_label = re.sub(r"\s+(Yesterday|Today|Tomorrow)\s*$", "", clean(date_label), flags=re.I)
    try:
        d = datetime.strptime(date_label, "%a, %B %d, %Y").date()
    except ValueError:
        return ""
    if time_label:
        try:
            t = datetime.strptime(clean(time_label).replace(" ", ""), "%I:%M%p").time()
            return datetime.combine(d, t, tzinfo=CST).isoformat()
        except ValueError:
            pass
    return datetime.combine(d, datetime.min.time(), tzinfo=CST).isoformat()


def _parse_vlr_page(url: str, limit: int):
    from lxml import html as LH

    doc = LH.fromstring(get_text(url))
    current_date = ""
    out = []
    for el in doc.xpath('//div[contains(@class,"wf-label") and contains(@class,"mod-large")] | //a[contains(@class,"match-item")]'):
        cls = el.get("class", "")
        if el.tag == "div" and "wf-label" in cls:
            current_date = clean(el.text_content())
            continue
        if el.tag != "a" or "match-item" not in cls:
            continue
        tm = el.xpath('.//div[contains(@class,"match-item-time")]')
        team_els = el.xpath('.//div[contains(@class,"match-item-vs-team-name")]')
        score_els = el.xpath('.//div[contains(@class,"match-item-vs-team-score")]')
        ev_els = el.xpath('.//div[contains(@class,"match-item-event")]')
        st_els = el.xpath('.//div[contains(@class,"ml-status")]')
        if len(team_els) < 2 or not ev_els:
            continue
        parts = [clean(p) for p in re.split(r"\s{2,}|\n", ev_els[0].text_content()) if clean(p)]
        parts.sort(key=len, reverse=True)
        title = parts[0] if parts else ""
        stage = " · ".join(parts[1:]) if len(parts) > 1 else ""
        time_label = clean(tm[0].text_content()) if tm else ""
        status_raw = clean(st_els[0].text_content()) if st_els else ""
        status = {"Upcoming": "未开始", "Live": "进行中", "Final": "已结束", "Completed": "已结束"}.get(status_raw, status_raw or "未开始")
        out.append({
            "date": _vlr_datetime(current_date, time_label),
            "dateLabel": current_date,
            "time": time_label,
            "teamA": clean(team_els[0].text_content()),
            "teamB": clean(team_els[1].text_content()),
            "scoreA": clean(score_els[0].text_content()) if len(score_els) > 0 else "",
            "scoreB": clean(score_els[1].text_content()) if len(score_els) > 1 else "",
            "event": title,
            "stage": stage,
            "status": status,
        })
        if len(out) >= limit:
            break
    return out


def build_vct():
    from lxml import html as LH  # bundled with the DSH runtime

    doc = LH.fromstring(get_text("https://www.vlr.gg/rankings"))
    regions = []
    for col in doc.xpath('//div[contains(@class,"world-rankings-col")]'):
        h2 = col.xpath('.//h2')
        if not h2:
            continue
        region = clean(h2[0].text_content())
        teams = []
        for tr in col.xpath('.//tr'):
            rank_td = tr.xpath('.//td[contains(@class,"rank-item-rank")]')
            team_td = tr.xpath('.//td[contains(@class,"rank-item-team")]')
            rate_td = tr.xpath('.//td[contains(@class,"rank-item-rating")]')
            if not (rank_td and team_td):
                continue
            name_div = team_td[0].xpath('.//div')
            name = clean(name_div[0].xpath('text()')[0]) if name_div and name_div[0].xpath('text()') else clean(team_td[0].text_content())
            country = ""
            sub = team_td[0].xpath('.//div[contains(@class,"rank-item-team-country")]')
            if sub:
                country = clean(sub[0].text_content())
            img = team_td[0].xpath('.//img')
            logo = img[0].get("src", "") if img else ""
            if logo.startswith("//"):
                logo = "https:" + logo
            teams.append({
                "rank": int(re.sub(r"\D", "", clean(rank_td[0].text_content())) or len(teams) + 1),
                "name": name,
                "country": country,
                "logo": logo,
                "points": int(re.sub(r"\D", "", clean(rate_td[0].text_content())) or 0) if rate_td else 0,
            })
        regions.append({"name": region, "teams": teams})

    upcoming = _parse_vlr_page("https://www.vlr.gg/matches", 18)
    recent_all = _parse_vlr_page("https://www.vlr.gg/matches/results", 120)
    recent = [m for m in recent_all
              if re.search(r"VCT|Champions|Masters|Game Changers", m["event"], re.I)][:8]
    return {"regions": regions, "upcoming": upcoming, "results": recent}


# ---------------------------------------------------------------- KPL
def build_kpl():
    base = "https://kplshop-op.timi-esports.qq.com/kplow"
    hdr = {"Origin": "https://kpl.qq.com", "Referer": "https://kpl.qq.com/"}
    seasons = json.loads(http(base + "/getSeasonAndStageAndTeamList", {"seasonid": ""}, hdr))["data"]["seasons"]
    season = next((s for s in seasons if int(s.get("is_cur_season", 0)) == 1), seasons[0])
    sid = season["seasonid"]
    progress = json.loads(http(base + "/getScheduleProgress", {"seasonid": sid}, hdr))["data"]["stage_list"]
    schedule = json.loads(http(base + "/getScheduleList", {"seasonid": sid, "page": 1, "pagesize": 500}, hdr))["data"]["list"]

    stages = []
    for st in progress:
        groups = []
        for g in st.get("groups", []):
            teams = []
            for i, t in enumerate(g.get("teams", [])):
                teams.append({
                    "rank": i + 1,
                    "name": t.get("team_name", ""),
                    "logo": t.get("team_logo", ""),
                    "wins": int(t.get("wins", 0) or 0),
                    "losses": int(t.get("losses", 0) or 0),
                    "net": int(t.get("net_score", 0) or 0),
                    "points": int(t.get("points", 0) or 0),
                })
            groups.append({"name": g.get("group_name", "积分榜"), "teams": teams})
        stages.append({
            "id": st.get("stage_id", ""),
            "name": st.get("stage_name", ""),
            "start": (st.get("start_time") or "")[:10],
            "end": (st.get("end_time") or "")[:10],
            "groups": groups,
        })

    matches = []
    for m in schedule:
        ts = int(m.get("start_timestamp", 0) or 0)
        dt = datetime.fromtimestamp(ts, CST) if ts else None
        status_code = m.get("schedule_status")
        a, b = m.get("team_a_score"), m.get("team_b_score")
        if status_code == 4:
            status = "已结束"
        elif status_code == 1:
            status = "未开始"
        else:
            status = "进行中" if dt and dt <= datetime.now(CST) else "未开始"
        matches.append({
            "id": m.get("scheduleid", ""),
            "stage": m.get("stage_name", ""),
            "stageId": m.get("stageid", ""),
            "date": dt.isoformat() if dt else "",
            "dateLabel": dt.strftime("%m-%d %H:%M") if dt else "",
            "teamA": m.get("team_a_name", ""),
            "teamB": m.get("team_b_name", ""),
            "logoA": m.get("team_a_logo", ""),
            "logoB": m.get("team_b_logo", ""),
            "scoreA": int(a) if a is not None else None,
            "scoreB": int(b) if b is not None else None,
            "bo": int(m.get("bo_total", 0) or 0),
            "format": m.get("competition_format", ""),
            "location": m.get("location_name", ""),
            "status": status,
        })
    matches.sort(key=lambda x: x["date"] or "9999")

    # 官方 stage_list 的顺序不完全是时间顺序（附加赛排在最后），
    # 且总决赛的 start_time 可能为 0。用实际比赛日期补全并按时间排序。
    for st in stages:
        own = [m for m in matches if m["stage"] == st["name"] and m["date"]]
        if own and (not st["start"] or st["start"] == "0"):
            st["start"] = own[0]["date"][:10]
        if own and (not st["end"] or st["end"] == "0"):
            st["end"] = own[-1]["date"][:10]
    stages.sort(key=lambda s: (s["start"] or "9999-12-31", s["name"] == "总决赛"))

    return {
        "season": sid,
        "name": season.get("season_name", "2026KPL年度总决赛"),
        "start": datetime.fromtimestamp(int(season["start_time"]), CST).date().isoformat(),
        "end": datetime.fromtimestamp(int(season["end_time"]), CST).date().isoformat(),
        "stages": stages,
        "matches": matches,
    }


# ---------------------------------------------------------------- IVL
def build_ivl():
    url = ("https://comp-sync.webapp.163.com/h55_schedule_result/free_convey"
           "?competition_uuid=DoxM4ZyMUhcu&callback=cb")
    text = get_text(url)
    m = re.search(r"cb\((.*)\)\s*;?\s*$", text, re.S)
    if not m:
        raise RuntimeError("IVL JSONP envelope not found")
    payload = json.loads(m.group(1))
    rows = payload["data"]["data"]
    matches = []
    for r in rows:
        raw = r.get("scheduleStartDatetime") or ""
        dt = None
        if raw:
            try:
                dt = datetime.strptime(raw, "%Y-%m-%d %H:%M").replace(tzinfo=CST)
            except ValueError:
                dt = None
        a, b = r.get("teamAWinAmount"), r.get("teamBWinAmount")
        st = r.get("scheduleStatus")
        if st == 0 and a is None:
            status = "未开始"
        elif st == 1:
            status = "进行中"
        else:
            status = "已结束"
        matches.append({
            "id": r.get("scheduleID"),
            "stage": r.get("competitionStageName", ""),
            "date": dt.isoformat() if dt else "",
            "dateLabel": dt.strftime("%m-%d %H:%M") if dt else raw,
            "teamA": r.get("teamAName", ""),
            "teamB": r.get("teamBName", ""),
            "abbrA": r.get("teamAAbbr", ""),
            "abbrB": r.get("teamBAbbr", ""),
            "logoA": r.get("teamALogoUrl", ""),
            "logoB": r.get("teamBLogoUrl", ""),
            "scoreA": int(a) if a is not None else None,
            "scoreB": int(b) if b is not None else None,
            "status": status,
        })
    matches.sort(key=lambda x: x["date"] or "9999")
    stage_order = []
    for m in matches:
        if m["stage"] and m["stage"] not in stage_order:
            stage_order.append(m["stage"])
    return {
        "name": "2026 IVL 秋季赛",
        "start": "2026-09-28",
        "end": "2027-01-03",
        "stages": stage_order,
        "matches": matches,
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    data = {"generatedAt": datetime.now(CST).isoformat(timespec="seconds"),
            "today": TODAY.isoformat(),
            "sources": [
                {"name": "Jolpica · Formula 1", "url": "https://api.jolpi.ca/ergast/f1/current/"},
                {"name": "FIA Formula E", "url": "https://www.fiaformulae.com/en/calendar"},
                {"name": "ScoreGG · LoL", "url": "https://www.scoregg.com/"},
                {"name": "VLR.GG · Valorant", "url": "https://www.vlr.gg/"},
                {"name": "KPL 官方赛事", "url": "https://kpl.qq.com/"},
                {"name": "IVL 官方赛事", "url": "https://ivl.163.com/"},
            ]}

    steps = [("f1", build_f1), ("fe", build_fe), ("lol", lambda: {"worlds": build_worlds(), "lpl": build_lpl()}),
             ("vct", build_vct), ("kpl", build_kpl), ("ivl", build_ivl)]
    for key, fn in steps:
        try:
            log(f"[build] {key} ...")
            data[key] = fn()
            log(f"[build] {key} OK")
        except Exception as exc:  # noqa: BLE001
            log(f"[build] {key} FAILED: {exc}")
            raise

    (ROOT / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "data.js").write_text("window.RACEHUB_DATA = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n",
                                  encoding="utf-8")
    log(f"[build] wrote {ROOT / 'data.js'}")


if __name__ == "__main__":
    main()
