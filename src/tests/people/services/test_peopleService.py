from unittest import mock
from unittest.mock import call

from src.app.people.daos.peopleDAO import PeopleDAO
from src.app.people.factories.peopleFactory import PeopleFactory
from src.app.people.models.people import FullViewPerson
from src.app.people.services.peopleService import PeopleService
from src.app.people.models.database import models
from pytest_unordered import unordered


@mock.patch.object(PeopleFactory, 'create_person_from_person_entity')
@mock.patch.object(PeopleDAO, 'get_all')
def test_get_all(mock_get_all, mock_create_person_from_person_entity):
    peopleDAO = PeopleDAO()
    peopleFactory = PeopleFactory()
    people_service = PeopleService(peopleDAO=peopleDAO, people_factory=peopleFactory)
    person_1 = models.Person(id=1, first_name="John")
    person_2 = models.Person(id=2, first_name="Jane")
    person_3 = models.Person(id=3, first_name="Jimmy")
    mock_get_all.return_value = [person_1, person_2, person_3]

    full_view_person_1 = FullViewPerson(id=1, first_name='John')
    full_view_person_2 = FullViewPerson(id=2, first_name='Jane')
    full_view_person_3 = FullViewPerson(id=3, first_name='Jimmy')

    def side_effect(person_entity: models.Person, include_profile_image=True, include_households=True) -> FullViewPerson:
        if person_entity.id == 1:
            return full_view_person_1
        elif person_entity.id == 2:
            return full_view_person_2
        elif person_entity.id == 3:
            return full_view_person_3

    mock_create_person_from_person_entity.side_effect = side_effect

    people = people_service.get_all()
    # for some reason the order of parameters matters, and is reversed to what is actually passed in, in the code.
    calls = [call(include_households=True, include_profile_image=True, person_entity=person_1),
             call(include_households=True, include_profile_image=True, person_entity=person_2),
             call(include_households=True, include_profile_image=True, person_entity=person_3)]
    mock_create_person_from_person_entity.assert_has_calls(calls, any_order=True)
                                                                #call(person_2, include_profile_image=True, include_households=True),
                                                                #call(person_3, include_profile_image=True, include_households=True)])

    assert len(people) == 3
    assert people == unordered([full_view_person_1, full_view_person_2, full_view_person_3])

