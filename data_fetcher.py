<<<<<<< HEAD
import logging
import math
import geopy.distance
=======
import json
import logging
import random
import re
>>>>>>> 5969bd781b948b4e694a8f066317b2c2dc7c303c
from urllib.parse import unquote, urlparse
import uuid
from typing import List, Dict, Any, Tuple, Optional
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from collections import defaultdict

from fastapi import HTTPException
from fastapi import status
<<<<<<< HEAD
=======
import stripe
>>>>>>> 5969bd781b948b4e694a8f066317b2c2dc7c303c
from backend_common.auth import (
    load_user_profile,
    update_user_profile,
    update_user_profile_settings,
<<<<<<< HEAD
)
=======
    db,
)
from backend_common.background import get_background_tasks
from dataset_helper import excecute_dataset_plan
from backend_common.stripe_backend.customers import fetch_customer
>>>>>>> 5969bd781b948b4e694a8f066317b2c2dc7c303c
from backend_common.utils.utils import convert_strings_to_ints
from backend_common.gbucket import (
    upload_file_to_google_cloud_bucket,
    delete_file_from_google_cloud_bucket,
)
from config_factory import CONF
from all_types.myapi_dtypes import *
from all_types.response_dtypes import (
    ResLyrMapData,
    LayerInfo,
    UserCatalogInfo
)
from cost_calculator import calculate_cost
from google_api_connector import (
    fetch_from_google_maps_api,
    text_fetch_from_google_maps_api,
)
from backend_common.logging_wrapper import (
    apply_decorator_to_module,
    preserve_validate_decorator,
)
from backend_common.logging_wrapper import log_and_validate
from mapbox_connector import MapBoxConnector
from storage import (
    GOOGLE_CATEGORIES,
    REAL_ESTATE_CATEGORIES,
    AREA_INTELLIGENCE_CATEGORIES,
    GRADIENT_COLORS,
    # load_real_estate_categories,
    # load_area_intelligence_categories,
    get_real_estate_dataset_from_storage,
    get_census_dataset_from_storage,
    get_commercial_properties_dataset_from_storage,
    fetch_dataset_id,
    load_dataset,
    update_dataset_layer_matching,
    update_user_layer_matching,
    delete_dataset_layer_matching,
    delete_user_layer_matching,
    fetch_user_catalogs,
    load_user_layer_matching,
    fetch_user_layers,
    load_store_catalogs,
    convert_to_serializable,
    make_dataset_filename,
    generate_layer_id,
    # load_google_categories,
    load_country_city,
    make_ggl_layer_filename,
)
from boolean_query_processor import reduce_to_single_query
from popularity_algo import create_plan, get_plan, process_plan_popularity, save_plan
<<<<<<< HEAD

=======
>>>>>>> 5969bd781b948b4e694a8f066317b2c2dc7c303c

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

EXPANSION_DISTANCE_KM = 60.0  # for each side from the center of the bounding box
# Global cache dictionary to store previously fetched locations
_LOCATION_CACHE = {}


def print_circle_hierarchy(circle: dict, number=""):
    center_marker = "*" if circle["is_center"] else ""
    print(
        f"Circle {number}{center_marker}: Center: (lng: {circle['center'][0]:.4f}, lat: {circle['center'][1]:.4f}), Radius: {circle['radius']:.2f} km"
    )
    for i, sub_circle in enumerate(circle["sub_circles"], 1):
        print_circle_hierarchy(sub_circle, f"{number}.{i}" if number else f"{i}")


def count_circles(circle: dict):
    return 1 + sum(count_circles(sub_circle) for sub_circle in circle["sub_circles"])


# def create_string_list(circle_hierarchy, type_string, text_search):
#     result = []
#     circles_to_process = [circle_hierarchy]

#     while circles_to_process:
#         circle = circles_to_process.pop(0)

#         lat, lng = circle["center"]
#         radius = circle["radius"]

#         circle_string = f"{lat}_{lng}_{radius * 1000}_{type_string}"
#         if text_search != "" and text_search is not None:
#             circle_string = circle_string + f"_{text_search}"
#         result.append(circle_string)

#         circles_to_process.extend(circle.get("sub_circles", []))

#     return result


def expand_bounding_box(
    lat: float, lon: float, expansion_distance_km: float = EXPANSION_DISTANCE_KM
) -> list:
    try:
        center_point = (lat, lon)

        # Calculate the distance in degrees
        north_expansion = geodesic(kilometers=expansion_distance_km).destination(
            center_point, 0
        )  # North
        south_expansion = geodesic(kilometers=expansion_distance_km).destination(
            center_point, 180
        )  # South
        east_expansion = geodesic(kilometers=expansion_distance_km).destination(
            center_point, 90
        )  # East
        west_expansion = geodesic(kilometers=expansion_distance_km).destination(
            center_point, 270
        )  # West

        expanded_bbox = [
            south_expansion[0],
            north_expansion[0],
            west_expansion[1],
            east_expansion[1],
        ]

        return expanded_bbox
    except Exception as e:
        logger.error(f"Error expanding bounding box: {str(e)}")
        return None


def get_req_geodata(city_name: str, country_name: str) -> Optional[ReqGeodata]:
    # Create cache key
    cache_key = f"{city_name},{country_name}"

    # Check if result exists in cache
    if cache_key in _LOCATION_CACHE:
        return _LOCATION_CACHE[cache_key]

    try:
        geolocator = Nominatim(user_agent="city_country_search")
        location = geolocator.geocode(f"{city_name}, {country_name}", exactly_one=True)

        if not location:
            logger.warning(f"No location found for {city_name}, {country_name}")
            _LOCATION_CACHE[cache_key] = None
            return None

        bounding_box = expand_bounding_box(location.latitude, location.longitude)
        if bounding_box is None:
            logger.warning(f"No bounding box found for {city_name}, {country_name}")
            _LOCATION_CACHE[cache_key] = None
            return None

        result = ReqGeodata(
            lat=float(location.latitude),
            lng=float(location.longitude),
            bounding_box=bounding_box,
        )

        # Store in cache before returning
        _LOCATION_CACHE[cache_key] = result
        return result

    except Exception as e:
        logger.error(f"Error getting geodata for {city_name}, {country_name}: {str(e)}")
        _LOCATION_CACHE[cache_key] = None
        return None

<<<<<<< HEAD
=======

def fetch_lat_lng_bounding_box(req: ReqFetchDataset) -> ReqFetchDataset:
    # If lat and lng are provided directly, use them
    if req.lat is not None and req.lng is not None:
        req._bounding_box = expand_bounding_box(req.lat, req.lng)
        return req
>>>>>>> 5969bd781b948b4e694a8f066317b2c2dc7c303c

def fetch_lat_lng_bounding_box(req: ReqFetchDataset) -> ReqFetchDataset:
    # Load country/city data
    country_city_data = load_country_city()

    # Find the city coordinates
    city_data = None
<<<<<<< HEAD
=======
    
    if not req.city_name:
        raise ValueError("Either city_name or lat/lng coordinates must be provided")

>>>>>>> 5969bd781b948b4e694a8f066317b2c2dc7c303c
    if req.country_name in country_city_data:
        for city in country_city_data[req.country_name]:
            if city["name"] == req.city_name:
                if (
                    city.get("lat") is None
                    or city.get("lng") is None
                    or city.get("bounding_box") is None
                ):
                    raise ValueError(
                        f"Invalid city data for {req.city_name} in {req.country_name}"
                    )
                req._bounding_box = expand_bounding_box(
                    city.get("lat"), city.get("lng")
                )
                req.lat = city.get("lat")
                req.lng = city.get("lng")
    else:
        # if city not found in country_city_data, use geocoding to get city_data
        city_data = get_req_geodata(req.city_name, req.country_name)
        req._bounding_box = city_data.bounding_box
        req.lat = city_data.lat
        req.lng = city_data.lng

    return req


