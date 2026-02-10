#!/usr/bin/env python3
import json
import re
from pathlib import Path

def get_wiki_url(title, country):
    """Find Wikipedia URL based on event title keywords"""
    title_lower = title.lower()
    
    # Russia mappings
    if country == 'RU':
        if 'stalin' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Josef_Stalin'
        if 'lenin' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Vladimir_Lenin'
        if 'trotski' in title_lower or 'trotsky' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Lev_Trotski'
        if 'hrusov' in title_lower or 'khrushchev' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Nikita_Hrusov'
        if 'gorbac' in title_lower or 'gorbachev' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Mihail_Gorbacov'
        if 'putin' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Vladimir_Putin'
        if 'yeltsin' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Boris_Yeltsin'
        if 'stalingrad' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Stalingrad_Muharebesi'
        if 'kursk' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Kursk_Muharebesi'
        if 'leningrad' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Leningrad_Kusatmasi'
        if 'berlin' in title_lower and 'sava' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Berlin_Muharebesi'
        if 'barbarossa' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Barbarossa_Harekati'
        if 'sputnik' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Sputnik_1'
        if 'gagarin' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Yuri_Gagarin'
        if 'holodomor' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Holodomor'
        if 'gulag' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Gulag'
        if 'trotski' in title_lower and 'surgun' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Lev_Trotski'
        if 'kronstadt' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Kronstadt_Ayaklanmasi'
        if 'prag' in title_lower and 'bahar' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Prag_Bahari'
        if 'kuba' in title_lower and 'fuze' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Kuba_Fuze_Krizi'
        if 'ceçen' in title_lower or 'chechen' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Birinci_Cecen_Savasi'
        if 'kirim' in title_lower or 'crimea' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Kirim_in_ilhaki'
        if 'ukrayna' in title_lower and 'isgal' in title_lower:
            return 'https://tr.wikipedia.org/wiki/2022_Rusya_nin_Ukrayna_yi_isgali'
        if 'navalny' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Aleksey_Navalny'
        if 'wagner' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Wagner_isyani'
        if 'soljenitsin' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Aleksandr_Soljenitsin'
        if 'saharov' in title_lower or 'sakharov' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Andrey_Saharov'
        if 'tarkovsky' in title_lower or 'tarkovski' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Andrey_Tarkovski'
        if 'eisenstein' in title_lower or 'eyzen' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Sergey_Eyzensteyn'
        if 'shostakovich' in title_lower or 'sostakovic' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Dmitri_Sostakovic'
        if 'prokofiev' in title_lower or 'prokofyev' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Sergey_Prokofyev'
        if 'mayakovsky' in title_lower or 'mayakovsk' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Vladimir_Mayakovski'
        if 'cernobil' in title_lower or 'chernobyl' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Cernobil_nukleer_faciasi'
        if 'katyn' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Katyn_Katliami'
        if 'glasnost' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Glasnost'
        if 'perestroika' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Perestroyka'
        if 'molotov' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Vyacheslav_Molotov'
        if 'berlin duvari' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Berlin_Duvari'
        if 'helsinki' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Helsinki_Antlasmalari'
        if 'yalta' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Yalta_Konferansi'
        if 'potemkin' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Potemkin_Zirhlisi_(film)'
        if 'sssr' in title_lower and ('kurul' in title_lower or 'cok' in title_lower):
            return 'https://tr.wikipedia.org/wiki/Sovyetler_Birligi'
        if '20. kongre' in title_lower:
            return 'https://tr.wikipedia.org/wiki/20._Parti_Kongresi'
        if 'macaristan' in title_lower and '1956' in title_lower:
            return 'https://tr.wikipedia.org/wiki/1956_Macaristan_ihtilali'
        if 'buyuk tasfiye' in title_lower or 'buyuk temizlik' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Buyuk_Temizlik'
        if 'kolektivizasyon' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Tarimsal_kollektiflestirme'
        if 'bes yillik plan' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Sovyetler_Birligi_nde_sanayilesme'
        
    # China mappings
    if country == 'CN':
        if 'mao' in title_lower and 'zedong' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Mao_Zedong'
        if 'deng' in title_lower and 'xiaoping' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Deng_Xiaoping'
        if 'zhou' in title_lower and 'enlai' in title_lower:
            return 'https://en.wikipedia.org/wiki/Zhou_Enlai'
        if 'jiang' in title_lower and 'qing' in title_lower:
            return 'https://en.wikipedia.org/wiki/Jiang_Qing'
        if 'lin' in title_lower and 'biao' in title_lower:
            return 'https://en.wikipedia.org/wiki/Lin_Biao'
        if 'liu' in title_lower and 'shaoqi' in title_lower:
            return 'https://en.wikipedia.org/wiki/Liu_Shaoqi'
        if 'peng' in title_lower and 'dehuai' in title_lower:
            return 'https://en.wikipedia.org/wiki/Peng_Dehuai'
        if 'chiang' in title_lower or 'kai-shek' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Chiang_Kai-shek'
        if 'sun' in title_lower and 'yat-sen' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Sun_Yat-sen'
        if 'cin komunist' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Cin_Komunist_Partisi'
        if 'kultur devrimi' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Kultur_Devrimi'
        if 'uzun yuruyus' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Uzun_Yuruyus'
        if 'buyuk atilim' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Buyuk_Atilim'
        if 'tibet' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Cin_in_Tibet_i_isgali'
        if 'kore savasi' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Kore_Savasi'
        if 'nanjing' in title_lower or 'nankin' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Nankin_Katliami'
        if 'shanghai' in title_lower and 'katliam' in title_lower:
            return 'https://en.wikipedia.org/wiki/Shanghai_massacre'
        if 'tiananmen' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Tiananmen_Meydani_Olayi'
        if 'hong kong' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Hong_Kong'
        if 'tayvan' in title_lower or 'taiwan' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Tayvan'
        if 'cin ic savas' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Cin_Ic_Savasi'
        if 'cin halk cumhuriyeti' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Cin_Halk_Cumhuriyeti'
        if 'nixon' in title_lower:
            return 'https://tr.wikipedia.org/wiki/1972_Cin_ziyareti'
        if 'bm uyelik' in title_lower:
            return 'https://en.wikipedia.org/wiki/China_and_the_United_Nations'
        if 'ping-pong' in title_lower or 'ping pong' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Ping-pong_diplomasisi'
        if 'kizil muhafiz' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Kizil_Muhafizlar'
        if 'hindistan' in title_lower and 'savas' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Cin-Hindistan_Savasi'
        if 'atom bomb' in title_lower and '1964' in str(title_lower):
            return 'https://en.wikipedia.org/wiki/Project_596'
        if 'mukden' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Mukden_Olayi'
        if 'marco polo' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Marco_Polo_Koprusu_Olayi'
        if 'nanchang' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Nanchang_Ayaklanmasi'
        if 'zunyi' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Zunyi_Konferansi'
        if 'lu xun' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Lu_Xun'
        if 'gang of four' in title_lower or 'dortlu cete' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Dortlu_Cete'
        if 'reform ve acilim' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Reform_ve_Acilim'
        if 'kuzey seferi' in title_lower:
            return 'https://tr.wikipedia.org/wiki/Kuzey_Seferi'
        if 'buyuk kitlik' in title_lower:
            return 'https://en.wikipedia.org/wiki/Great_Chinese_Famine'
    
    return ''

def main():
    with open('data/events.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    events = data['events']
    
    count_ru = 0
    count_cn = 0
    
    for event in events:
        cc = event.get('country_code', '')
        if cc not in ['RU', 'CN']:
            continue
        
        if event.get('wikipedia_url'):
            continue
        
        url = get_wiki_url(event.get('title', ''), cc)
        if url:
            event['wikipedia_url'] = url
            if cc == 'RU':
                count_ru += 1
            else:
                count_cn += 1
    
    with open('data/events.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f'Added Wikipedia URLs:')
    print(f'  Russia: {count_ru}')
    print(f'  China: {count_cn}')

if __name__ == '__main__':
    main()
