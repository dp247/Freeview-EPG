from lxml import etree
from datetime import datetime, timedelta, time, timezone
import json
import requests

def get_days() -> list[int]:
    now = int(datetime.timestamp(datetime.now()))
    day_1 = int(datetime.timestamp(datetime.combine(datetime.now(), time(0, 0)) + timedelta(1)))
    day_2 = int(datetime.timestamp(datetime.combine(datetime.now(), time(0, 0)) + timedelta(2)))
    return [now, day_1, day_2]

def get_channels_data() -> list:
    data_list = []
    # Load in channels xml file
    x = etree.parse('sky.com.channels.xml')
    data = x.find('channels').getchildren()

    # channels_data.append([c.attrib for c in data])
    for channel in data:
        if channel.items() is not None:
            items = channel.items()
            items.append(('name', channel.text))
            data_list.append(items)

    return data_list

channels_data = get_channels_data()
programs = []
for channel in channels_data:
    epoch_times = get_days()
    for epoch in epoch_times:
        url = f"https://epgservices.sky.com/5.2.2/api/2.0/channel/json/{channel[2][1]}/{epoch}/86400/4"
        req = requests.get(url)
        if req.status_code != 200:
            continue
        result = json.loads(req.text)
        epg_data = result['listings'][f'{channel[2][1]}']
        for item in epg_data:
            title = item['t']
            desc = item['d']
            start = int(item['s'])
            end = int(item['s']) + int(item['m'][1])
            if hasattr(item, "image"):
                icon = f"http://epgstatic.sky.com/epgdata/1.0/paimage/46/1/{item['image']}"
            else:
                icon = None
            ch_name = channel[1][1]

            programs.append({
                "title": title,
                "description": desc,
                "start": start,
                "stop": end,
                "icon": icon,
                "channel": ch_name
            })




print('')
