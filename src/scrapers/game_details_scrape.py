import re
import requests
from bs4 import BeautifulSoup
from src.utils.constants import *

def clean_name(name):
    """Strip extra information from player names, keeping only first and last name."""
    # try to match firstname, lastname format
    if ',' in name:
        match = re.match(r'^([^,]+),\s*(\w+)', name)
        if match:
            return f"{match.group(1)}, {match.group(2)}"
    else:
        match = re.match(r'^(\w+)\s+(\w+)', name)
        if match:
            return f"{match.group(1)} {match.group(2)}"
    
    # fallback for removing common extra characters
    cleaned = re.sub(r'\s*\([^)]*\).*$', '', name)
    cleaned = re.sub(r'\s*\d+.*$', '', cleaned)
    cleaned = cleaned.strip()
    return cleaned

def fetch_page(url):
    response = requests.get(url)
    return BeautifulSoup(response.text, 'html.parser')

def extract_teams_and_scores(box_score_section, sport):
    score_table = box_score_section.find(TAG_TABLE, class_=CLASS_SIDEARM_TABLE)
    team_names = []
    period_scores = []

    for row in score_table.find(TAG_TBODY).find_all(TAG_TR):
        # Check if team name is in <th> (some sports) or first <td> (other sports)
        team_name_cell = row.find(TAG_TH)
        if team_name_cell:
            # Team name is in <th>, all <td> elements are period scores
            team_name = team_name_cell.text.strip().replace("Winner", "").strip()
            scores = [td.text.strip() for td in row.find_all(TAG_TD)]
        else:
            # Team name is in first <td>, remaining <td> elements are period scores
            team_name_cell = row.find(TAG_TD)
            team_name = team_name_cell.text.strip().replace("Winner", "").strip() if team_name_cell else "Unknown"
            scores = [td.text.strip() for td in row.find_all(TAG_TD)[1:]]
        
        # Basketball box score includes a "Records" column at the end - exclude it
        if sport == 'basketball' and scores:
            scores = scores[:-1]
        
        team_name = ' '.join(team_name.split())
        team_names.append(team_name)
        period_scores.append(scores)

    return team_names, period_scores

def soccer_summary(box_score_section):
    summary = []
    scoring_section = box_score_section.find(TAG_SECTION, {ATTR_ARIA_LABEL: LABEL_SCORING_SUMMARY})
    if scoring_section:
        scoring_rows = scoring_section.find(TAG_TBODY)
        if scoring_rows:
            cornell_score = 0
            opp_score = 0
            for row in scoring_rows.find_all(TAG_TR):
                time = row.find_all(TAG_TD)[0].text.strip()
                team = row.find_all(TAG_TD)[1].find(TAG_IMG)[ATTR_ALT]
                event = row.find_all(TAG_TD)[2]
                desc = event.find_all(TAG_SPAN)[-1].text.strip()
                
                if team == "COR" or team == "CU" or team == "CRNL":
                    cornell_score += 1
                else:
                    opp_score += 1
                    
                summary.append({
                    'time': time, 
                    'team': team, 
                    'description': desc,
                    'cor_score': cornell_score,
                    'opp_score': opp_score
                })
    if not summary:
        summary = [{"message": "No scoring events in this game."}]
    return summary

def football_summary(box_score_section):
    summary = []
    scoring_section = box_score_section.find(TAG_SECTION, {ATTR_ARIA_LABEL: LABEL_SCORING_SUMMARY})
    if scoring_section:
        scoring_rows = scoring_section.find(TAG_TBODY)
        if scoring_rows:
            for row in scoring_rows.find_all(TAG_TR):
                period = row.find_all(TAG_TD)[1].text.strip()
                time = row.find_all(TAG_TD)[0].text.strip()
                description = row.find_all(TAG_TD)[3].text.strip()
                cornell_score = row.find_all(TAG_TD)[4].text.strip()
                opp_score = row.find_all(TAG_TD)[5].text.strip()
                description_parts = description.split(' - ', 1)
                team = description_parts[0].strip() if len(description_parts) > 1 else ""
                summary.append({
                    'team': team,
                    'period': period,
                    'time': time,
                    'description': description,
                    'cor_score': cornell_score,
                    'opp_score': opp_score
                })
    if not summary:
        summary = [{"message": "No scoring events in this game."}]
    return summary

