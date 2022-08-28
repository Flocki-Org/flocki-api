class HouseholdUtils:

    @staticmethod
    def get_household_ids_to_remove(existing_household_ids, new_household_ids):
        return [household_id for household_id in existing_household_ids if
                household_id not in new_household_ids]

    @staticmethod
    def get_household_ids_to_add(existing_household_ids, new_household_ids):
        return [household_id for household_id in new_household_ids if
                household_id not in existing_household_ids]

    @staticmethod
    def get_existing_household_ids(person_entity):
        return [household.id for household in person_entity.households]

    @staticmethod
    def get_people_ids_to_remove(existing_people_ids, new_people_ids):
        return [person_id for person_id in existing_people_ids if
                person_id not in new_people_ids]

    @staticmethod
    def get_people_ids_to_add(existing_people_ids, new_people_ids):
        return [person_id for person_id in new_people_ids if
                person_id not in existing_people_ids]

    @staticmethod
    def get_existing_people_ids(household_entity):
        return [person.id for person in household_entity.people]