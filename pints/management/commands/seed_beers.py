from django.core.management.base import BaseCommand
from pints.models import Beer

# Curated list of common UK pub beers by category.
# image_url is blank by default — populated as users contribute.
BEERS = [
    # Lagers
    'Stella Artois', 'Heineken', 'Carling', 'Fosters', 'Carlsberg',
    'Peroni', 'Birra Moretti', 'Corona', 'San Miguel', 'Kronenbourg 1664',
    'Amstel', 'Budweiser', 'Cobra', 'Asahi', 'Estrella Damm',
    'Becks', 'Coors Light', 'Mahou', 'Tiger', 'Baltika',
    'Efes', 'Kingfisher', 'Nastro Azzurro', 'Sagres', 'Super Bock',
    'Brahma', 'Sol', 'Modelo Especial', 'Singha', 'Chang',

    # Ales & Bitters
    'London Pride', 'Doom Bar', 'Timothy Taylor Landlord',
    'Old Speckled Hen', 'Bombardier', 'Hobgoblin', 'Tribute',
    'Greene King IPA', 'Spitfire', 'Pedigree', 'Bass',
    "John Smith's", 'Boddingtons', 'Abbot Ale', 'Wells Bombardier',
    'Directors', 'Black Sheep Ale', 'Theakstons Best', 'Wychwood Hobgoblin',
    'Sharp\'s Atlantic', 'Brakspear Oxford Gold',

    # IPAs
    'Brewdog Punk IPA', 'Camden Pale Ale', 'Neck Oil',
    'Beavertown Gamma Ray', 'Meantime London Pale Ale',
    'Thornbridge Jaipur', 'Sierra Nevada Pale Ale',
    'BrewDog Hazy Jane', 'Magic Rock Cannonball',
    'Verdant Putty', 'Cloudwater DIPA',

    # Stouts & Porters
    'Guinness', "Murphy's Irish Stout", 'Beamish',
    'Guinness Extra Cold', 'London Porter', 'Beavertown Smog Rocket',
    'Fuller\'s London Porter', 'Tiny Rebel Cwtch',

    # Wheat Beers
    'Hoegaarden', 'Erdinger', 'Blue Moon', 'Paulaner',
    'Franziskaner', 'Weihenstephaner', 'Edelweiss',

    # Craft & Specialty
    'Camden Hells', 'Meantime Pale Ale', 'BrewDog Elvis Juice',
    'Vocation Heart & Soul', 'Ossett Yorkshire Blonde',
    'Ilkley Mary Jane', 'Northern Monk Eternal',
    'Five Points Pale', 'Kernel Table Beer',
    'Orbit Ipa', 'Siren Craft Undercurrent',

    # World
    'Leffe Blonde', 'Leffe Brown', 'Duvel', 'Chimay Blue',
    'Chimay Red', 'Orval', 'Kwak', 'La Chouffe',
]


class Command(BaseCommand):
    help = 'Seeds the database with common UK pub beers'

    def handle(self, *args, **options):
        created = 0
        skipped = 0

        for name in BEERS:
            name = name.strip()
            if Beer.objects.filter(name__iexact=name).exists():
                skipped += 1
            else:
                Beer.objects.create(name=name)
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done. {created} beers added, {skipped} already existed.'
        ))
