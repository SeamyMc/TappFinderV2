# TappFinder

Crowd-sourced beer price tracker. Log what you're drinking, where, and what you paid — see it all on a map.

## Getting started

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Configure settings**
```bash
cp tappfinder/settings.py.example tappfinder/settings.py
```
Open `tappfinder/settings.py` and replace the `SECRET_KEY` value with a freshly generated one:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**3. Run migrations**
```bash
python manage.py migrate
```

**4. Seed initial data**
```bash
# Common UK pub beers
python manage.py seed_beers

# Pubs from OpenStreetMap (change city as needed)
python manage.py seed_pubs --city london
```

Other supported cities: `manchester`, `birmingham`, `leeds`, `liverpool`, `edinburgh`, `glasgow`, `bristol`, `sheffield`, `newcastle`, `cardiff`, `nottingham`

For anywhere else, supply a bounding box:
```bash
python manage.py seed_pubs --bbox "53.37,-2.28,53.42,-2.18"
```

**5. Start the dev server**
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` and create an account to get started.
