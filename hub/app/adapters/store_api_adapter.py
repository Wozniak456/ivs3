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
            processed_agent_data_batch (List[ProcessedAgentData]): Processed road data to be saved.
        Returns:
            bool: True if the data is successfully saved, False otherwise.
        """
        data = [item.model_dump() for item in processed_agent_data_batch]

        try:
            response = requests.post(f"{self.api_base_url}/processed_agent_data/", json=data)
            response.raise_for_status()  # Raise exception for non-200 status codes
            return True
        except requests.RequestException as e:
            logging.error(f"Error while saving data to Store API: {e}")
            return False
