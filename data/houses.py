import pandas as pd

from pydantic import BaseModel
from datetime import date

# Dataset Overview

# - **BHK**: Number of Bedrooms, Hall, Kitchen.
# - **Rent**: Rent of the Houses/Apartments/Flats.
# - **Size**: Size of the Houses/Apartments/Flats in Square Feet.
# - **Floor**: Houses/Apartments/Flats situated in which Floor and Total Number of Floors (Example: Ground out of 2, 3 out of 5, etc.)
# - **Area Type**: Size of the Houses/Apartments/Flats calculated on either Super Area or Carpet Area or Build Area.
# - **Area Locality**: Locality of the Houses/Apartments/Flats.
# - **City**: City where the Houses/Apartments/Flats are Located.
# - **Furnishing Status**: Furnishing Status of the Houses/Apartments/Flats, either it is Furnished or Semi-Furnished or Unfurnished.
# - **Tenant Preferred**: Type of Tenant Preferred by the Owner or Agent.
# - **Bathroom**: Number of Bathrooms.
# - **Point of Contact**: Whom should you contact for more information regarding the Houses/Apartments/Flats.


class House(BaseModel):
    posted_on: date
    bhk: int
    rent: int
    size: int
    floor: str
    area_type: str
    area_locality: str
    city: str
    furnishing_status: str
    tenant_preferred: str
    bathroom: int
    point_of_contact: str

    @staticmethod
    def from_dataframe(dataframe: pd.DataFrame):
        #'Posted On', 'BHK', 'Rent', 'Size', 'Floor', 'Area Type', 'Area Locality', 'City', 'Furnishing Status', 'Tenant Preferred', 'Bathroom', 'Point of Contact'
        return [
            House(
                posted_on=row["Posted On"],
                bhk=row["BHK"],
                rent=row["Rent"],
                size=row["Size"],
                floor=row["Floor"], # [i or floor_name] out of j
                area_type=row["Area Type"].lower(),
                area_locality=row["Area Locality"].lower(),
                city=row["City"].lower(), # ['Kolkata' 'Mumbai' 'Bangalore' 'Delhi' 'Chennai' 'Hyderabad']
                furnishing_status=row["Furnishing Status"].lower(), # ['Unfurnished' 'Semi-Furnished' 'Furnished']
                tenant_preferred=row["Tenant Preferred"].lower(), # ['Bachelors/Family' 'Bachelors' 'Family']
                bathroom=row["Bathroom"],
                point_of_contact=row["Point of Contact"].lower() # ['Contact Owner' 'Contact Agent' 'Contact Builder']
            )
            for _, row in dataframe.iterrows()
        ]

    def __str__(self):
        return f"A {self.bhk} BHK House ({self.size} sq.ft.) in {self.area_locality},{self.city} for {self.rent}. Suitable for {self.tenant_preferred}, please contact {self.point_of_contact} for more information."
    
    