async def fetch_census_realestate(
    req: ReqFetchDataset, data_type
) -> Tuple[Any, str, str, str]:
    next_page_token = req.page_token
    plan_name = ""
    action = req.action
    bknd_dataset_id = ""
    dataset = None

    req._included_types, req._excluded_types = reduce_to_single_query(req.boolean_query)

    req = fetch_lat_lng_bounding_box(req)
    # bknd_dataset_id = make_dataset_filename(req)
    # TODO remove redundent code
    # dataset = await load_dataset(bknd_dataset_id)

    if not dataset:
        if data_type == "real_estate" or (
            data_type == "commercial" and req.country_name == "Saudi Arabia"
        ):
            get_dataset_func = get_real_estate_dataset_from_storage
        elif data_type in ["Population Area Intelligence"]:
            get_dataset_func = get_census_dataset_from_storage
        elif data_type == "commercial":
            get_dataset_func = get_commercial_properties_dataset_from_storage

        dataset, bknd_dataset_id, next_page_token = await get_dataset_func(
            bknd_dataset_id,
            action,
            request_location=req,
            next_page_token=next_page_token,
            data_type=data_type,
        )
        if dataset:
            dataset = convert_strings_to_ints(dataset)
            # bknd_dataset_id = await store_data_resp(
            #     req_dataset, dataset, bknd_dataset_id
            # )

    return dataset, bknd_dataset_id, next_page_token, plan_name


async def fetch_ggl_nearby(req: ReqFetchDataset):
    search_type = req.search_type
<<<<<<< HEAD
    next_page_token = req.page_token
    action = req.action
    plan_name = ""

    if req.action == "full data":
        req, plan_name, next_page_token, current_plan_index, bknd_dataset_id = (
            await process_req_plan(req)
        )
    else:
        req = fetch_lat_lng_bounding_box(req)

    bknd_dataset_id = make_dataset_filename(req)
    # dataset = await load_dataset(bknd_dataset_id)

    # dataset, bknd_dataset_id = await get_dataset_from_storage(req)

    # if not dataset:

    if "default" in search_type or "category_search" in search_type:
        dataset = await fetch_from_google_maps_api(req)
    elif "keyword_search" in search_type:
        ggl_api_resp, _ = await text_fetch_from_google_maps_api(req)
        dataset = await MapBoxConnector.new_ggl_to_boxmap(ggl_api_resp, req.radius)
        if ggl_api_resp:
            dataset = convert_strings_to_ints(dataset)
    # Store the fetched data in storage
    # dataset = await MapBoxConnector.new_ggl_to_boxmap(ggl_api_resp,req.radius)
    # if ggl_api_resp:
    #     dataset = convert_strings_to_ints(dataset)
    #     bknd_dataset_id = await store_data_resp(
    #         req, dataset, bknd_dataset_id
    #     )
    # if dataset is less than 20 or none and action is full data
    #     call function rectify plan
    #     replace next_page_token with next non-skip page token
=======
    action = req.action
    plan_name = ""

    # try 30 times to get non empty dataset
    for _ in range(30):
        next_page_token = req.page_token

        if req.action == "full data":
            req, plan_name, next_page_token, current_plan_index, bknd_dataset_id = (
                await process_req_plan(req)
            )
        else:
            req = fetch_lat_lng_bounding_box(req)

        bknd_dataset_id = make_dataset_filename(req)

        if "default" in search_type or "category_search" in search_type:
            dataset = await fetch_from_google_maps_api(req)
        elif "keyword_search" in search_type:
            ggl_api_resp, _ = await text_fetch_from_google_maps_api(req)
            dataset = await MapBoxConnector.new_ggl_to_boxmap(ggl_api_resp, req.radius)
            if ggl_api_resp:
                dataset = convert_strings_to_ints(dataset)

        if req.action == "full data" and len(dataset.get("features", "")) == 0:
            new_page_index = await rectify_plan(plan_name, current_plan_index)
            if new_page_index == "":
                break
            else:
                req.page_token = (
                    req.page_token.split("@#$")[0] + "@#$" + str(new_page_index)
                )
        else:
            # continue as usual
            break
        
    # if dataset is less than 20 or none and action is full data
>>>>>>> 5969bd781b948b4e694a8f066317b2c2dc7c303c
    if len(dataset.get("features", "")) < 20 and action == "full data":
        next_plan_index = await rectify_plan(plan_name, current_plan_index)
        if next_plan_index == "":
            next_page_token = ""
        else:
            next_page_token = (
                next_page_token.split("@#$")[0] + "@#$" + str(next_plan_index)
            )

    return dataset, bknd_dataset_id, next_page_token, plan_name


async def rectify_plan(plan_name, current_plan_index):
    plan = await get_plan(plan_name)
    rectified_plan = add_skip_to_subcircles(plan, current_plan_index)
    await save_plan(plan_name, rectified_plan)
    next_plan_index = get_next_non_skip_index(rectified_plan, current_plan_index)

    return next_plan_index


def get_next_non_skip_index(rectified_plan, current_plan_index):
    for i in range(current_plan_index + 1, len(rectified_plan)):
        if (
            not rectified_plan[i].endswith("_skip")
            and rectified_plan[i] != "end of search plan"
        ):
            # Return the new token with the found index
            return i

    # If no non-skipped item is found, return None or a special token
    return ""


def add_skip_to_subcircles(plan: list, token_plan_index: str):
    circle_string = plan[token_plan_index]
    # Extract the circle number from the input string

    circle_number = circle_string.split("_circle=")[1].split("_")[0].replace("*", "")

    def is_subcircle(circle):
        circle = "_circle=" + circle.split("_circle=")[1]
        return circle.startswith(f"_circle={circle_number}.")

    # Add "_skip" to subcircles
    modified_plan = []
    for circle in plan[:-1]:
        if is_subcircle(circle):
            if not circle.endswith("_skip"):
                circle += "_skip"
        modified_plan.append(circle)
    # Add the last item separately
    modified_plan.append(plan[-1])

    return modified_plan


async def process_req_plan(req: ReqFetchDataset):
    action = req.action
    plan: List[str] = []
    current_plan_index = 0
    bknd_dataset_id = ""

    if req.page_token == "" and action == "full data":
        if req.radius > 750:
            string_list_plan = await create_plan(
                req.lng, req.lat, req.radius, req.boolean_query, req.text_search
            )

        # TODO creating the name of the file should be moved to storage
        tcc_string = make_ggl_layer_filename(req)
        plan_name = f"plan_{tcc_string}"
        if req.text_search != "" and req.text_search is not None:
            plan_name = plan_name + "_text_search="
        await save_plan(plan_name, string_list_plan)
        plan = string_list_plan

        next_search = string_list_plan[0]
        first_search = next_search.split("_")
        req.lng, req.lat, req.radius = (
            float(first_search[0]),
            float(first_search[1]),
            float(first_search[2]),
        )

        bknd_dataset_id = plan[current_plan_index]
        next_page_token = f"page_token={plan_name}@#${1}"  # Start with the first search

    elif req.page_token != "":

        plan_name, current_plan_index = req.page_token.split("@#$")
        _, plan_name = plan_name.split("page_token=")

        current_plan_index = int(current_plan_index)

        # limit to 30 calls per plan
        if current_plan_index > 30:
            raise HTTPException(
                status_code=488, detail="temporarely disabled for more than 30 searches"
            )
        plan = await get_plan(plan_name)

        if (
            plan is None
            or current_plan_index is None
            or len(plan) <= current_plan_index
        ):
            return req, plan_name, "", current_plan_index, bknd_dataset_id

        search_info = plan[current_plan_index].split("_")
        req.lng, req.lat, req.radius = (
            float(search_info[0]),
            float(search_info[1]),
            float(search_info[2]),
        )
        next_plan_index = current_plan_index + 1
        if plan[next_plan_index] == "end of search plan":
            next_page_token = ""  # End of search plan
            await process_plan_popularity(plan_name)
        else:
            next_page_token = f"page_token={plan_name}@#${next_plan_index}"

        # TODO: Remove this after testing Process plan at index 5
        if current_plan_index == 5:
            await process_plan_popularity(plan_name)

    return req, plan_name, next_page_token, current_plan_index, bknd_dataset_id


