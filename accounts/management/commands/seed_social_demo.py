from datetime import date
from io import BytesIO

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from PIL import Image, ImageDraw

from boards.models import Board
from family_harmony.models import FamilyHarmonyPreference, FamilyHarmonyProfile
from organization.models import Jamatkhana, LocalCouncil, NationalCouncil, RegionalCouncil
from people.models import Person


class Command(BaseCommand):
    help = 'Create fictional Social Welfare demo data.'

    def add_arguments(self, parser):
        parser.add_argument('--confirm', action='store_true')
        parser.add_argument('--jks-per-local', type=int, default=2)
        parser.add_argument('--profiles-per-jk', type=int, default=5)

    @transaction.atomic
    def handle(self, *args, **options):
        if not options['confirm']:
            raise CommandError('Pass --confirm to create demo data.')
        for name, code in [('Family Harmony', 'FAMILY_HARMONY'), ('Seniors', 'SENIORS'), ('Economic Support', 'ECONOMIC_SUPPORT'), ('Children', 'CHILDREN')]:
            Board.objects.get_or_create(code=code, defaults={'name': name})
        first_names = ['Amina', 'Zara', 'Mariam', 'Sana', 'Hiba', 'Fatima', 'Sarah', 'Nadia', 'Hassan', 'Ibrahim', 'Saad', 'Danish', 'Bilal', 'Arman', 'Rayan', 'Owais']
        last_names = ['Khan', 'Hussain', 'Shah', 'Merchant', 'Kassam', 'Bakhshi', 'Ali', 'Momin', 'Rizvi', 'Qureshi', 'Siddiqui', 'Jaffar']
        cities = ['Islamabad', 'Karachi', 'Lahore', 'Rawalpindi', 'Peshawar', 'Multan', 'Hyderabad', 'Faisalabad']
        professions = ['Public health officer', 'Software engineer', 'Chartered accountant', 'Teacher', 'Architect', 'Business owner', 'Project manager', 'Research associate']
        educations = ['Masters in Economics', 'BS Computer Science', 'MBA Finance', 'Masters in Education', 'Bachelors in Architecture', 'MBBS', 'LLB', 'Bachelors in Business']
        admin_user = get_user_model().objects.filter(is_superuser=True).first()
        national = NationalCouncil.objects.create(name='National Social Welfare Council', code='DEMO-NATIONAL')
        for region_no in range(1, 5):
            region = RegionalCouncil.objects.create(national_council=national, name=['Northern Region', 'Central Region', 'Southern Region', 'Western Region'][region_no - 1], code=f'DEMO-R{region_no}')
            for local_no in range(1, 4):
                local = LocalCouncil.objects.create(regional_council=region, name=f'{cities[(region_no + local_no) % len(cities)]} Local Council', code=f'DEMO-R{region_no}-L{local_no}')
                for jk_no in range(1, options['jks_per_local'] + 1):
                    jk = Jamatkhana.objects.create(local_council=local, name=f'{cities[(region_no + local_no + jk_no) % len(cities)]} Jamatkhana', short_name=f'JK {region_no}-{local_no}-{jk_no}', code=f'DEMO-R{region_no}-L{local_no}-J{jk_no}')
                    for profile_no in range(1, options['profiles_per_jk'] + 1):
                        index = (region_no * 100 + local_no * 10 + jk_no * 3 + profile_no) % len(first_names)
                        gender = 'Female' if profile_no % 2 else 'Male'
                        first_name = first_names[index]
                        last_name = last_names[(index + region_no) % len(last_names)]
                        city = cities[(region_no + local_no) % len(cities)]
                        person = Person.objects.create(title='Mr.' if gender == 'Male' else 'Ms.', first_name=first_name, last_name=last_name, gender=gender, date_of_birth=date(1982 + profile_no, (profile_no % 9) + 1, (profile_no % 26) + 1), nationality='Pakistani', identity_type=Person.IdentityType.OTHER, identity_number=f'DEMO-ID-{region_no}{local_no}{jk_no}{profile_no:02d}', mobile=f'+92 300 55{region_no:02d}{local_no}{jk_no}{profile_no:02d}', alternate_mobile=f'+92 301 44{region_no:02d}{local_no}{jk_no}{profile_no:02d}', whatsapp_number=f'+92 300 55{region_no:02d}{local_no}{jk_no}{profile_no:02d}', email=f'candidate{region_no}{local_no}{jk_no}{profile_no}@example.test', current_address=f'House {profile_no}, Community Avenue, {city}', permanent_address=f'Family House, Main Road, {city}', city=city, province='Punjab' if region_no in (1, 2) else 'Sindh', country='Pakistan', marital_status='Never Married', education=educations[index % len(educations)], education_details=f'{educations[index % len(educations)]}, completed with distinction', occupation=professions[index % len(professions)], employer_or_business='Established local organization', income_range='PKR 150,000 - 250,000', languages='English, Urdu', interests='Reading, community work, travel, photography', facebook_url='https://example.test/facebook/demo', linkedin_url='https://example.test/linkedin/demo', instagram_url='https://example.test/instagram/demo', other_social_url='https://example.test/profile/demo', region=region, local_council=local, jamatkhana=jk, created_by=admin_user, updated_by=admin_user, is_demo=True)
                        person.photo.save(f'demo-avatar-{region_no}-{local_no}-{jk_no}-{profile_no}.jpg', ContentFile(self._avatar(first_name, last_name, index)), save=True)
                        profile = FamilyHarmonyProfile.objects.create(person=person, status='ACTIVE', assigned_officer=admin_user, owning_jamatkhana=jk, owning_local_council=local, owning_region=region, height_cm=155 + (index % 25), education_level='Masters' if index % 2 else 'Bachelors', qualification=educations[index % len(educations)], institution='Community University', profession=professions[index % len(professions)], employer_or_business='Established local organization', years_experience=f'{3 + index % 12} years', income_range='PKR 150,000 - 250,000', financial_status='Financially stable', family_background='Respectable, educated family with strong community values.', place_of_origin=city, family_values='Mutual respect, kindness, and family responsibility.', personality='Honest, thoughtful, caring, and family-oriented.', interests='Reading, community work, travel, photography', languages='English, Urdu', smoking='Non-smoker', other_lifestyle_details='Enjoys community events and a balanced lifestyle.', marital_status='Never Married', children_count=0, child_details='No children', previous_marriage_notes='Not applicable', disabilities='None reported', health_information='Good general health reported; subject to consent review.', personal_statement='Interested in building a peaceful and respectful family life.', expectations='Seeking a mature, responsible, and emotionally intelligent partner.', facebook_url='https://example.test/facebook/demo', instagram_url='https://example.test/instagram/demo', linkedin_url='https://example.test/linkedin/demo', notes='Fictional demonstration record. Review consent before sharing.', is_demo=True)
                        FamilyHarmonyPreference.objects.create(profile=profile, minimum_age=25, maximum_age=45, preferred_locations=[person.city], preferred_education='Well educated', preferred_professions=['Professional or business owner'], preferred_marital_status='Never Married preferred', preferred_family_values='Respectful and family-oriented', preferred_personality='Kind, mature, responsible', willingness_to_relocate=True, preferred_languages=['English', 'Urdu'], free_text_seeking_description='Please contact only if serious about marriage.')
        self.stdout.write(self.style.SUCCESS('Fictional demo data created.'))

    @staticmethod
    def _avatar(first_name, last_name, index):
        image = Image.new('RGB', (480, 480), ((40 + index * 17) % 180, (100 + index * 11) % 180, (130 + index * 7) % 180))
        draw = ImageDraw.Draw(image)
        initials = f'{first_name[0]}{last_name[0]}'
        draw.ellipse((100, 70, 380, 350), fill='#f1c6a8')
        draw.text((195, 185), initials, fill='#18313b')
        draw.rectangle((80, 350, 400, 480), fill='#126b68')
        output = BytesIO()
        image.save(output, format='JPEG', quality=88)
        return output.getvalue()