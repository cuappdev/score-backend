import requests
from bs4 import BeautifulSoup
from src.utils.constants import *

def fetch_page(url):
    response = requests.get(url)
    return BeautifulSoup(response.text, 'html.parser')

def extract_teams_and_scores(box_score_section, sport):
    score_table = box_score_section.find(TAG_TABLE, class_=CLASS_SIDEARM_TABLE)
    team_names = []
    period_scores = []

    for row in score_table.find(TAG_TBODY).find_all(TAG_TR):
        team_name_cell = row.find(TAG_TH) if sport == 'ice hockey' else row.find(TAG_TD)
        if team_name_cell:
            team_name = team_name_cell.text.strip().replace("Winner", "").strip()
            team_name = ' '.join(team_name.split())
        else:
            team_name = "Unknown"
        
        team_names.append(team_name)
        scores = [td.text.strip() for td in row.find_all(TAG_TD)[1:]]
        scores = scores[:-1] if sport == 'basketball' else scores
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
                
                if team == "COR" or team == "CU":
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
            
            if team == "COR" or team == "CU":
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
                period = row.find_all(TAG_TD)[2].text.strip()
                time = row.find_all(TAG_TD)[3].text.strip()
                scorer = row.find_all(TAG_TD)[4].text.strip()
                assist = row.find_all(TAG_TD)[5].text.strip()
                opp_score = row.find_all(TAG_TD)[7].text.strip()
                cor_score = row.find_all(TAG_TD)[6].text.strip()
                summary.append({
                    'period': period,
                    'time': time,
                    'scorer': scorer,
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