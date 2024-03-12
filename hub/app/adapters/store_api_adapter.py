import json
import logging
from typing import List

import requests

from app.entities.processed_agent_data import ProcessedAgentData
from app.interfaces.store_gateway import StoreGateway


class StoreApiAdapter(StoreGateway):
    def __init__(self, api_base_url):
        self.api_base_url = api_base_url

    def save_data(self, processed_agent_data_batch: List[ProcessedAgentData]) -> bool:
        """
        Save the processed road data to the Store API.
        Parameters:
            processed_agent_data_batch (dict): Processed road data to be saved.
        Returns:
            bool: True if the data is successfully saved, False otherwise.
        """
        for item in processed_agent_data_batch:
            # Serialize datetime object to ISO format
            item.agent_data.timestamp = item.agent_data.timestamp.isoformat()
            try:
                response = requests.post(f"{self.api_base_url}/processed_agent_data/", json=item.model_dump())
                response.raise_for_status()
            except requests.RequestException as e:
                logging.error(f"Error while saving data to Store API: {e}. Data : {item.model_dump()}")
                return False
        return True