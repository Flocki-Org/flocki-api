class HouseholdUtils:

    def get_household_ids_to_remove(self, existing_household_ids, new_household_ids):
        return [household_id for household_id in existing_household_ids if
                household_id not in new_household_ids]

    def get_household_ids_to_add(self, existing_household_ids, new_household_ids):
        return [household_id for household_id in new_household_ids if
                household_id not in existing_household_ids]

    def get_existing_household_ids(self, person_entity):
        return [household.id for household in person_entity.households]

    def get_people_ids_to_remove(self, existing_people_ids, new_people_ids):
        return [person_id for person_id in existing_people_ids if
                person_id not in new_people_ids]

    def get_people_ids_to_add(self, existing_people_ids, new_people_ids):
        return [person_id for person_id in new_people_ids if
                person_id not in existing_people_ids]

    def get_existing_people_ids(self, household_entity):
        return [person.id for person in household_entity.people]