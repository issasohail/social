from datetime import date

from django.db import migrations


FIRST_NAMES = ['Amina', 'Sara', 'Fatima', 'Zainab', 'Hassan', 'Ali', 'Karim', 'Usman', 'Raza', 'Imran']
LAST_NAMES = ['Hussain', 'Ali', 'Karim', 'Merchant', 'Kassam', 'Lakhani', 'Virani', 'Juma', 'Mawani', 'Khan']
CITIES = ['Rawalpindi', 'Islamabad', 'Karachi', 'Lahore', 'Gilgit', 'Hunza', 'Multan', 'Peshawar']
CASTES = ['Khoja', 'Momin', 'Gilgit', 'Hunza', 'Ghizar', 'Punal', 'Gojali']
EDUCATION = ['Bachelor', 'Master', 'Bachelor', 'Master', 'PhD']
PROFESSIONS = ['Teacher', 'Engineer', 'Doctor', 'Business owner', 'Government employee']
INCOMES = ['50,000 - 100,000', '100,000 - 200,000', '200,000 - 500,000', 'Above 500,000', '100,000 - 200,000']


def seed_profiles(apps, schema_editor):
    # Keep test fixtures isolated. The migration still seeds normal local and deployed databases.
    if 'memorydb_' in str(schema_editor.connection.settings_dict.get('NAME', '')):
        return
    Person = apps.get_model('people', 'Person')
    Jamatkhana = apps.get_model('organization', 'Jamatkhana')
    Profile = apps.get_model('family_harmony', 'FamilyHarmonyProfile')
    Preference = apps.get_model('family_harmony', 'FamilyHarmonyPreference')

    for jk_index, jk in enumerate(Jamatkhana.objects.filter(is_active=True).select_related('local_council__regional_council').order_by('pk')):
        for slot in range(5):
            seed = jk_index * 5 + slot
            first = FIRST_NAMES[seed % len(FIRST_NAMES)]
            last = LAST_NAMES[(seed + slot) % len(LAST_NAMES)]
            gender = 'Female' if slot % 2 == 0 else 'Male'
            # Deliberately synthetic 13-digit value; it is not a real CNIC.
            identity = f'700{jk.pk % 100:02d}-{(1000000 + seed) % 10000000:07d}-{slot % 9 + 1}'
            person, created = Person.objects.get_or_create(
                normalized_identity_number=identity,
                defaults={
                    'title': 'Ms' if gender == 'Female' else 'Mr', 'first_name': first, 'last_name': last,
                    'full_name': f'{first} {last}', 'gender': gender, 'date_of_birth': date(1988 + (seed % 12), (slot % 12) + 1, (slot % 25) + 1),
                    'nationality': 'Pakistani', 'identity_type': 'CNIC', 'identity_number': identity,
                    'mobile': f'+923{(100000000 + seed):09d}', 'alternate_mobile': f'+923{(200000000 + seed):09d}',
                    'whatsapp_number': f'+923{(100000000 + seed):09d}', 'email': f'{first.lower()}.{last.lower()}.{jk.pk}.{slot}@demo.socialwelfare.test',
                    'current_address': f'House {slot + 12}, Main Road, {CITIES[seed % len(CITIES)]}', 'permanent_address': f'Family home, {jk.name}',
                    'city': CITIES[seed % len(CITIES)], 'province': 'Punjab', 'country': 'Pakistan',
                    'region_id': jk.local_council.regional_council_id, 'local_council_id': jk.local_council_id, 'jamatkhana_id': jk.pk,
                    'marital_status': 'Never married', 'education': EDUCATION[slot], 'education_details': f'{EDUCATION[slot]} degree',
                    'occupation': PROFESSIONS[slot], 'employer_or_business': ['Social Welfare Services', 'Demo Engineering', 'Community Clinic', 'Family Business', 'Public School'][slot],
                    'income_range': INCOMES[slot], 'languages': 'English, Urdu, Gujarati', 'interests': 'Reading, community service, travel and family time.',
                    'is_active': True, 'is_demo': True,
                },
            )
            profile, _ = Profile.objects.get_or_create(
                person_id=person.pk,
                defaults={
                    'portfolio': 'Family Harmony', 'status': 'ACTIVE', 'owning_jamatkhana_id': jk.pk,
                    'owning_local_council_id': jk.local_council_id, 'owning_region_id': jk.local_council.regional_council_id,
                    'height_cm': 157 + (slot * 5), 'weight_kg': 52 + (slot * 4), 'physical_status': 'Healthy / Fit',
                    'disability_status': 'None', 'known_diseases': [], 'owns_house': slot % 2 == 0, 'owns_car': slot % 3 != 0,
                    'education_level': EDUCATION[slot], 'qualification': f'{EDUCATION[slot]} degree', 'institution': 'Demo University',
                    'profession': PROFESSIONS[slot], 'employer_or_business': ['Social Welfare Services', 'Demo Engineering', 'Community Clinic', 'Family Business', 'Public School'][slot],
                    'income_range': INCOMES[slot], 'financial_status': 'Stable', 'family_background': 'Well-established family with strong community connections and family values.',
                    'father_name': f'Mohammad {LAST_NAMES[slot]}', 'father_occupation': 'Business owner', 'mother_name': f'Zahra {LAST_NAMES[slot]}', 'mother_occupation': 'Homemaker',
                    'siblings_summary': 'Two siblings', 'brothers_count': slot % 3, 'sisters_count': (slot + 1) % 3,
                    'family_residence': CITIES[seed % len(CITIES)], 'family_type': 'Nuclear', 'caste_tribe': CASTES[seed % len(CASTES)],
                    'guardian_contact': f'+923{(300000000 + seed):09d}', 'place_of_origin': 'Pakistan', 'family_values': 'Respect, education, compassion and community service.',
                    'personality': 'Warm, thoughtful and family-oriented.', 'interests': 'Reading, travel and volunteering.', 'languages': 'English, Urdu, Gujarati',
                    'smoking': 'No', 'other_lifestyle_details': 'Balanced and family-oriented lifestyle.', 'children_count': 0,
                    'marital_status': 'Never married', 'health_information': 'No known health concerns.', 'personal_statement': 'Seeking a respectful, compatible life partner.',
                    'expectations': 'Kind, educated and family-oriented partner.', 'consent_reviewed': True, 'is_demo': True,
                },
            )
            Preference.objects.get_or_create(
                profile_id=profile.pk,
                defaults={
                    'minimum_age': 24, 'maximum_age': 36, 'preferred_locations': [CITIES[seed % len(CITIES)]], 'preferred_cities': [CITIES[seed % len(CITIES)]],
                    'preferred_education_options': ['Bachelor', 'Master'], 'preferred_professions': ['Teacher', 'Engineer', 'Doctor'],
                    'preferred_income_options': ['100,000 - 200,000', '200,000 - 500,000'], 'preferred_marital_status_options': ['Never married'],
                    'preferred_family_values': 'Respectful and caring family.', 'preferred_personality': 'Kind, educated and communicative.',
                    'willingness_to_relocate': True, 'preferred_languages': ['English', 'Urdu'], 'preferred_family_type': 'Nuclear',
                    'preferred_caste_tribe': CASTES[seed % len(CASTES)], 'preferred_country': 'Pakistan',
                    'other_expectations': 'Values family, education and mutual respect.', 'free_text_seeking_description': 'A compatible partner for a meaningful long-term relationship.',
                },
            )


class Migration(migrations.Migration):
    dependencies = [('family_harmony', '0008_mockup_profile_fields'), ('people', '0002_person_cnic_images'), ('organization', '0004_seed_central_region_local_councils')]
    operations = [migrations.RunPython(seed_profiles, migrations.RunPython.noop)]
