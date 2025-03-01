import pandas as pd

from typing import List, Dict
from data.houses import House

class Database:
    def __init__(self, database_path):
        self.database_path = database_path
        self.database: List[House] = None
        self.init_db(database_path)

    def init_db(self, database_path):
        """Initialize the database with the given path."""
        if database_path:
            dataframe = pd.read_csv(database_path)
            self.database = House.from_dataframe(dataframe)
            print(f"Database initialized with {len(self.database)} houses.")

    def get_houses(self, slots: Dict[str, str]) -> List[House]:
        """Get all houses from the database that match the given slots."""

        # Filter slots values to match the database types
        house_bhk = slots.get("house_bhk")
        if isinstance(house_bhk, str):
            if " " in house_bhk:
                house_bhk = [int(word) for word in house_bhk.split() if word.isdigit()]
            else:
                house_bhk = [int(house_bhk)]
        house_bhk = min(house_bhk) if house_bhk else 0
        house_bhk = [i for i in range(house_bhk, 6)]
        
        house_size = slots.get("house_size")
        if isinstance(house_size, str):
            if " " in house_size:
                house_size = [int(word) for word in house_size.split() if word.isdigit()]
            else:
                house_size = [int(house_size)]
        house_size = min(house_size) if house_size else 0

        house_rent = slots.get("house_rent")
        if isinstance(house_rent, str):
            if " " in house_rent:
                house_rent = [int(word) for word in house_rent.split() if word.isdigit()]
            else:
                house_rent = [int(house_rent)]
        house_rent = max(house_rent) if house_rent else 1000000

        house_location = slots.get("house_location")
        house_location = house_location.lower()
        house_city = slots.get("house_city")
        house_city = house_city.lower()
        house_furnished = slots.get("house_furnished")
        house_furnished = house_furnished.lower()

        print(f"Filtering houses with BHK: {house_bhk}, Size: {house_size}, Rent: {house_rent}, Location: {house_location}, City: {house_city}, Furnished: {house_furnished}")
        print("Current filters' types:", type(house_bhk), type(house_size), type(house_rent), type(house_location), type(house_city), type(house_furnished))

        #! to be tested
        filter_func = lambda house: house.bhk in house_bhk and \
            house.size >= house_size and \
            house.rent <= house_rent and \
            house_city in house.city and \
            house_furnished in house.furnishing_status and \
            house_location in house.area_locality

        # Filter houses based on the slots
        filtered_houses = filter(filter_func, self.database)

        return list(filtered_houses)
