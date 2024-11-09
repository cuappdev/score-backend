import requests
from bs4 import BeautifulSoup
import json

def fetch_page(url):
    response = requests.get(url)
    return BeautifulSoup(response.text, 'html.parser')

def extract_teams_and_scores(box_score_section, sport):
    score_table = box_score_section.find('table', class_='sidearm-table')
    team_names = []
    period_scores = []

    for row in score_table.find('tbody').find_all('tr'):
        if sport in ['soccer', 'football', 'baseball', 'lacrosse', 'basketball']:
            team_name_cell = row.find('td')
            if team_name_cell:
                if sport == 'baseball':
                    team_name = ' '.join(span.text.strip() for span in team_name_cell.find_all('span', class_='hide-on-large-down'))
                else:
                    team_name = ' '.join(span.text.strip() for span in team_name_cell.find_all('span', class_='hide-on-small-down'))
            else:
                team_name = "Unknown"
        elif sport in ['hockey']:
            team_name_cell = row.find('th')
            if team_name_cell:
                team_name = team_name_cell.text.strip().replace("Winner", "").strip()
                team_name = ' '.join(team_name.split())
            else:
                team_name = "Unknown"
        
        team_names.append(team_name)
        scores = [td.text.strip() for td in row.find_all('td')[1:]]
        period_scores.append(scores)

    return team_names, period_scores

def soccer_summary(box_score_section):
    summary = []
    scoring_section = box_score_section.find('section', {'aria-label': 'Scoring Summary'})
    if scoring_section:
        scoring_rows = scoring_section.find('tbody').find_all('tr')
        for row in scoring_rows:
            time = row.find_all('td')[0].text.strip()
            team = row.find_all('td')[1].find('img')['alt']
            description = row.find_all('td')[2].text.strip()
            summary.append({'time': time, 'team': team, 'description': description})
    return summary

def football_summary(box_score_section):
    summary = []
    scoring_rows = box_score_section.find('section', {'aria-label': 'Scoring Summary'}).find('tbody').find_all('tr')
    for row in scoring_rows:
        quarter_time = row.find_all('td')[0].text.strip()
        time = row.find_all('td')[1].text.strip()
        description = row.find_all('td')[3].text.strip()
        score_by = description[:3]
        cornell_score = row.find_all('td')[4].text.strip()
        opp_score = row.find_all('td')[5].text.strip()
        summary.append({
            'quarter_time': quarter_time,
            'time': time,
            'score_by': score_by,
            'description': description,
            'cor_score': cornell_score,
            'opp_score': opp_score
        })
    return summary

def hockey_summary(box_score_section):
    summary = []
    scoring_rows = box_score_section.find('table', class_='scoring-summary').find('tbody').find_all('tr')
    for row in scoring_rows:
        period = row.find_all('td')[2].text.strip()
        time = row.find_all('td')[3].text.strip()
        scorer = row.find_all('td')[4].text.strip()
        assist = row.find_all('td')[5].text.strip()
        opp_score = row.find_all('td')[6].text.strip()
        cor_score = row.find_all('td')[7].text.strip()
        power_play_or_short_hand = row.find_all('td')[1].text.strip()
        summary.append({
            'period': period,
            'time': time,
            'scorer': scorer,
            'assist': assist,
            'cor_score': cor_score,
            'opp_score': opp_score,
            'special_play': power_play_or_short_hand
        })
    return summary

def lacrosse_summary(box_score_section):
    summary = []
    scoring_rows = box_score_section.find('table', class_='scoring-summary').find('tbody').find_all('tr')
    for row in scoring_rows:
        period = row.find_all('td')[2].text.strip()
        time = row.find_all('td')[3].text.strip()
        scorer = row.find_all('td')[4].text.strip()
        assist = row.find_all('td')[5].text.strip()
        opp_score = row.find_all('td')[6].text.strip()
        cor_score = row.find_all('td')[7].text.strip()
        summary.append({
            'period': period,
            'time': time,
            'scorer': scorer,
            'assist': assist,
            'cor_score': cor_score,
            'opp_score': opp_score,
        })
    return summary
    

def baseball_summary(box_score_section):
    summary = []
    scoring_rows = box_score_section.find('table', class_='sidearm-table scoring-summary').find('tbody').find_all('tr')
    
    for row in scoring_rows:
        team = row.find_all('td')[1].text.strip()
        period = row.find_all('td')[3].text.strip()
        play_description = row.find_all('td')[4].text.strip()
        cor_score = row.find_all('td')[5].text.strip()
        opp_score = row.find_all('td')[6].text.strip()
        summary.append({
            'team': team,
            'period': period,
            'play_description': play_description,
            'cor_score': cor_score,
            'opp_score': opp_score
        })
    
    return summary

