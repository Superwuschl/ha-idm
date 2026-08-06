from __future__ import annotations

import requests


BASE_URL = "https://a.myidm.at"


class IDMApi:

    def __init__(
        self,
        access_token: str,
        refresh_token: str | None,
        wp_id: int,
    ):

        self.access_token = access_token
        self.refresh_token = refresh_token
        self.wp_id = wp_id


    def _headers(self):

        return {
            "Authorization":
                f"Access-Token {self.access_token}",

            "Accept":
                "application/json, text/plain, */*",

            "Origin":
                "https://app.myidm.at",

            "Referer":
                "https://app.myidm.at/",
        }


    def get(
        self,
        endpoint,
    ):

        url = BASE_URL + endpoint

        response = requests.get(
            url,
            headers=self._headers(),
            timeout=20,
        )

        response.raise_for_status()

        return response.json()



    def heatpump(self):

        return self.get(
            f"/api/v1/heatpumps/{self.wp_id}/"
        )


    def diagrams(self):

        return self.get(
            f"/api/v1/heatpumps/{self.wp_id}/diagrams/"
        )


    def system_graph(self):

        return self.get(
            f"/api/v1/heatpumps/{self.wp_id}/diagrams/graph_system/?period=24h"
        )


    def heat_a_graph(self):

        return self.get(
            f"/api/v1/heatpumps/{self.wp_id}/diagrams/graph_heat_a/?period=24h"
        )