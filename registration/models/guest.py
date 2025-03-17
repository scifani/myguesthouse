from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class GuestType(Enum):
  SINGLE = "Single"
  HOUSE_HEAD = "HouseHead"
  GROUP_LEADER = "GroupLeader"
  FAMILY_MEMBER = "FamilyMember"
  GROUP_MEMBER = "GroupMember"

class GuestGender(Enum):
  MALE = "M"
  FEMALE = "F"
  UNKNOWN = "X"

@dataclass
class Guest:
  guest_type: GuestType
  arrival_date: datetime
  num_days: int
  last_name: str
  first_name: str
  gender: GuestGender
  birth_date: str
  birth_city: str
  birth_province: str
  birth_country: str
  citizenship: str
  document_type: str
  document_number: str
  document_issue_place: str