async def fetch_catlog_collection():
    """
    Generates and returns a collection of catalog metadata. This function creates
    a list of predefined catalog entries and then adds 20 more dummy entries.
    Each entry contains information such as ID, name, description, thumbnail URL,
    and access permissions. This is likely used for testing or as placeholder data.
    """

    metadata = [
        {
            "id": "2",
            "name": "Saudi Arabia - Real Estate Transactions",
            "description": "Database of real-estate transactions in Saudi Arabia",
            "thumbnail_url": "https://catalog-assets.s3.ap-northeast-1.amazonaws.com/real_estate_ksa.png",
            "catalog_link": "https://example.com/catalog2.jpg",
            "records_number": 20,
            "can_access": True,
        },
        {
            "id": "55",
            "name": "Saudi Arabia - gas stations poi data",
            "description": "Database of all Saudi Arabia gas stations Points of Interests",
            "thumbnail_url": "https://catalog-assets.s3.ap-northeast-1.amazonaws.com/SAUgasStations.PNG",
            "catalog_link": "https://catalog-assets.s3.ap-northeast-1.amazonaws.com/SAUgasStations.PNG",
            "records_number": 8517,
            "can_access": False,
        },
        {
            "id": "65",
            "name": "Saudi Arabia - Restaurants, Cafes and Bakeries",
            "description": "Focusing on the restaurants, cafes and bakeries in KSA",
            "thumbnail_url": "https://catalog-assets.s3.ap-northeast-1.amazonaws.com/sau_bak_res.PNG",
            "catalog_link": "https://catalog-assets.s3.ap-northeast-1.amazonaws.com/sau_bak_res.PNG",
            "records_number": 132383,
            "can_access": False,
        },
    ]

    # Add 20 more dummy entries
    for i in range(3, 4):
        metadata.append(
            {
                "id": str(i),
                "name": f"Saudi Arabia - Sample Data {i}",
                "description": f"Sample description for dataset {i}",
                "thumbnail_url": "https://catalog-assets.s3.ap-northeast-1.amazonaws.com/sample_image.png",
                "catalog_link": "https://example.com/sample_image.jpg",
                "records_number": i * 100,
                "can_access": True,
            }
        )

    return metadata


async def fetch_layer_collection():
    """
    Similar to fetch_catlog_collection, this function returns a collection of layer
    metadata. It provides a smaller, fixed set of layer entries. Each entry includes
    details like ID, name, description, and access permissions.
    """

    metadata = [
        {
            "id": "2",
            "name": "Saudi Arabia - Real Estate Transactions",
            "description": "Database of real-estate transactions in Saudi Arabia",
            "thumbnail_url": "https://catalog-assets.s3.ap-northeast-1.amazonaws.com/real_estate_ksa.png",
            "catalog_link": "https://example.com/catalog2.jpg",
            "records_number": 20,
            "can_access": False,
        },
        {
            "id": "3",
            "name": "Saudi Arabia - 3",
            "description": "Database of all Saudi Arabia gas stations Points of Interests",
            "thumbnail_url": "https://catalog-assets.s3.ap-northeast-1.amazonaws.com/SAUgasStations.PNG",
            "catalog_link": "https://catalog-assets.s3.ap-northeast-1.amazonaws.com/SAUgasStations.PNG",
            "records_number": 8517,
            "can_access": False,
        },
    ]

    return metadata


async def fetch_country_city_data() -> Dict[str, List[Dict[str, float]]]:
    """
    Returns a set of country and city data for United Arab Emirates, Saudi Arabia, and Canada.
    The data is structured as a dictionary where keys are country names and values are lists of cities.
    """

    data = load_country_city()
    return data


async def validate_city_data(country, city):
    """Validates and returns city data"""
    country_city_data = await fetch_country_city_data()
    for c, cities in country_city_data.items():
        if c.lower() == country.lower():
            for city_data in cities:
                if city_data["name"].lower() == city.lower():
                    return city_data
    raise HTTPException(
        status_code=404, detail="City not found in the specified country"
    )


# def determine_data_type(included_types: List[str], categories: Dict) -> Optional[str]:
#     """
#     Determines the data type based on included types by checking against all category types
#     """
#     if not included_types:
#         return None

#     for category_type, type_list in categories.items():
#         # Handle both direct lists and nested dictionaries
#         if isinstance(type_list, list):
#             if set(included_types).intersection(set(type_list)):
#                 return category_type
#         elif isinstance(type_list, dict):
#             # Flatten nested categories for comparison
#             all_subcategories = []
#             for subcategories in type_list.values():
#                 if isinstance(subcategories, list):
#                     all_subcategories.extend(subcategories)
#             if set(included_types).intersection(set(all_subcategories)):
#                 return category_type

#     return None


def determine_data_type(boolean_query: str, categories: Dict) -> Optional[str]:
    """
    Determines the data type based on boolean query.
    Returns:
    - Special category if ALL terms belong to that category
    - "google_categories" if ANY terms are Google or custom terms
    - Raises error if mixing Google/custom with special categories
    """
    if not boolean_query:
        return None

    # Extract just the terms
    terms = set(
        term.strip()
        for term in boolean_query.replace("(", " ")
        .replace(")", " ")
        .replace("AND", " ")
        .replace("OR", " ")
        .replace("NOT", " ")
        .split()
    )

    if not terms:
        return None

    # Check non-Google categories first
    for category, category_terms in categories.items():
        if category not in GOOGLE_CATEGORIES:
            matches = terms.intersection(set(category_terms))
            if matches:
                # If we found any special category terms, ALL terms must belong to this category
                if len(matches) != len(terms):
                    raise ValueError(
                        "Cannot mix special category terms with other terms"
                    )
                return category

    # If we get here, no special category matches were found
    # So we can safely return google_categories for either Google terms or custom terms
    return "google_categories"


async def fetch_dataset(req: ReqFetchDataset):
    """
    This function attempts to fetch an existing layer based on the provided
    request parameters. If the layer exists, it loads the data, transforms it,
    and returns it. If the layer doesn't exist, it creates a new layer
    """
    next_page_token = None
<<<<<<< HEAD
    new_layer_id = req.prdcer_lyr_id
    if req.page_token != "" or req.page_token != "0":
        new_layer_id = generate_layer_id()
=======
    layer_id = req.prdcer_lyr_id
    if req.page_token == "" or req.prdcer_lyr_id == "":
        layer_id = generate_layer_id()
