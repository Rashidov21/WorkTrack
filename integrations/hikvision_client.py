"""Minimal Hikvision ISAPI client for historical access events import."""
from dataclasses import dataclass
from datetime import datetime, time

import requests
from requests.auth import HTTPDigestAuth


@dataclass
class HikvisionClient:
    base_url: str
    username: str
    password: str
    timeout: int = 20

    def fetch_events_page(self, date_from, date_to, position=0, max_results=30):
        """Fetch one AcsEvent page from device. Returns dict payload."""
        if max_results > 30:
            max_results = 30
        if max_results < 1:
            max_results = 1
        start_dt = datetime.combine(date_from, time.min).replace(microsecond=0)
        end_dt = datetime.combine(date_to, time.max).replace(microsecond=0)
        payload = {
            "AcsEventCond": {
                "searchID": "worktrack-import",
                "searchResultPosition": int(position),
                "maxResults": int(max_results),
                "major": 5,
                "startTime": start_dt.isoformat(),
                "endTime": end_dt.isoformat(),
            }
        }
        resp = requests.post(
            f"{self.base_url}/ISAPI/AccessControl/AcsEvent?format=json",
            json=payload,
            auth=HTTPDigestAuth(self.username, self.password),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict):
            raise ValueError("Invalid response shape from Hikvision API")
        return data
