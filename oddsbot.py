import requests
from datetime import datetime

markets_url = "https://api.norsk-tipping.no/OddsenGameInfo/v1/api/markets/"
events_url_template = "https://api.norsk-tipping.no/OddsenGameInfo/v1/api/events/FBL/{start}/{end}"
headers = {
    'Accept': 'application/json;charset=utf-8'
}

def get_events_today():
    today = datetime.now()
    start_of_day = today.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y%m%d%H%M")
    end_of_day = today.replace(hour=23, minute=59, second=59, microsecond=0).strftime("%Y%m%d%H%M")
    
    events_url = events_url_template.format(start=start_of_day, end=end_of_day)
    response = requests.get(events_url, headers=headers)
    if response.status_code == 200:
        data = response.json()
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")
        return None
    
    euro_events = [event for event in data['eventList'] if 'Europa - EM' in event.get('tournament', {}).get('name', '')]
    events_data = []

    # Loop through filtered events and collect necessary event data
    for event in euro_events:
        event_data = {
            'eventId': event.get('eventId'),
            'homeParticipant': event.get('homeParticipant'),
            'awayParticipant': event.get('awayParticipant')
        }
        events_data.append(event_data)

    return events_data

def get_sports_results(event_id):
    url = f"{markets_url}{event_id}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to retrieve data for event ID {event_id}. Status code: {response.status_code}")
        return None

def print_most_likely_results(events_data):
    for event in events_data:
        event_id = event['eventId']
        home_team = event['homeParticipant']
        away_team = event['awayParticipant']
        
        data = get_sports_results(event_id)
        
        if data is None:
            continue
        
        # Retrieve odds for H (Home), B (Away), and U (Draw)
        h_odds = b_odds = u_odds = None
        probabilities = {}
        for market in data.get('markets', []):
            if market.get('marketName') == 'HUB':
                for selection in market.get('selections', []):
                    if selection.get('selectionValue') == 'H':
                        h_odds = selection.get('selectionOdds')
                    elif selection.get('selectionValue') == 'A':
                        b_odds = selection.get('selectionOdds')
                    elif selection.get('selectionValue') == 'D':
                        u_odds = selection.get('selectionOdds')

            if market.get('marketName') == "Korrekt resultat":
                selections = market.get('selections')
                
                if not selections:
                    continue
                
                # Sort the selections by the lowest odds
                sorted_selections = sorted(selections, key=lambda x: float(x['selectionOdds']))

                # Calculate probabilities and expected points
                expected_points = {}
                draw_selections = []
                for selection in sorted_selections:
                    selection_name = selection.get('selectionName')
                    selection_odds = selection.get('selectionOdds')
                    probability = 1 / float(selection_odds)
                    probabilities[selection_name] = probability
                    if "Uavgjort" in selection_name:
                        expected_points[selection_name] = 3 * probability
                        draw_selections.append((selection_name, selection_odds, expected_points[selection_name]))
                    else:
                        expected_points[selection_name] = 3 * probability + 2 * (1 - probability)

                # Sort by expected points and get the top four
                top_selections = sorted(expected_points.items(), key=lambda x: x[1], reverse=True)[:4]

                # Find the most likely draw result
                most_likely_draw = draw_selections[0] if draw_selections else None

                # Prepare the message
                match_info = f"{home_team} vs {away_team} | H: {h_odds}, B: {b_odds}, U: {u_odds}"
                headers = f"{'Resultat':<30} {'XP':<11} {'%':<6}"
                message = f"{match_info}\n"
                message += headers + "\n"
                for selection_name, xp in top_selections:
                    selection_odds = next(sel['selectionOdds'] for sel in sorted_selections if sel['selectionName'] == selection_name)
                    percentage = 100 / float(selection_odds)
                    message += f"{selection_name:<30} {xp:<10.2f} {percentage:>5.1f} %\n"

                # Add the most likely draw result as the last row
                if most_likely_draw:
                    draw_name, draw_odds, draw_xp = most_likely_draw
                    draw_percentage = 100 / float(draw_odds)
                    message += f"{draw_name:<30} {draw_xp:<10.2f} {draw_percentage:>5.1f} %\n"

                print(message)

if __name__ == "__main__":
    today = datetime.today()
    print(f"EM-profeten anbefaling for {today.day}.{today.month}:\n")
    events_data = get_events_today()
    if events_data:
        print_most_likely_results(events_data)
    print("Beregninger gjort med odds fra Norsk Tipping")