>>>>>>> 5969bd781b948b4e694a8f066317b2c2dc7c303c

    geojson_dataset = []

    # Load all categories

    categories = await poi_categories(
        ReqCityCountry(country_name=req.country_name, city_name=req.city_name)
    )

    # Now using boolean_query instead of included_types
    data_type = determine_data_type(req.boolean_query, categories)

    if (
        data_type == "real_estate"
        or data_type in list(AREA_INTELLIGENCE_CATEGORIES.keys())
        or (data_type == "commercial" and (req.country_name == "Saudi Arabia" or True))
    ):
        geojson_dataset, bknd_dataset_id, next_page_token, plan_name = (
            await fetch_census_realestate(req=req, data_type=data_type)
        )
    else:

        city_data = fetch_lat_lng_bounding_box(req)

        if city_data is None:
            raise HTTPException(
                status_code=404, detail="City not found in the specified country"
            )
        # Default to Google Maps API
        req.lat = city_data.lat
        req.lng = city_data.lng
        req._bounding_box = city_data._bounding_box
        geojson_dataset, bknd_dataset_id, next_page_token, plan_name = (
            await fetch_ggl_nearby(req)
        )

    # if request action was "full data" then store dataset id in the user profile
    # the name of the dataset will be the action + cct_layer name
    # make_ggl_layer_filename
    if req.action == "full data":
        estimated_cost, _ = await calculate_cost(req)
        estimated_cost = int(round(estimated_cost[1], 2) * 100)
        user_data = await load_user_profile(req.user_id)
        admin_id = user_data["admin_id"]
        user_owns_this_dataset = False

        if plan_name in user_data["prdcer"]["prdcer_dataset"]:
            user_owns_this_dataset = True

        # if the user already has this dataset on his profile don't charge him 
        if not user_owns_this_dataset:
            
            if not admin_id:
                customer = await fetch_customer(user_id=req.user_id)
            else:
                customer = await fetch_customer(user_id=admin_id)

            if not customer:
                raise HTTPException(status_code=404, detail="Customer not found")
            
            if customer['balance'] < estimated_cost:
                raise HTTPException(
                    status_code=400, 
                    detail="Insufficient balance in wallet"
                )

            # Deduct funds from the customer's balance in Stripe
            # Note: For deductions, we pass a negative amount
            stripe.Customer.create_balance_transaction(
                customer['id'],
                amount=-estimated_cost,  # Negative amount to decrease balance
                currency="usd",
                description="Deducted funds from wallet"
            )
        # if the user already has this dataset on his profile don't charge him 

        # if the first query of the full data was successful and returned results
        # deduct money from the user's wallet for the price of this dataset
        # if the user doesn't have funds return a specific error to the frontend to prompt the user to add funds

        get_background_tasks().add_task(excecute_dataset_plan, req, plan_name, layer_id)

        # if the first query of the full data was successful and returned results continue the fetch data plan in the background
        # when the user has made a purchase as a background task we should finish the plan, the background taks should execute calls within the same level at the same time in a batch of 5 at a time
        # when saving the dataset we should save what is the % availability of this dataset based on the plan , plan that is 50% executed means data available 50%
        # while we are at it we should add the dataset's next refresh date, and a flag saying whether to auto refresh or no
        # after the initiial api call api call, when we return to the frontend we need to add a new key in the return object saying delay before next call ,
        # and we should make this delay 3 seconds
        # in those 3 seconds we hope to allow to backend to advance in the query plan execution
        # the frontend should display the % as a bar with an indication that this bar is filling in those 3 seconds to reassure the user
        # we should return this % completetion to the user to display while the user is watiing for his data

        # TODO this is seperate, optimisation for foreground process of data retrival from db
        # then on subsequent calls using next page token the backend should execute calls within the same level at the same time in a batch of 5 at a time

        bknd_dataset_id = plan_name
        # TODO
        # we need to somehow deduplicate our data before we send it to the user, i'm not sure how

        user_data = await load_user_profile(req.user_id)
        user_data["prdcer"]["prdcer_dataset"][f"{plan_name}"] = plan_name
        await update_user_profile(req.user_id, user_data)

    geojson_dataset["bknd_dataset_id"] = bknd_dataset_id
    geojson_dataset["records_count"] = len(geojson_dataset.get("features", ""))
<<<<<<< HEAD
    geojson_dataset["prdcer_lyr_id"] = new_layer_id
=======
    geojson_dataset["prdcer_lyr_id"] = layer_id
>>>>>>> 5969bd781b948b4e694a8f066317b2c2dc7c303c
    geojson_dataset["next_page_token"] = next_page_token
    geojson_dataset["delay_before_next_call"] = 3
    geojson_dataset["progress"] = random.randint(0, 100)
    return geojson_dataset


async def save_lyr(req: ReqSavePrdcerLyer) -> str:
    user_data = await load_user_profile(req.user_id)

    try:
        # Check for duplicate prdcer_layer_name
        new_layer_name = req.model_dump(exclude={"user_id"})["prdcer_layer_name"]
        for layer in user_data["prdcer"]["prdcer_lyrs"].values():
            if layer["prdcer_layer_name"] == new_layer_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Layer name '{new_layer_name}' already exists. Layer names must be unique.",
                )

        # Add the new layer to user profile
        user_data["prdcer"]["prdcer_lyrs"][req.prdcer_lyr_id] = req.model_dump(
            exclude={"user_id"}
        )

        # Save updated user data
        await update_user_profile(req.user_id, user_data)
        await update_dataset_layer_matching(req.prdcer_lyr_id, req.bknd_dataset_id)
        await update_user_layer_matching(req.prdcer_lyr_id, req.user_id)
    except KeyError as ke:
        logger.error(f"Invalid user data structure for user_id: {req.user_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user data structure",
        ) from ke

    return "Producer layer created successfully"


async def delete_layer(req: ReqDeletePrdcerLayer) -> str:
    """
    Deletes a layer based on its id.
    Args:
        req (ReqDeletePrdcerLayer): The request data containing `user_id` and `prdcer_lyr_id`.

    Returns:
        str: Success message if the layer is deleted.
    """

    bknd_dataset_id, dataset_info = await fetch_dataset_id(req.prdcer_lyr_id)
    user_data = await load_user_profile(req.user_id)

    try:
        # Find the layer to delete based on its id
        layers = user_data["prdcer"]["prdcer_lyrs"]
        layer_to_delete = None

        for layer_id, layer in layers.items():
            if layer["prdcer_lyr_id"] == req.prdcer_lyr_id:
                layer_to_delete = layer_id
                break

        if not layer_to_delete:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Layer id '{req.prdcer_lyr_id}' not found.",
            )

        # Delete the layer
        del user_data["prdcer"]["prdcer_lyrs"][layer_to_delete]

        # Save updated user data
        await update_user_profile(req.user_id, user_data)
        await delete_dataset_layer_matching(layer_to_delete, bknd_dataset_id)
        await delete_user_layer_matching(layer_to_delete)

    except KeyError as ke:
        logger.error(f"Invalid user data structure for user_id: {req.user_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user data structure",
        ) from ke

    return f"Layer '{req.prdcer_lyr_id}' deleted successfully."


@preserve_validate_decorator
@log_and_validate(logger, validate_output=True, output_model=List[LayerInfo])
async def aquire_user_lyrs(req: ReqUserId) -> List[LayerInfo]:
    """
    Retrieves all producer layers associated with a specific user. It reads the
    user's data file and the dataset-layer matching file to compile a list of
    all layers owned by the user, including metadata like layer name, color,
    and record count.
    """
    user_layers = await fetch_user_layers(req.user_id)

    user_layers_metadata = []
    for lyr_id, lyr_data in user_layers.items():
        try:
            dataset_id, dataset_info = await fetch_dataset_id(lyr_id)
            records_count = dataset_info["records_count"]

            user_layers_metadata.append(
                LayerInfo(
                    prdcer_lyr_id=lyr_id,
                    prdcer_layer_name=lyr_data["prdcer_layer_name"],
                    points_color=lyr_data["points_color"],
                    layer_legend=lyr_data["layer_legend"],
                    layer_description=lyr_data["layer_description"],
                    records_count=records_count,
                    city_name=lyr_data["city_name"],
                    bknd_dataset_id=lyr_data["bknd_dataset_id"],
                    is_zone_lyr="false",
                    progress=random.randint(0, 100),
                )
            )
        except KeyError as e:
            logger.error(f"Missing key in layer data: {str(e)}")
            # Continue to next layer instead of failing the entire request
            continue

    # if not user_layers_metadata:
    #     raise HTTPException(
    #         status_code=404, detail="No valid layers found for the user"
    #     )

    return user_layers_metadata


