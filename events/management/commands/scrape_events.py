import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Scrape upcoming UFC events'
    
    def handle(self, *args, **options):
        def scrape_fight_card(event_url):
            """Scrape the fight card from an event page"""
            try:
                res = requests.get(event_url)
                soup = BeautifulSoup(res.content, 'html.parser')
                
                fights = []
                
            
                print(f"Page title: {soup.title.string if soup.title else 'No title'}")
                
                #h3 on ufc.com
                all_h3 = soup.find_all('h3')
                print(f"Found {len(all_h3)} h3 elements on the page")
                for i, h3 in enumerate(all_h3[:10]):  # Show first 10
                    print(f"h3 #{i}: {h3.get_text().strip()}")
                
                selectors_to_try = [
                    'h3.c-listing-fight__corner-name',
                    '.c-listing-fight__corner-name',
                    '[class*="fighter-name"]',
                    '[class*="corner-name"]',
                    'h3[class*="name"]'
                ]
                
                for selector in selectors_to_try:
                    fighter_elements = soup.select(selector)
                    if fighter_elements:
                        print(f"Found {len(fighter_elements)} elements with selector: {selector}")
                        for i, fighter in enumerate(fighter_elements):
                            print(f"Fighter {i}: {fighter.get_text().strip()}")
                        
                        # pair up fighter 1 and 2
                        for i in range(0, len(fighter_elements), 2):
                            if i + 1 < len(fighter_elements):
                                #clean names \n after first+last
                                fighter1 = fighter_elements[i].get_text().strip().replace('\n', ' ')
                                fighter2 = fighter_elements[i + 1].get_text().strip().replace('\n', ' ')
                                
                                # remove extra spaces
                                fighter1 = ' '.join(fighter1.split())
                                fighter2 = ' '.join(fighter2.split())
                                
                                fights.append({
                                    "fighter1": fighter1,
                                    "fighter2": fighter2
                                })
                        break  
                
                # find vs if needed
                if not fights:
                    vs_elements = soup.find_all(string=lambda text: text and ' vs ' in text)
                    for vs_text in vs_elements:
                        parts = vs_text.split(' vs ')
                        if len(parts) == 2:
                            fighter1 = parts[0].strip().replace('\n', ' ')
                            fighter2 = parts[1].strip().replace('\n', ' ')
                            fighter1 = ' '.join(fighter1.split())
                            fighter2 = ' '.join(fighter2.split())
                            
                            fights.append({
                                "fighter1": fighter1,
                                "fighter2": fighter2
                            })
                
                return fights
            except Exception as e:
                print(f"Error scraping fight card: {e}")
                return []

        cur_time = datetime.now()
        res = requests.get('https://www.ufc.com/events')
        soup = BeautifulSoup(res.content, 'html.parser')

        articles = soup.select("article.c-card-event--result")
        print(f"Found {len(articles)} events")

        # find upcoming event
        next_event = None
        next_event_time = None
        
        for a in articles:
            date_tag = a.find("div", class_="c-card-event--result__date")
            if not date_tag:
                continue

            ev_date_ts = date_tag.get("data-main-card-timestamp")
            if not ev_date_ts:
                continue

            ev_time = datetime.fromtimestamp(int(ev_date_ts))

            # future events
            if ev_time > cur_time:
                a_tag = a.find("a", href=lambda h: h and h.startswith("/event/"))
                if a_tag:
                    name_tag = a.find("h3", class_="c-card-event--result__headline") or a_tag
                    event_name = name_tag.get_text().strip() if name_tag else "Unknown Event"
                    
                    # get rid of \n after arena + location
                    location_tag = a.find("div", class_="c-card-event--result__location")
                    location = location_tag.get_text().strip().replace('\n', ' ') if location_tag else "TBD"
                    
                    event_data = {
                        "name": event_name,
                        "date": ev_time.strftime("%B %d, %Y"),
                        "location": location,
                        "url": f"https://www.ufc.com{a_tag['href']}"
                    }
                    
                    # next event 
                    if next_event is None or ev_time < next_event_time:
                        next_event = event_data
                        next_event_time = ev_time

        if next_event:
            print("Next upcoming UFC event:")
            print(f"Name: {next_event['name']}")
            print(f"Date: {next_event['date']}")
            print(f"Location: {next_event['location']}")
            
            # fight card scrape
            print("Scraping fight card...")
            fights = scrape_fight_card(next_event['url'])
            next_event['fights'] = fights
            print(f"Found {len(fights)} fights")
            
            # save to json
            with open("next_event.json", "w") as f:
                json.dump(next_event, f, indent=2)
            print("Saved next upcoming event with fight card to next_event.json")
        else:
            print("No upcoming events found")