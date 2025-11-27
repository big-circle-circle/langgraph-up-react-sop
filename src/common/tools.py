"""This module provides example tools for web scraping and search functionality.

It includes a basic Tavily search function (as an example)

These tools are intended as free examples to get started. For production use,
consider implementing more robust and specialized tools tailored to your needs.
"""

import logging
from typing import Any, Callable, List, Optional, cast
import pandas as pd
# from langchain_tavily import TavilySearch
from duckduckgo_search import DDGS
from langgraph.runtime import get_runtime

from common.context import Context
from common.mcp import get_deepwiki_tools
from common.utils import merge_two_tables

logger = logging.getLogger(__name__)


dataset_file_path = './data/test_set_with_outputs.csv'
# merge 150 task records with outputs and 150 without outputs into one file for easier lookup
merge_two_tables('./data/test_set_with_outputs.csv', './data/test_set_without_outputs.csv', './data/test_set_with_and_without_output.csv', on_columns=['aircraft_id'])

async def web_search(query: str) -> Optional[dict[str, Any]]:
    """Search for general web results.

    This function performs a search using the Tavily search engine, which is designed
    to provide comprehensive, accurate, and trusted results. It's particularly useful
    for answering questions about current events.
    """
    runtime = get_runtime(Context)
    # wrapped = TavilySearch(max_results=runtime.context.max_search_results)
    # return cast(dict[str, Any], await wrapped.ainvoke({"query": query}))
    max_results = runtime.context.max_search_results

    # ddgs is synchronous; run it in a thread if needed by your runtime,
    # but here we just call it directly for simplicity.
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=max_results))

    # Normalize into a dict similar to Tavily's style
    return cast(
        dict[str, Any],
        {
            "query": query,
            "results": results,
        },
    )


async def VerifyAircraftClearance(
    aircraft_id: str,
    tail_number: str,
    maintenance_record_id: str,
    expected_departure_time: str
    ) -> str:
    """
    Validates aircraft identification and checks maintenance records.
    """
    if not all([aircraft_id, tail_number, maintenance_record_id, expected_departure_time]):
        raise ValueError("Missing required input fields.")

    df = pd.read_csv(dataset_file_path)
    logger.info(f"dataset_file_path: {dataset_file_path}")
    logger.info(f"df head: {df.head()}")
    matched_rows = df[(df["aircraft_id"] == aircraft_id)]

    if matched_rows.empty:
        raise ValueError("No data found for given aircraft_id and tail_number.")

    return matched_rows.iloc[0]["aircraft_ready"]


def VerifyMechanicalComponents(
    aircraft_id: str,
    component_serial_number: str,
    inspection_location_id: str,
    component_weight: float,
    physical_condition_observation: str,
    installation_time: str
    ) -> str:
    """
    Performs comprehensive mechanical component verification.
    """
    if not all([aircraft_id, component_serial_number, inspection_location_id, component_weight, physical_condition_observation, installation_time]):
        raise ValueError("Missing required input fields.")

    df = pd.read_csv(dataset_file_path)
    matched_rows = df[(df["aircraft_id"] == aircraft_id)]

    if matched_rows.empty:
        raise ValueError("No data found for given component_serial_number.")

    return matched_rows.iloc[0]["mechanical_inspection_result"]

def VerifyElectricalSystems(
    aircraft_id: str,
    battery_status: str,
    circuit_continuity_check: str,
    avionics_diagnostics_response: str
    ) -> str:
    """
    Verifies electrical systems according to ESAP standards.
    """
    if not all([aircraft_id, battery_status, circuit_continuity_check, avionics_diagnostics_response]):
        raise ValueError("Missing required input fields.")

    df = pd.read_csv(dataset_file_path)
    matched_rows = df[df["aircraft_id"] == aircraft_id]

    if matched_rows.empty:
        raise ValueError("No data found for given aircraft_id.")

    return matched_rows.iloc[0]["electrical_inspection_result"]

def ReportComponentIncident(               
    aircraft_id: str,
    mechanical_inspection_result: str,
    electrical_inspection_result: str
    ) -> str:
    """
    Reports component incidents based on inspection results.
    """
    if not all([aircraft_id, mechanical_inspection_result, electrical_inspection_result]):
        raise ValueError("Missing required input fields.")

    df = pd.read_csv(dataset_file_path)
    matched_rows = df[df["aircraft_id"] == aircraft_id]

    if matched_rows.empty:
        raise ValueError("No data found for given aircraft_id.")

    return matched_rows.iloc[0]["component_incident_response"]

def ReportComponentMismatch(
    aircraft_id: str,
    component_serial_number: str,
    installed_component_serial_number: str,
    inspection_location_id: str
    ) -> str:
    """
    Reports component serial number mismatches during inspections.
    """
    if not all([aircraft_id, component_serial_number, installed_component_serial_number, inspection_location_id]):
        raise ValueError("Missing required input fields.")

    df = pd.read_csv(dataset_file_path)
    matched_rows = df[df["aircraft_id"] == aircraft_id]

    if matched_rows.empty:
        raise ValueError("No data found for given component_serial_number.")

    return matched_rows.iloc[0]["component_mismatch_response"]

def CrossCheckSpecifications(
    aircraft_id: str,
    component_weight: float,
    expected_component_weight:float,
    installation_time: str,
    actual_inspection_time: str
    ) -> str:
    """
    Reports component serial number mismatches during inspections.
    """
    if not all([aircraft_id, component_weight, expected_component_weight, installation_time, actual_inspection_time]):
        raise ValueError("Missing required input fields.")

    df = pd.read_csv(dataset_file_path)
    matched_rows = df[df["aircraft_id"] == aircraft_id]

    if matched_rows.empty:
        raise ValueError("No data found for given component_serial_number.")

    return matched_rows.iloc[0]["cross_check_response"]

def ReportCrossCheck(
    maintenance_record_id,
    aircraft_id: str,
    component_incident_response: str,
    component_mismatch_response: str
    ) -> str:
    """
    Reports component serial number mismatches during inspections.
    """
    if not all([aircraft_id, maintenance_record_id, component_incident_response, component_mismatch_response]):
        raise ValueError("Missing required input fields.")

    df = pd.read_csv(dataset_file_path)
    matched_rows = df[df["aircraft_id"] == aircraft_id]


    if matched_rows.empty:
        raise ValueError("No data found for given component_serial_number.")

    return matched_rows.iloc[0]["cross_check_reporting_response"]

async def get_tools() -> List[Callable[..., Any]]:
    """Get all available tools based on configuration."""
    tools = [VerifyAircraftClearance, VerifyMechanicalComponents, VerifyElectricalSystems,
             ReportComponentIncident, ReportComponentMismatch, CrossCheckSpecifications,
             ReportCrossCheck]

    runtime = get_runtime(Context)

    if runtime.context.enable_deepwiki:
        deepwiki_tools = await get_deepwiki_tools()
        tools.extend(deepwiki_tools)
        logger.info(f"Loaded {len(deepwiki_tools)} deepwiki tools")

    return tools