async def fetch_lyr_map_data(req: ReqPrdcerLyrMapData) -> ResLyrMapData:
    """
    Fetches detailed map data for a specific producer layer.
    """
    dataset = {}
    user_layer_matching = await load_user_layer_matching()
    layer_owner_id = user_layer_matching.get(req.prdcer_lyr_id)
    layer_owner_data = await load_user_profile(layer_owner_id)

    try:
        layer_metadata = layer_owner_data["prdcer"]["prdcer_lyrs"][req.prdcer_lyr_id]
    except KeyError as ke:
        raise HTTPException(
            status_code=404, detail="Producer layer not found for this user"
        ) from ke

    dataset_id, dataset_info = await fetch_dataset_id(req.prdcer_lyr_id)
    dataset = await load_dataset(dataset_id, fetch_full_plan_datasets=True)

    # Extract properties from first feature if available
    properties = []
    if dataset.get("features") and len(dataset.get("features", [])) > 0:
        first_feature = dataset.get("features", [])[0]
        properties = list(first_feature.get("properties", {}).keys())

    return ResLyrMapData(
        type="FeatureCollection",
        features=dataset.get("features", []),
        properties=properties,  # Add the properties list here
        prdcer_layer_name=layer_metadata.get("prdcer_layer_name"),
        prdcer_lyr_id=req.prdcer_lyr_id,
        bknd_dataset_id=dataset_id,
        points_color=layer_metadata.get("points_color"),
        layer_legend=layer_metadata.get("layer_legend"),
        layer_description=layer_metadata.get("layer_description"),
        city_name=layer_metadata.get("city_name"),
        records_count=dataset_info.get("records_count"),
        is_zone_lyr="false",
<<<<<<< HEAD
=======
        progress=random.randint(0, 100),
>>>>>>> 5969bd781b948b4e694a8f066317b2c2dc7c303c
    )


async def save_prdcer_ctlg(req: ReqSavePrdcerCtlg) -> str:
    """
    Creates and saves a new producer catalog.
    """

    # add display elements key value pair display_elements:{"polygons":[]}
    # catalog should have "catlog_layer_options":{} extra configurations for the layers with their display options (point,grid:{"size":3, color:#FFFF45},heatmap:{"proeprty":rating})
    try:
        user_data = await load_user_profile(req["user_id"])
        new_ctlg_id = str(uuid.uuid4())

        req["thumbnail_url"] = ""
        if req["image"]:
            try:
                thumbnail_url = upload_file_to_google_cloud_bucket(
                    req["image"],
                    CONF.gcloud_slocator_bucket_name,
                    CONF.gcloud_images_bucket_path,
                    CONF.gcloud_bucket_credentials_json_path,
                )
            except Exception as e:
                logger.error(f"Error uploading image: {str(e)}")
                # Keep the original thumbnail_url if upload fails

        new_catalog = {
            "prdcer_ctlg_name": req["prdcer_ctlg_name"],
            "prdcer_ctlg_id": new_ctlg_id,
            "subscription_price": req["subscription_price"],
            "ctlg_description": req["ctlg_description"],
            "total_records": req["total_records"],
            "lyrs": req["lyrs"],
            "thumbnail_url": thumbnail_url,
            "ctlg_owner_user_id": req["user_id"],
            "display_elements": req["display_elements"],
            "catalog_layer_options": req["catalog_layer_options"],
        }
        user_data["prdcer"]["prdcer_ctlgs"][new_ctlg_id] = new_catalog
        # serializable_user_data = convert_to_serializable(user_data)
        await update_user_profile(req["user_id"], user_data)
        return new_ctlg_id
    except Exception as e:
        raise e


async def delete_prdcer_ctlg(req: ReqDeletePrdcerCtlg) -> str:
    """
    Deletes an existing producer catalog.
    """
    try:
        # Load the user profile to get the catalog
        user_data = await load_user_profile(req.user_id)

        # Check if the catalog exists
        if req.prdcer_ctlg_id not in user_data["prdcer"]["prdcer_ctlgs"]:
            raise ValueError(f"Catalog ID {req.prdcer_ctlg_id} not found.")

        thumbnail_url = user_data["prdcer"]["prdcer_ctlgs"][req.prdcer_ctlg_id][
            "thumbnail_url"
        ]

        # Delete the catalog
        del user_data["prdcer"]["prdcer_ctlgs"][req.prdcer_ctlg_id]

        # Delete the thumbnail image from Google Cloud Storage if it exists
        if thumbnail_url:
            # Extract the file path from the URL (assuming the URL is like 'https://storage.googleapis.com/bucket_name/path/to/file.jpg')
            parsed_url = urlparse(thumbnail_url)
            blob_name = unquote(parsed_url.path.lstrip("/").split("/", 1)[-1])
            # file_path = thumbnail_url.split(CONF.gcloud_slocator_bucket_name+"/")[-1]  # Get the file path (e.g., "path/to/file.jpg")
            delete_file_from_google_cloud_bucket(
                blob_name,
                CONF.gcloud_slocator_bucket_name,
                CONF.gcloud_bucket_credentials_json_path,
            )

        # Update the user profile after deleting the catalog
        await update_user_profile(req.user_id, user_data)

        return f"Catalog with ID {req.prdcer_ctlg_id} deleted successfully."

    except Exception as e:
        logger.error(f"Error deleting catalog: {str(e)}")
        raise e


async def fetch_prdcer_ctlgs(req: ReqUserId) -> List[UserCatalogInfo]:
    """
    Retrieves all producer catalogs associated with a specific user.
    """
    try:
        user_catalogs = await fetch_user_catalogs(req.user_id)
        validated_catalogs = []

        for ctlg_id, ctlg_data in user_catalogs.items():
            validated_catalogs.append(
                UserCatalogInfo(
                    prdcer_ctlg_id=ctlg_id,
                    prdcer_ctlg_name=ctlg_data["prdcer_ctlg_name"],
                    ctlg_description=ctlg_data["ctlg_description"],
                    thumbnail_url=ctlg_data.get("thumbnail_url", ""),
                    subscription_price=ctlg_data["subscription_price"],
                    total_records=ctlg_data["total_records"],
                    lyrs=ctlg_data["lyrs"],
                    ctlg_owner_user_id=ctlg_data["ctlg_owner_user_id"],
                )
            )
        return validated_catalogs
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching catalogs: {str(e)}",
        ) from e


