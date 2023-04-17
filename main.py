from lxml import etree
from datetime import datetime, timedelta, time, timezone
import json
import requests
import pytz

def get_days() -> list[int]:
    """
Generate epoch times for now, midnight tomorrow, and midnight the next day
    :return: List of epoch times
    """
    now = int(datetime.timestamp(datetime.now()))
    day_1 = int(datetime.timestamp(datetime.combine(datetime.now(), time(0, 0)) + timedelta(1)))
    day_2 = int(datetime.timestamp(datetime.combine(datetime.now(), time(0, 0)) + timedelta(2)))
    return [now, day_1, day_2]

def get_channels_data() -> list:
    """
Load XML file of channel information
    :return: XML elements as a set, then all sets as a list
    """
    data_list = []
    x = etree.parse('freeview_channels.xml')
    data = x.find('channels').getchildren()

    for element in data:
        if element.items() is not None:
            items = element.items()
            items.append(('name', element.text))
            data_list.append(items)

    return data_list

def build_xmltv(channels: list, programmes: list) -> bytes:
    """
Make the channels and programmes into something readable by XMLTV
    :param channels: The list of channels to be generated
    :param programmes: The list of programmes to be generated
    :return: A sequence of bytes for XML
    """
    # Timezones since UK has daylight savings
    dt_format = '%Y%m%d%H%M%S %z'
    tz = pytz.timezone('Europe/London')

    data = etree.Element("tv")
    data.set("generator-info-name", "sky-epg-parser")
    data.set("generator-info-url", "https://github.com/dp247/Freeview-EPG")
    for ch in channels:
        channel = etree.SubElement(data, "channel")
        channel.set("id", ch[1][1])
        name = etree.SubElement(channel, "display-name")
        name.set("lang", "en")
        name.text = ch[3][1]

    for pr in programmes:
        programme = etree.SubElement(data, 'programme')
        start_time = datetime.fromtimestamp(pr.get('start'), tz).strftime(dt_format)
        end_time = datetime.fromtimestamp(pr.get('stop'), tz).strftime(dt_format)

        programme.set("channel", pr.get('channel'))
        programme.set("start", start_time)
        programme.set("stop", end_time)

        title = etree.SubElement(programme, "title")
        title.set('lang', 'en')
        title.text = pr.get("title")

        if pr.get('description') is not None:
            description = etree.SubElement(programme, "desc")
            description.set('lang', 'en')
            description.text = pr.get("description")

        if pr.get('icon') is not None:
            icon = etree.SubElement(programme, "icon")
            icon.set('src', pr.get("icon"))

    return etree.tostring(data, pretty_print=True, encoding='utf-8')

# Load the channels data
channels_data = get_channels_data()

programme_data = []
for channel in channels_data:
    print(channel[1][1])
    # Get some epoch times - right now, 12am tomorrow and 12am the day after tomorrow (so 48h)
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
            desc = item['d'] if 'd' in item else None
            start = int(item['s'])
            end = int(item['s']) + int(item['m'][1])
            icon = f"http://epgstatic.sky.com/epgdata/1.0/paimage/46/1/{item['image']}" if 'image' in item else None
            ch_name = channel[1][1]

            programme_data.append({
                "title": title,
                "description": desc,
                "start": start,
                "stop": end,
                "icon": icon,
                "channel": ch_name
            })

channel_xml = build_xmltv(channels_data, programme_data)

with open('epg.xml', 'wb') as f:
    f.write(channel_xml)
    f.close()

