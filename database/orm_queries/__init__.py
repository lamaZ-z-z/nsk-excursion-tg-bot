'''Init module; orm queries to get data from db'''
from .places_suggest import (
    add_place_suggestion,
    get_suggestion_by_id,
    get_all_suggestions,
    suggestion_status_update
)
from .districts import (
    add_district, get_all_districts,
    get_district, orm_districts_on_start,
    get_district_id, update_district
)
from .main import add_main_banner, get_main_banner, update_main_banner
from .places import (
    add_place, get_place,
    get_places_by_district,
    get_all_places,
    add_place_from_suggestion,
    delete_place
)