async def fetch_ctlg_lyrs(req: ReqFetchCtlgLyrs) -> List[ResLyrMapData]:
    """
    Fetches all layers associated with a specific catalog.
    """
    try:
        user_data = await load_user_profile(req.user_id)
        ctlg = (
            user_data.get("prdcer", {})
            .get("prdcer_ctlgs", {})
            .get(req.prdcer_ctlg_id, {})
        )
        if not ctlg:
            store_ctlgs = load_store_catalogs()
            ctlg = next(
                (
                    ctlg_info
                    for ctlg_key, ctlg_info in store_ctlgs.items()
                    if ctlg_key == req.prdcer_ctlg_id
                ),
                {},
            )
        if not ctlg:
            raise HTTPException(status_code=404, detail="Catalog not found")

        ctlg_owner_data = await load_user_profile(ctlg["ctlg_owner_user_id"])
        ctlg_lyrs_map_data = []

        for lyr_info in ctlg["lyrs"]:
            lyr_id = lyr_info["layer_id"]
            dataset_id, dataset_info = await fetch_dataset_id(lyr_id)
            trans_dataset = await load_dataset(
                dataset_id, fetch_full_plan_datasets=True
            )
            # trans_dataset = await MapBoxConnector.new_ggl_to_boxmap(trans_dataset)

            # Extract properties from first feature if available
            properties = []
            if trans_dataset.get("features") and len(trans_dataset["features"]) > 0:
                first_feature = trans_dataset["features"][0]
                properties = list(first_feature.get("properties", {}).keys())

            lyr_metadata = (
                ctlg_owner_data.get("prdcer", {}).get("prdcer_lyrs", {}).get(lyr_id, {})
            )

            ctlg_lyrs_map_data.append(
                ResLyrMapData(
                    type="FeatureCollection",
                    features=trans_dataset["features"],
                    properties=properties,  # Add the properties list here
                    prdcer_layer_name=lyr_metadata.get(
                        "prdcer_layer_name", f"Layer {lyr_id}"
                    ),
                    prdcer_lyr_id=lyr_id,
                    bknd_dataset_id=dataset_id,
                    points_color=lyr_metadata.get("points_color", "red"),
                    layer_legend=lyr_metadata.get("layer_legend", ""),
                    layer_description=lyr_metadata.get("layer_description", ""),
                    records_count=len(trans_dataset["features"]),
                    city_name=lyr_metadata["city_name"],
                    is_zone_lyr="false",
                )
            )
        return ctlg_lyrs_map_data
    except HTTPException:
        raise