def hockey_summary(box_score_section):
    summary = []
    scoring_table = box_score_section.find(TAG_TABLE, class_=CLASS_SCORING_SUMMARY)
    if scoring_table:
        scoring_rows = scoring_table.find(TAG_TBODY)
        if scoring_rows:
            cornell_score = 0
            opp_score = 0
            for row in scoring_rows.find_all(TAG_TR):
                team = row.find_all(TAG_TD)[1].find(TAG_IMG)[ATTR_ALT]
                period = row.find_all(TAG_TD)[2].text.strip()
                time = row.find_all(TAG_TD)[3].text.strip()
                scorer = row.find_all(TAG_TD)[4].text.strip()
                assist = row.find_all(TAG_TD)[5].text.strip()
                
                if team == "COR" or team == "CU" or team == "Cornell":
                    cornell_score += 1
                else:
                    opp_score += 1

                summary.append({
                    'team': team,
                    'period': period,
                    'time': time,
                    'scorer': scorer,
                    'assist': assist,
                    'cor_score': cornell_score,
                    'opp_score': opp_score,
                })
    if not summary:
        summary = [{"message": "No scoring events in this game."}]
    return summary

def field_hockey_summary(box_score_section):
    summary = []
    scoring_rows = box_score_section.find(TAG_TABLE, class_=CLASS_OVERALL_STATS).find(TAG_TBODY)
    if scoring_rows:
        cornell_score = 0
        opp_score = 0
        for row in scoring_rows.find_all(TAG_TR):
            time = row.find_all(TAG_TD)[0].text.strip()
            team = row.find_all(TAG_TD)[1].find(TAG_IMG)[ATTR_ALT]
            event = row.find_all(TAG_TD)[2]
            desc = event.find_all(TAG_SPAN)[-1].text.strip()
            
            if team == "COR" or team == "CU" or team == "CORFH" or team == "CORNELL":
                cornell_score += 1
            else:
                opp_score += 1
                
            summary.append({
                'time': time,
                'team': team,
                'description': desc,
                'cor_score': cornell_score,
                'opp_score': opp_score
            })
    if not summary:
        summary = [{"message": "No scoring events in this game."}]
    return summary

def lacrosse_summary(box_score_section):
    summary = []
    scoring_table = box_score_section.find(TAG_TABLE, class_=CLASS_SCORING_SUMMARY)
    if scoring_table:
        scoring_rows = scoring_table.find(TAG_TBODY)
        if scoring_rows:
            for row in scoring_rows.find_all(TAG_TR):
                team = row.find_all(TAG_TD)[1].find(TAG_IMG)[ATTR_ALT]
                period = row.find_all(TAG_TD)[2].text.strip()
                time = row.find_all(TAG_TD)[3].text.strip()
                scorer = clean_name(row.find_all(TAG_TD)[4].text.strip())
                assist = clean_name(row.find_all(TAG_TD)[5].text.strip())
                opp_score = row.find_all(TAG_TD)[7].text.strip()
                cor_score = row.find_all(TAG_TD)[6].text.strip()
                
                if assist and assist != "Unassisted":
                    desc = f"Scored by {scorer}, assisted by {assist}"
                else:
                    desc = f"Scored by {scorer}"

                summary.append({
                    'team': team,
                    'period': period,
                    'time': time,
                    'scorer': scorer,
                    'description': desc,
                    'assist': assist,
                    'cor_score': cor_score,
                    'opp_score': opp_score,
                })
    if not summary:
        summary = [{"message": "No scoring events in this game."}]
    return summary