def basketball_play_by_play(soup):
    play_by_play_data = {}

    for period_id in ['period-1', 'period-2']:
        period_section = soup.find(id=period_id)
        if not period_section:
            continue
        
        period_label = "1st Half" if period_id == 'period-1' else "2nd Half"
        play_by_play_data[period_label] = []

        play_rows = period_section.find_all('tr')
        
        for row in play_rows:
            columns = row.find_all('td')
            
            if len(columns) >= 5:
                time = columns[0].text.strip()
                description_left = columns[1].text.strip()
                score_before = columns[2].text.strip()
                team_indicator = columns[3].find('img')['alt'] if columns[3].find('img') else ""
                score_after = columns[4].text.strip()
                description_right = columns[5].text.strip()

                description = description_left if description_left else description_right
                play = {
                    'time': time,
                    'team': team_indicator,
                    'description': description,
                    'score_before': score_before,
                    'score_after': score_after
                }
                play_by_play_data[period_label].append(play)

    return play_by_play_data

def tennis_summary(box_score_section):
    summary = {
        'singles': [],
        'doubles': []
    }
    
    singles_section = box_score_section.find('section', {'aria-label': 'Singles Competition'})
    if singles_section:
        singles_rows = singles_section.find('table', class_='tennis-tournament').find_all('tr')
        for row in singles_rows:
            match_detail = row.find_all('td')[1].text.strip()
            summary['singles'].append(match_detail)
    
    doubles_section = box_score_section.find('section', {'aria-label': 'Doubles Competition'})
    if doubles_section:
        doubles_rows = doubles_section.find('table', class_='tennis-tournament').find_all('tr')
        for row in doubles_rows:
            match_detail = row.find_all('td')[1].text.strip()
            summary['doubles'].append(match_detail)
    
    return summary

def scrape_game(url, sport):
    soup = fetch_page(url)
    if sport == 'baseball':
        box_score_section = soup.find(class_='box-score')
    else:
        box_score_section = soup.find(id='box-score')
        if sport == 'basketball':
            team_names, scores = extract_teams_and_scores(box_score_section, 'basketball')
            play_by_play_data = basketball_play_by_play(soup)
            return {
                'teams': team_names,
                'scores': scores,
                'play_by_play': play_by_play_data
            }
    
    if not box_score_section:
        return {"error": "Box score section not found"}
    
    sport_parsers = {
        'soccer': (lambda: extract_teams_and_scores(box_score_section, 'soccer'), soccer_summary),
        'football': (lambda: extract_teams_and_scores(box_score_section, 'football'), football_summary),
        'hockey': (lambda: extract_teams_and_scores(box_score_section, 'hockey'), hockey_summary),
        'baseball': (lambda: extract_teams_and_scores(box_score_section, 'baseball'), baseball_summary),
        'tennis': (lambda: ([], []), tennis_summary),
        'lacrosse': (lambda: extract_teams_and_scores(box_score_section, 'lacrosse'), lacrosse_summary),
    }

    extract_teams_func, summary_func = sport_parsers.get(sport, (None, None))
    
    if extract_teams_func and summary_func:
        team_names, scores = extract_teams_func()
        scoring_summary = summary_func(box_score_section)

        return {
            'teams': team_names,
            'scores': scores,
            'scoring_summary': scoring_summary
        }
    
    return {"error": "Sport parser not found"}

# print(json.dumps(scrape_game('https://cornellbigred.com/sports/mens-soccer/stats/2024/university-of-pennsylvania/boxscore/59943', 'soccer'), indent=2))
# print(json.dumps(scrape_game('https://cornellbigred.com/sports/sprint-football/stats/2024/molloy-university/boxscore/59894', 'football'), indent=2))
print(json.dumps(scrape_game('https://cornellbigred.com/sports/mens-ice-hockey/stats/2024-25/university-of-toronto/boxscore/59967', 'hockey'), indent=2))
# print(json.dumps(scrape_game('https://cornellbigred.com/sports/baseball/stats/2024/georgia-tech/boxscore/59019', 'baseball'), indent=2))
# print(json.dumps(scrape_game('https://cornellbigred.com/sports/mens-tennis/stats/2024-25/chowderfest-day-1/boxscore/61397', 'tennis'), indent=2))
# print(json.dumps(scrape_game('https://cornellbigred.com/sports/mens-lacrosse/stats/2024/lehigh-university/boxscore/59352', 'lacrosse'), indent=2))
# print(json.dumps(scrape_game('https://cornellbigred.com/sports/mens-basketball/stats/2024-25/marywood-university/boxscore/61143', 'basketball')))