def calculate_thresholds(values: List[float]) -> List[float]:
    """
    Calculates threshold values to divide a set of values into three categories.
    """
    try:
        sorted_values = sorted(values)
        n = len(sorted_values)
        return [sorted_values[n // 3], sorted_values[2 * n // 3]]
    except Exception as e:
        raise ValueError(f"Error in calculate_thresholds: {str(e)}")

async def load_area_intelligence_categories(req: ReqCityCountry = "") -> Dict:
    """
    Loads and returns a dictionary of area intelligence categories.
    """
    return AREA_INTELLIGENCE_CATEGORIES


<<<<<<< HEAD
async def load_area_intelligence_categories(req: ReqCityCountry = "") -> Dict:
    """
    Loads and returns a dictionary of area intelligence categories.
    """
    return AREA_INTELLIGENCE_CATEGORIES


=======
>>>>>>> 5969bd781b948b4e694a8f066317b2c2dc7c303c
async def poi_categories(req: ReqCityCountry = "") -> Dict:
    """
    Provides a comprehensive list of place categories, including Google places,
    real estate, and other custom categories.
    """
    # google_categories = load_google_categories()

    # get city lat and long
    # geo_data = get_req_geodata(req.city_name, req.country_name)
    # non_ggl_categories = fetch_db_categories_by_lat_lng(geo_data.bounding_box)
    # categories = {**google_categories, **non_ggl_categories}

    # combine all category types
    categories = {
        **GOOGLE_CATEGORIES,
        **REAL_ESTATE_CATEGORIES,
        **AREA_INTELLIGENCE_CATEGORIES,
    }

    return categories


async def save_draft_catalog(req: ReqSavePrdcerLyer) -> str:
    try:
        user_data = await load_user_profile(req.user_id)
        if len(req.lyrs) > 0:

            new_ctlg_id = str(uuid.uuid4())
            new_catalog = {
                "prdcer_ctlg_name": req.prdcer_ctlg_name,
                "prdcer_ctlg_id": new_ctlg_id,
                "subscription_price": req.subscription_price,
                "ctlg_description": req.ctlg_description,
                "total_records": req.total_records,
                "lyrs": req.lyrs,
                "thumbnail_url": req.thumbnail_url,
                "ctlg_owner_user_id": req.user_id,
            }
            user_data["prdcer"]["draft_ctlgs"][new_ctlg_id] = new_catalog

            serializable_user_data = convert_to_serializable(user_data)
            await update_user_profile(req.user_id, serializable_user_data)

            return new_ctlg_id
        else:
            raise HTTPException(
                status_code=400,
                detail="No layers found in the request",
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while saving draft catalog: {str(e)}",
        ) from e


async def fetch_gradient_colors() -> List[List]:
    """ """
    return GRADIENT_COLORS


async def given_layer_fetch_dataset(layer_id: str):
    # given layer id get dataset
    user_layer_matching = await load_user_layer_matching()
    layer_owner_id = user_layer_matching.get(layer_id)
    layer_owner_data = await load_user_profile(layer_owner_id)
    try:
        layer_metadata = layer_owner_data["prdcer"]["prdcer_lyrs"][layer_id]
    except KeyError as ke:
        raise HTTPException(
            status_code=404, detail="Producer layer not found for this user"
        ) from ke

    dataset_id, dataset_info = await fetch_dataset_id(layer_id)
    all_datasets = await load_dataset(dataset_id, fetch_full_plan_datasets=True)

    return all_datasets, layer_metadata


# async def fetch_nearest_points_Gmap(
#     req: ReqNearestRoute,
# ) -> List[NearestPointRouteResponse]:
#     """
#     Fetches detailed map data for a specific producer layer.
#     """
#     try:
#         dataset_id, dataset_info = await fetch_dataset_id(req.prdcer_lyr_id)
#         all_datasets = await load_dataset(dataset_id)
#         coordinates_list = [
#             {
#                 "latitude": item["location"]["latitude"],
#                 "longitude": item["location"]["longitude"],
#             }
#             for item in all_datasets
#         ]

#         business_target_coordinates = [
#             {"latitude": point.latitude, "longitude": point.longitude}
#             for point in req.points
#         ]

<<<<<<< HEAD
# async def fetch_nearest_points_Gmap(
#     req: ReqNearestRoute,
# ) -> List[NearestPointRouteResponse]:
#     """
#     Fetches detailed map data for a specific producer layer.
#     """
#     try:
#         dataset_id, dataset_info = await fetch_dataset_id(req.prdcer_lyr_id)
#         all_datasets = await load_dataset(dataset_id)
#         coordinates_list = [
#             {
#                 "latitude": item["location"]["latitude"],
#                 "longitude": item["location"]["longitude"],
#             }
#             for item in all_datasets
#         ]

#         business_target_coordinates = [
#             {"latitude": point.latitude, "longitude": point.longitude}
#             for point in req.points
#         ]

#         nearest_points = await calculate_nearest_points(
#             coordinates_list, business_target_coordinates
#         )

#         Gmap_response = await calculate_nearest_points_drive_time(nearest_points)
#         return Gmap_response
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=400, detail=f"An error occurred: {str(e)}"
#         ) from e


async def filter_for_nearest_points(
    category_coordinates: List[Dict[str, float]],
    bussiness_target_coordinates: List[Dict[str, float]],
    num_points_per_target=3,
) -> List[Dict[str, Any]]:
    nearest_locations = []
    for target in bussiness_target_coordinates:
        distances = []
        for loc in category_coordinates:
            dist = calculate_distance_km(
                (target["longitude"], target["latitude"]),
                (loc["longitude"], loc["latitude"]),
            )
            distances.append(
                {
                    "latitude": loc["latitude"],
                    "longitude": loc["longitude"],
                    "distance": dist,
                }
            )

        # Sort distances and get the nearest 3
        nearest = sorted(distances, key=lambda x: x["distance"])[:num_points_per_target]
        nearest_locations.append(
            {
                "target": target,
                "nearest_coordinates": [
                    (loc["latitude"], loc["longitude"]) for loc in nearest
                ],
            }
        )

    return nearest_locations


async def calculate_nearest_points_drive_time(
    nearest_locations: List[Dict[str, Any]]
) -> List[NearestPointRouteResponse]:
    results = []
    for item in nearest_locations:
        target = item["target"]
        target_routes = NearestPointRouteResponse(target=target, routes=[])

        for nearest in item["nearest_coordinates"]:
            origin = f"{target['latitude']},{target['longitude']}"
            destination = f"{nearest[0]},{nearest[1]}"

            try:
                # Fetch route information between target and nearest location
                route_info = await calculate_distance_traffic_route(origin, destination)
                target_routes.routes.append(route_info)
            except HTTPException as e:
                # Handle HTTP exceptions during the route fetching
                target_routes.routes.append({"error": str(e.detail)})
            except Exception as e:
                # Handle any other exceptions
                target_routes.routes.append({"error": f"An error occurred: {str(e)}"})

        results.append(target_routes)

    return results


def filter_locations_by_drive_time(
    nearest_locations: List[Dict[str, Any]], coverage_minutes: float
) -> List[Dict[str, Any]]:
    """
    Filter coordinates near target locations based on estimated driving distance.

    Args:
        nearest_locations: List of dicts containing targets and their nearest coordinates
        coverage_minutes: Desired drive time in minutes

    Returns:
        List of filtered locations with coordinates within estimated driving distance
    """
    AVERAGE_SPEED_MPS = 11.11  # Average urban speed of 40 km/h = 11.11 m/s
    desired_time_seconds = coverage_minutes * 60  # Convert minutes to seconds
    estimated_distance_meters = AVERAGE_SPEED_MPS * desired_time_seconds

    filtered_nearest_locations: List[Dict[str, Any]] = []
    for location in nearest_locations:
        target = location["target"]
        filtered_coords: List[Tuple[float, float]] = []
        for nearest_coord in location["nearest_coordinates"]:
            actual_distance = geodesic(
                (target["latitude"], target["longitude"]), nearest_coord
            ).meters
            if actual_distance <= estimated_distance_meters:
                filtered_coords.append(nearest_coord)

        filtered_nearest_locations.append(
            {
                "target": target,
                "nearest_coordinates": filtered_coords,  # This might be empty
            }
        )

    return filtered_nearest_locations


def average_metric_of_surrounding_points(
    color_based_on, point, based_on_dataset, radius
):
    lat, lon = (
        point["geometry"]["coordinates"][1],
        point["geometry"]["coordinates"][0],
    )

    nearby_metric_value = []

    for point_2 in based_on_dataset["features"]:
        if color_based_on not in point_2["properties"]:
            continue

        distance = geodesic(
            (lat, lon),
            (
                point_2["geometry"]["coordinates"][1],
                point_2["geometry"]["coordinates"][0],
            ),
        ).meters

        if distance <= radius:
            nearby_metric_value.append(point_2["properties"][color_based_on])

    if nearby_metric_value:
        cleaned_list = [float(x) for x in nearby_metric_value 
                        if str(x).strip() and not isinstance(x, bool)]
        return np.mean(cleaned_list)
    else:
        return None


def calculate_distance(coord1, coord2):
    """
    Calculate the distance between two points (latitude and longitude) in meters.
    """
    return geopy.distance.distance(
        (coord1["latitude"], coord1["longitude"]),
        (coord2["latitude"], coord2["longitude"]),
    ).meters


async def process_color_based_on(
    req: ReqGradientColorBasedOnZone,
) -> List[ResGradientColorBasedOnZone]:
    change_layer_dataset, change_layer_metadata = await given_layer_fetch_dataset(
        req.change_lyr_id
    )
    based_on_layer_dataset, based_on_layer_metadata = await given_layer_fetch_dataset(
        req.based_on_lyr_id
    )
    based_on_coordinates = [
        {
            "latitude": point["geometry"]["coordinates"][1],
            "longitude": point["geometry"]["coordinates"][0],
        }
        for point in based_on_layer_dataset["features"]
    ]

    to_be_changed_coordinates = [
        {
            "latitude": point["geometry"]["coordinates"][1],
            "longitude": point["geometry"]["coordinates"][0],
        }
        for point in change_layer_dataset["features"]
    ]
    if (
        req.coverage_property == "drive_time"
    ):  # currently drive does not take into account ANY based on property

        # Get nearest points
        # instead of always producing three pointsthat are nearestI want totake the amount of time that the user wantedto have his location to be inand find what would bethe equivalent distance assumingregular drive conditions and regular speed limitand have that distance in metersbe the radius that we will use to determine the points that are closeand then we will find the nearest pointssuch that its maximum of three pointsbut maybe within that distancewe can only find one point
        nearest_locations = await filter_for_nearest_points(
            based_on_coordinates, to_be_changed_coordinates, num_points_per_target=2
        )

        filtered_nearest_locations = filter_locations_by_drive_time(
            nearest_locations, req.coverage_value
        )

        # Calculate routes with Google Maps
        route_results = await calculate_nearest_points_drive_time(
            filtered_nearest_locations
        )

        # Main function
        within_time_features = []
        outside_time_features = []
        unallocated_features = []

        for target_routes in route_results:
            min_static_time = float("inf")

            # Get minimum static drive time from routes
            for route in target_routes.routes:
                if route.route and route.route[0].static_duration:
                    static_time = int(route.route[0].static_duration.replace("s", ""))
                    min_static_time = min(min_static_time, static_time)

            # Find the point with matching coordinates
            for change_point in change_layer_dataset["features"]:
                if (
                    change_point["geometry"]["coordinates"][1]
                    == target_routes.target["latitude"]
                    and change_point["geometry"]["coordinates"][0]
                    == target_routes.target["longitude"]
                ):

                    feature = assign_point_properties(change_point)

                    if min_static_time != float("inf"):
                        drive_time_minutes = min_static_time / 60
                        if drive_time_minutes <= req.coverage_value:
                            within_time_features.append(feature)
                        else:
                            outside_time_features.append(feature)
                    else:
                        unallocated_features.append(feature)
                    break

        # Create the three layers
        new_layers = []
        base_layer_name = f"{req.change_lyr_name} based on {req.based_on_lyr_name}"

        layer_configs = [
            {
                "features": within_time_features,
                "category": "within_drivetime",
                "name_suffix": "Within Drive Time",
                "color": req.color_grid_choice[0],
                "legend": f"Drive Time ≤ {req.coverage_value} m",
                "description": f"Points within {req.coverage_value} minutes drive time",
            },
            {
                "features": outside_time_features,
                "category": "outside_drivetime",
                "name_suffix": "Outside Drive Time",
                "color": req.color_grid_choice[-1],
                "legend": f"Drive Time > {req.coverage_value} m",
                "description": f"Points outside {req.coverage_value} minutes drive time",
            },
            {
                "features": unallocated_features,
                "category": "unallocated_drivetime",
                "name_suffix": "Unallocated Drive Time",
                "color": "#FFFFFF",
                "legend": "No route available",
                "description": "Points with no available route information",
            },
        ]

        for config in layer_configs:
            if config["features"]:
                new_layers.append(
                    ResGradientColorBasedOnZone(
                        type="FeatureCollection",
                        features=config["features"],
                        properties=list(
                            config["features"][0].get("properties", {}).keys()
                        ),
                        prdcer_layer_name=f"{base_layer_name} ({config['name_suffix']})",
                        prdcer_lyr_id=str(uuid.uuid4()),
                        sub_lyr_id=f"{req.change_lyr_id}_{config['category']}_{req.based_on_lyr_id}",
                        bknd_dataset_id=req.change_lyr_id,
                        points_color=config["color"],
                        layer_legend=config["legend"],
                        layer_description=f"{config['description']}. Layer {req.change_lyr_id} based on {req.based_on_lyr_id}",
                        records_count=len(config["features"]),
                        city_name=change_layer_metadata.get(
                            "city_name", ""
                        ),  # Added city_name field
                        is_zone_lyr="true",
                    )
                )

        return new_layers


    if req.color_based_on == "name":
        # Validate input conditions
        if not req.list_names:
            raise ValueError("list_names must be provided when color_based_on is 'name'.")
        if req.based_on_lyr_id != req.change_lyr_id:
            raise ValueError("Based_on and change layers must be identical for name-based coloring")

        # Normalize names for case-insensitive comparison
        list_names_lower = [name.strip().lower() for name in req.list_names]
        
        # Determine colors to use
        original_color = req.change_lyr_orginal_color
        new_color = req.change_lyr_new_color

        # Categorize features
        matched_features = []
        unmatched_features = []
        
        for feature in change_layer_dataset["features"]:
            feature_name = feature["properties"].get("name", "").strip().lower()
            
            # Check for partial substring matches
            if any(search_name in feature_name for search_name in list_names_lower):
                matched_features.append(assign_point_properties(feature))
            else:
                unmatched_features.append(assign_point_properties(feature))

        # Create result layers
        new_layers = []
        base_layer_name = f"{req.change_lyr_name} - Name Match"

        if matched_features:
            new_layers.append(
                ResGradientColorBasedOnZone(
                    type="FeatureCollection",
                    features=matched_features,
                    properties=list(matched_features[0].get("properties", {}).keys()),
                    prdcer_layer_name=f"{base_layer_name} (Matched)",
                    prdcer_lyr_id=str(uuid.uuid4()),
                    sub_lyr_id=f"{req.change_lyr_id}_matched",
                    bknd_dataset_id=req.change_lyr_id,
                    points_color=new_color,
                    layer_legend=f"Contains: {', '.join(req.list_names)}",
                    layer_description=f"Features matching names: {', '.join(req.list_names)}",
                    records_count=len(matched_features),
                    city_name=change_layer_metadata.get("city_name", ""),
                    is_zone_lyr="true",
                )
            )

        if unmatched_features:
            new_layers.append(
                ResGradientColorBasedOnZone(
                    type="FeatureCollection",
                    features=unmatched_features,
                    properties=list(unmatched_features[0].get("properties", {}).keys()),
                    prdcer_layer_name=f"{base_layer_name} (Unmatched)",
                    prdcer_lyr_id=str(uuid.uuid4()),
                    sub_lyr_id=f"{req.change_lyr_id}_unmatched",
                    bknd_dataset_id=req.change_lyr_id,
                    points_color=original_color,
                    layer_legend="No name match",
                    layer_description="Features without matching names",
                    records_count=len(unmatched_features),
                    city_name=change_layer_metadata.get("city_name", ""),
                    is_zone_lyr="true",
                )
            )

        return new_layers
    else:

        # Calculate influence scores for change_layer_dataset and store them
        influence_scores = []
        point_influence_map = {}
        for change_point in change_layer_dataset["features"]:
            change_point["id"] = str(uuid.uuid4())
            surrounding_metric_avg = average_metric_of_surrounding_points(
                req.color_based_on,
                change_point,
                based_on_layer_dataset,
                req.coverage_value,
            )
            if surrounding_metric_avg is not None:
                influence_scores.append(surrounding_metric_avg)
                point_influence_map[change_point["id"]] = surrounding_metric_avg

        # Create layers
        new_layers = []

        # Calculate thresholds based on influence scores
        percentiles = [16.67, 33.33, 50, 66.67, 83.33]

        # Initialize layer data
        if not influence_scores:
            # If no scores, create single layer of unallocated points
            layer_data = [[]] * (len(percentiles) + 1) + [
                [
                    assign_point_properties(point)
                    for point in change_layer_dataset["features"]
                ]
            ]
            thresholds = []  # Empty thresholds since we have no scores
        else:
            # Calculate thresholds if we have influence scores
            thresholds = np.percentile(influence_scores, percentiles)
            layer_data = [[] for _ in range(len(thresholds) + 2)]

            # Assign points to layers
            for change_point in change_layer_dataset["features"]:
                surrounding_metric_avg = point_influence_map.get(change_point["id"])
                feature = assign_point_properties(change_point)

                if surrounding_metric_avg is None:
                    layer_index = -1  # Last layer (unallocated)
                    feature["properties"]["influence_score"] = None
                else:
                    layer_index = next(
                        (
                            i
                            for i, threshold in enumerate(thresholds)
                            if surrounding_metric_avg <= threshold
                        ),
                        len(thresholds),
                    )
                    feature["properties"]["influence_score"] = surrounding_metric_avg

                layer_data[layer_index].append(feature)

        # Create layers only for non-empty data
        for i, data in enumerate(layer_data):
            if data:
                color = (
                    req.color_grid_choice[i]
                    if i < len(req.color_grid_choice)
                    else "#FFFFFF"
                )
                if i == len(layer_data) - 1:
                    layer_name = "Unallocated Points"
                    layer_legend = "No nearby points"
                elif i == 0:
                    layer_name = f"Gradient Layer {i+1}"
                    layer_legend = f"Influence Score < {thresholds[0]:.2f}"
                elif i == len(thresholds):
                    layer_name = f"Gradient Layer {i+1}"
                    layer_legend = f"Influence Score > {thresholds[-1]:.2f}"
                else:
                    layer_name = f"Gradient Layer {i+1}"
                    layer_legend = (
                        f"Influence Score {thresholds[i-1]:.2f} - {thresholds[i]:.2f}"
                    )

                # Extract properties from first feature if available
                properties = []
                if data and len(data) > 0:
                    first_feature = data[0]
                    properties = list(first_feature.get("properties", {}).keys())

                new_layers.append(
                    ResGradientColorBasedOnZone(
                        type="FeatureCollection",
                        features=data,
                        properties=properties,  # Add the properties list here
                        prdcer_layer_name=layer_name,
                        prdcer_lyr_id=req.change_lyr_id,
                        sub_lyr_id=f"{req.change_lyr_id}_gradient_{i+1}",
                        bknd_dataset_id=req.change_lyr_id,
                        points_color=color,
                        layer_legend=layer_legend,
                        layer_description=f"Gradient layer based on nearby {req.color_based_on} influence",
                        records_count=len(data),
                        city_name=change_layer_metadata.get("city_name", ""),
                        is_zone_lyr="true",
                    )
                )

        return new_layers
=======
#         nearest_points = await calculate_nearest_points(
#             coordinates_list, business_target_coordinates
#         )
>>>>>>> 5969bd781b948b4e694a8f066317b2c2dc7c303c

#         Gmap_response = await calculate_nearest_points_drive_time(nearest_points)
#         return Gmap_response
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=400, detail=f"An error occurred: {str(e)}"
#         ) from e

async def get_user_profile(req):
    return await load_user_profile(req.user_id)


async def update_profile(req):
    return await update_user_profile_settings(req)


<<<<<<< HEAD
=======
# llm agent call


>>>>>>> 5969bd781b948b4e694a8f066317b2c2dc7c303c
# Apply the decorator to all functions in this module
apply_decorator_to_module(logger)(__name__)