def baseball_summary(box_score_section):
    summary = []
    scoring_rows = box_score_section.find(TAG_TABLE, class_=CLASS_SIDEARM_TABLE + " " + CLASS_SCORING_SUMMARY)
    if scoring_rows:
        scoring_rows = scoring_rows.find(TAG_TBODY)
        if scoring_rows:
            for row in scoring_rows.find_all(TAG_TR):
                team = row.find_all(TAG_TD)[1].text.strip()
                period = row.find_all(TAG_TD)[3].text.strip()
                desc_td = row.find_all(TAG_TD)[4]
                desc = ''.join(desc_td.find_all(text=True, recursive=False)).strip()
                cor_score = row.find_all(TAG_TD)[5].text.strip()
                opp_score = row.find_all(TAG_TD)[6].text.strip()
                summary.append({
                    'team': team,
                    'period': period,
                    'description': desc,
                    'cor_score': cor_score,
                    'opp_score': opp_score
                })
    if not summary:
        summary = [{"message": "No scoring events in this game."}]
    return summary

# def basketball_summary(box_score_section):
#     summary = []
#     scoring_section = box_score_section.find(TAG_SECTION, {ATTR_ARIA_LABEL: LABEL_SCORING_SUMMARY})
#     if scoring_section:
#         scoring_rows = scoring_section.find(TAG_TBODY)
#         if scoring_rows:
#             cornell_score = 0
#             opp_score = 0
#             for row in scoring_rows.find_all(TAG_TR):
#                 time = row.find_all(TAG_TD)[0].text.strip()
#                 team = row.find_all(TAG_TD)[1].find(TAG_IMG)[ATTR_ALT]
#                 event = row.find_all(TAG_TD)[2]
#                 desc = event.find_all(TAG_SPAN)[-1].text.strip()
                
#                 if team == "COR" or team == "CU" or team == "CRNL":
#                     cornell_score += 1
#                 else:
#                     opp_score += 1
                    
#                 summary.append({
#                     'time': time, 
#                     'team': team, 
#                     'description': desc,
#                     'cor_score': cornell_score,
#                     'opp_score': opp_score
#                 })
#     if not summary:
#         summary = [{"message": "No scoring events in this game."}]
#     return summary

def scrape_game(url, sport):
    soup = fetch_page(url)
    box_score_section = soup.find(class_=CLASS_BOX_SCORE) if sport in ['baseball', 'softball'] else soup.find(id=ID_BOX_SCORE)
    if not box_score_section:
        return {"error": "Box score section not found"}
    
    sport_parsers = {
        'soccer': (lambda: extract_teams_and_scores(box_score_section, 'soccer'), soccer_summary),
        'football': (lambda: extract_teams_and_scores(box_score_section, 'football'), football_summary),
        'ice hockey': (lambda: extract_teams_and_scores(box_score_section, 'ice hockey'), hockey_summary),
        'field hockey': (lambda: extract_teams_and_scores(box_score_section, 'field hockey'), field_hockey_summary),
        'lacrosse': (lambda: extract_teams_and_scores(box_score_section, 'lacrosse'), lacrosse_summary),
        'baseball': (lambda: extract_teams_and_scores(box_score_section, 'baseball'), baseball_summary),
        'basketball': (lambda: extract_teams_and_scores(box_score_section, 'basketball'), lambda _: []),
    }

    extract_teams_func, summary_func = sport_parsers.get(sport, (None, None))
    
    if extract_teams_func and summary_func:
        team_names, scores = extract_teams_func()
        scoring_summary = summary_func(box_score_section)
        
        for event in scoring_summary:
            if not event.get("time") and event.get("period"):
                event["time"] = event["period"]
                
        return {
            'teams': team_names,
            'scores': scores,
            'scoring_summary': scoring_summary or [{"message": "No scoring events in this game."}]
        }
    
    return {"error": "Sport parser not found"}