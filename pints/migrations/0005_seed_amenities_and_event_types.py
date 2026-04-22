from django.db import migrations


AMENITIES = [
    ('Dog Friendly', 'dog-friendly', '🐶', 'Dogs welcome inside or in the garden.'),
    ('Beer Garden', 'beer-garden', '🌳', 'Outdoor seating area to drink in.'),
    ('Outdoor Seating', 'outdoor-seating', '🪑', 'Tables and chairs outside the front.'),
    ('Food Served', 'food-served', '🍽️', 'Kitchen serves food during opening hours.'),
    ('Sunday Roast', 'sunday-roast', '🍗', 'Traditional Sunday roast on the menu.'),
    ('Real Ale', 'real-ale', '🍺', 'Cask-conditioned real ale available.'),
    ('Craft Beer', 'craft-beer', '🍻', 'Good selection of craft beer.'),
    ('Cocktails', 'cocktails', '🍸', 'Full cocktail menu.'),
    ('Live Sports', 'live-sports', '📺', 'Shows live sports on TV.'),
    ('Pool Table', 'pool-table', '🎱', 'Pool or snooker table available.'),
    ('Darts', 'darts', '🎯', 'Darts board available.'),
    ('Board Games', 'board-games', '🎲', 'Board games to play while you drink.'),
    ('Open Fire', 'open-fire', '🔥', 'Open fire or log burner inside.'),
    ('Kid Friendly', 'kid-friendly', '👶', 'Welcomes families with children.'),
    ('Wheelchair Accessible', 'wheelchair-accessible', '♿', 'Step-free access and accessible toilet.'),
    ('Free WiFi', 'free-wifi', '📶', 'Free WiFi available for customers.'),
    ('Card Only', 'card-only', '💳', 'Does not accept cash.'),
    ('Late Opening', 'late-opening', '🌙', 'Open past midnight on at least some nights.'),
    ('Quiet', 'quiet', '🤫', 'Reliably quiet — good for conversation.'),
    ('Historic', 'historic', '🏛️', 'Heritage or historic pub.'),
]


EVENT_TYPES = [
    ('Pub Quiz', 'pub-quiz', '❓', 'General knowledge quiz.'),
    ('Live Music', 'live-music', '🎸', 'Live band or solo performer.'),
    ('Open Mic', 'open-mic', '🎤', 'Open microphone night for local talent.'),
    ('Karaoke', 'karaoke', '🎙️', 'Sing along to classics.'),
    ('Comedy Night', 'comedy-night', '🤣', 'Stand-up comedy.'),
    ('DJ Night', 'dj-night', '🎧', 'DJ playing a set.'),
    ('Bingo', 'bingo', '🎱', 'Bingo night.'),
    ('Live Sports', 'live-sports', '📺', 'Live sports screening.'),
    ('Board Games', 'board-games', '🎲', 'Board games meet-up.'),
    ('Meet the Brewer', 'meet-the-brewer', '🍺', 'Tap takeover or brewer Q&A.'),
    ('Poetry Reading', 'poetry-reading', '📖', 'Poetry or spoken word.'),
    ('Tasting', 'tasting', '🥃', 'Whisky, gin, or beer tasting.'),
]


def seed(apps, schema_editor):
    Amenity = apps.get_model('pints', 'Amenity')
    EventType = apps.get_model('pints', 'EventType')

    for name, slug, icon, desc in AMENITIES:
        Amenity.objects.update_or_create(
            slug=slug,
            defaults={'name': name, 'icon': icon, 'description': desc, 'is_approved': True},
        )

    for name, slug, icon, desc in EVENT_TYPES:
        EventType.objects.update_or_create(
            slug=slug,
            defaults={'name': name, 'icon': icon, 'description': desc, 'is_approved': True},
        )


def unseed(apps, schema_editor):
    Amenity = apps.get_model('pints', 'Amenity')
    EventType = apps.get_model('pints', 'EventType')
    Amenity.objects.filter(slug__in=[s for _, s, _, _ in AMENITIES]).delete()
    EventType.objects.filter(slug__in=[s for _, s, _, _ in EVENT_TYPES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('pints', '0004_alter_beer_id_alter_pintlog_id_alter_pub_id_amenity_and_more'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
