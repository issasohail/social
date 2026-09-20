from django.db import transaction

from .models import Person, PersonRelationship


RECIPROCAL_TYPES = {
    'spouse': 'spouse',
    'father': 'son',
    'mother': 'daughter',
    'son': 'father',
    'daughter': 'mother',
    'brother': 'brother',
    'sister': 'sister',
    'guardian': 'dependent',
    'dependent': 'guardian',
}


@transaction.atomic
def link_relationship(person, related_person, relationship_type):
    if person == related_person:
        raise ValueError('A person cannot be related to themselves.')
    relationship, _ = PersonRelationship.objects.get_or_create(
        person=person, related_person=related_person, relationship_type=relationship_type,
    )
    reciprocal = RECIPROCAL_TYPES.get(relationship_type)
    if reciprocal:
        PersonRelationship.objects.get_or_create(
            person=related_person, related_person=person, relationship_type=reciprocal,
        )
    return relationship
