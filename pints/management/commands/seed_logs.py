"""
seed_logs — populate PintLog with randomised seeded data.

Usage:
    python manage.py seed_logs                 # 200 logs across 10 fake users
    python manage.py seed_logs --logs 500 --users 20
    python manage.py seed_logs --clear         # delete all seeded logs (and seed users)

All seeded rows have is_seeded=True so they can be filtered / deleted cleanly.
Seeded users are given usernames like seed_user_01 and are flagged is_active=False
so they cannot log in.
"""
import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from pints.models import Beer, PintLog, Pub

SEED_USER_PREFIX = 'seed_user_'

NOTES_POOL = [
    'Really smooth, would order again.',
    'Slightly warm but still good.',
    'Surprisingly cheap for the area.',
    'A bit flat but decent.',
    'Great atmosphere, nice pint.',
    'Overpriced for what it was.',
    'Perfect after a long week.',
    'On the expensive side but fresh.',
    '',  # no notes — blank intentionally common
    '',
    '',
]


class Command(BaseCommand):
    help = 'Seed random PintLog entries for demo purposes'

    def add_arguments(self, parser):
        parser.add_argument('--logs',  type=int, default=200, help='Number of logs to create (default 200)')
        parser.add_argument('--users', type=int, default=10,  help='Number of seed users to use (default 10)')
        parser.add_argument('--clear', action='store_true',   help='Delete all seeded logs and seed users then exit')

    def handle(self, *args, **options):
        if options['clear']:
            deleted_logs, _ = PintLog.objects.filter(is_seeded=True).delete()
            deleted_users, _ = User.objects.filter(username__startswith=SEED_USER_PREFIX).delete()
            self.stdout.write(self.style.SUCCESS(
                f'Cleared {deleted_logs} seeded log(s) and {deleted_users} seed user(s).'
            ))
            return

        n_logs  = options['logs']
        n_users = options['users']

        # ── Ensure we have pubs and beers ──────────────────────────────────
        pubs  = list(Pub.objects.all())
        beers = list(Beer.objects.all())

        if not pubs:
            self.stdout.write(self.style.ERROR('No pubs in DB. Run seed_pubs first.'))
            return
        if not beers:
            self.stdout.write(self.style.ERROR('No beers in DB. Run seed_beers first.'))
            return

        # ── Get or create seed users ───────────────────────────────────────
        seed_users = []
        for i in range(1, n_users + 1):
            username = f'{SEED_USER_PREFIX}{i:02d}'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'is_active': False,      # cannot log in
                    'email': f'{username}@seed.local',
                },
            )
            if created:
                user.set_unusable_password()
                user.save()
            seed_users.append(user)

        self.stdout.write(f'Using {len(seed_users)} seed user(s).')

        # ── Build logs ─────────────────────────────────────────────────────
        # Prices: normally distributed around a realistic UK pint price
        # Range roughly £3.00–£7.50, tighter around each pub's "local" mean
        now = timezone.now()

        logs_to_create = []
        for _ in range(n_logs):
            pub   = random.choice(pubs)
            beer  = random.choice(beers)
            user  = random.choice(seed_users)

            # Price: pub gets a random baseline £3.80–£6.50, then ±50p noise
            pub_mean = 3.80 + (hash(pub.id) % 271) / 100   # deterministic per pub
            raw_price = pub_mean + random.gauss(0, 0.35)
            price = Decimal(str(max(2.50, min(8.50, round(raw_price, 2)))))

            serving_size = random.choices(
                ['pint', 'half', 'third'],
                weights=[70, 20, 10],
            )[0]

            # Logged at a random point in the past 90 days
            logged_at = now - timedelta(
                days=random.randint(0, 90),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
            )

            logs_to_create.append(PintLog(
                user=user,
                pub=pub,
                beer=beer,
                price=price,
                serving_size=serving_size,
                notes=random.choice(NOTES_POOL),
                is_seeded=True,
                logged_at=logged_at,   # set below via update — auto_now_add blocks this
            ))

        # bulk_create then back-date logged_at (auto_now_add ignores passed value)
        created = PintLog.objects.bulk_create(logs_to_create)

        # Back-date: update each row individually using the value we stored
        # (bulk_create returns objects with PKs; we stored the target time on them)
        for obj, target in zip(created, logs_to_create):
            PintLog.objects.filter(pk=obj.pk).update(logged_at=target.logged_at)

        self.stdout.write(self.style.SUCCESS(
            f'Created {len(created)} seeded log(s) across '
            f'{len(pubs)} pub(s) and {len(beers)} beer(s).'
        ))
        self.stdout.write(
            f'To remove all seeded data: python manage.py seed_logs --clear'
        )
