"""
OM Data Engine
Base Dataset Connector

All dataset connectors must follow this interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterator, Dict, Any


class DatasetConnector(ABC):


    @abstractmethod
    def stream(self) -> Iterator[Dict[str, Any]]:
        """
        Stream dataset records.

        Returns:
            {
                "text": "...",
                "source": "...",
                "license": "..."
            }
        """
        pass



    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """
        Dataset information.
        """
        pass