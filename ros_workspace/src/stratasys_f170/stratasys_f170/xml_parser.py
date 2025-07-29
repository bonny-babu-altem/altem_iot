import json
from typing import Any
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element


NS: dict[str, str] = {
    'm': 'urn:mtconnect.org:MTConnectStreams:1.5'
}


def parse_type(
        xml_data: Element,
        component_id: str, debug: bool) -> list[dict[str, Any]]:
    count: int = 0

    parsed_data: list[dict[str, Any]] = []

    for sample in xml_data:
        tag: str = sample.tag.split('}')[-1]
        value: str | None = sample.text
        attrs: dict[str, str] = sample.attrib

        item_data: dict[str, Any] = {
            'name': f'{component_id}_{attrs.get("dataItemId")}',
            'value': value,
            'type': tag,
            'sub_type': attrs.get("subType")
        }

        parsed_data.append(item_data)

        if debug:
            count = count + 1
            print(item_data)

    if debug:
        print(count)

    return parsed_data


def type_1(element: Element) -> None | dict[str, Any]:
    clean_data: dict[str, Any] = {}

    comp_name: str | None = element.get('name')
    comp_id: str | None = element.get('componentId')
    component: str | None = element.get('component')

    debug: bool = True if component == '' else False

    if component is None or comp_id is None:
        return None

    clean_data[component] = {
        'tag': [
            {
                'id': comp_id,
                'name': comp_name,
                'data': []
            }
        ]

    }

    events: Element | None = element.find('m:Events', NS)
    samples: Element | None = element.find('m:Samples', NS)

    if events is None and samples is None:
        print("⚠️ No <data> in this component.")
        return None

    if events:
        event_data: list[dict[str, Any]] = parse_type(
            xml_data=events,
            component_id=comp_id,
            debug=debug
        )

        for item in event_data:
            clean_data[component]['tag'][0]['data'].append(item)

    if samples:
        sample_data: list[dict[str, Any]] = parse_type(
            xml_data=samples,
            component_id=comp_id,
            debug=debug
        )
        for item in sample_data:
            clean_data[component]['tag'][0]['data'].append(item)

    if debug:
        print(json.dumps(clean_data, indent=4))

    return clean_data


def parse_data(xml_data: str) -> None | dict[str, Any]:
    root: Element = ET.fromstring(xml_data)
    streams: Element | None = root.find('m:Streams', NS)

    if streams is None:
        print("⚠️ No <Streams> found.")
        return None

    data: dict[str, Any] = {}

    for device_stream in streams.findall('m:DeviceStream', NS):

        for comp_stream in device_stream.findall('m:ComponentStream', NS):
            cleaned_data: None | dict[str, Any] = type_1(comp_stream)

            if cleaned_data is None:
                continue

            key = list(cleaned_data.keys())[0]

            if data.get(key) is None:
                data = data | cleaned_data

            else:
                data[key]['tag'].append(cleaned_data[key]['tag'][0])

    return data
