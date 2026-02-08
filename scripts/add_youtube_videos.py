import json
import re

def add_youtube_videos(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    events = data.get('events', [])
    
    # Mapping of criteria to youtube_video_id
    # Criteria: (country_name, year_range_start, year_range_end, title_regex)
    video_mappings = [
        ("Filipinler", 1986, 1988, r"Gerilla|Akvino|Aquino", "0rF0S48Xegs"),
        ("Azerbaycan", 1989, 1991, r"Kara Ocak|Black January|Azerbaycan", "vz8_zOgnVgg"),
        ("Almanya", 1989, 1991, r"Birle[sş]me", "X6pg4KT7Da4"),
        ("Irak", 1990, 1992, r"Körfez|Gulf", "W0JA9b_uMKs"),
        ("Kuveyt", 1990, 1992, r"İşgal|Occupation|Körfez", "W0JA9b_uMKs"),
        ("Bosna Hersek", 1991, 1996, r"Sava[sş]|Srebrenica", "ngDfMflSwD8"),
        ("Turkiye", 1974, 1975, r"Kıbrıs|Barış Harek", "9owC4fHLRIc"),
        ("Kuzey Kıbrıs", 1974, 1975, r"Barış Harek", "9owC4fHLRIc"),
        ("Kuzey Kıbrıs", 1995, 1997, r"Kardak", "_xi9B1nsCBQ"),
        ("Turkiye", 1995, 1997, r"Kardak", "_xi9B1nsCBQ"),
        ("Turkiye", 1980, 1981, r"12 Eylül|Darbe", "SOnjYp6M_rE"),
        ("Turkiye", 1998, 2000, r"Öcalan|Apo", "3iQfB_6j8mI"),
        ("Vietnam", 1974, 1976, r"Sava[sş]|Sona|Fall of Saigon", "T8CNo97GNo0"), # Generic 32. Gun Vietnam id if found
    ]
    
    changed_count = 0
    for event in events:
        for country, y_start, y_end, title_re, video_id in video_mappings:
            if event.get('country_name') == country:
                if y_start <= event.get('year', 0) <= y_end:
                    if re.search(title_re, event.get('title', ''), re.IGNORECASE) or re.search(title_re, event.get('description', ''), re.IGNORECASE):
                        event['youtube_video_id'] = video_id
                        changed_count += 1
                        break # Only one video per event
                        
    if changed_count > 0:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Updated {changed_count} events with YouTube videos.")
    else:
        print("No matches found for YouTube videos.")

if __name__ == "__main__":
    add_youtube_videos('data/events.json')
