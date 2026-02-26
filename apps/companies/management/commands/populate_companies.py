"""Populate database with sample data for testing."""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings

import random
from apps.companies.models import Company, CompanyClaim
from apps.users.models import User
from apps.reviews.models import Review, Tag, Comment


class Command(BaseCommand):
    help = 'Populate database with sample data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')

        # Create companies
        companies_data = [
            {'name': 'TechCorp Inc', 'country': 'US', 'city': 'San Francisco', 'industry': 'Technology'},
            {'name': 'Global Bank', 'country': 'GB', 'city': 'London', 'industry': 'Finance'},
            {'name': 'HealthPlus', 'country': 'CA', 'city': 'Toronto', 'industry': 'Healthcare'},
            {'name': 'ShopMart', 'country': 'US', 'city': 'New York', 'industry': 'Retail'},
            {'name': 'FoodChain Co', 'country': 'FR', 'city': 'Paris', 'industry': 'Food & Beverage'},
        ]

        companies = []
        for data in companies_data:
            company, created = Company.objects.get_or_create(
                name=data['name'],
                country=data['country'],
                defaults=data
            )
            companies.append(company)
            if created:
                self.stdout.write(f'  Created company: {company.name}')

        # Get or create test users
        user1, created = User.objects.get_or_create(
            phone='+1234567890',
            defaults={
                'full_name': 'John Doe',
                'email': 'john@example.com',
            }
        )
        if created:
            user1.set_password('testpass123')
            user1.save()
            self.stdout.write(f'  Created user: {user1.full_name}')

        user2, created = User.objects.get_or_create(
            phone='+1234567891',
            defaults={
                'full_name': 'Jane Smith',
                'email': 'jane@example.com',
            }
        )
        if created:
            user2.set_password('testpass123')
            user2.save()
            self.stdout.write(f'  Created user: {user2.full_name}')

        company_user, created = User.objects.get_or_create(
            phone='+1234567892',
            defaults={
                'full_name': 'TechCorp Representative',
                'email': 'rep@techcorp.com',
            }
        )
        if created:
            company_user.set_password('testpass123')
            company_user.save()
            self.stdout.write(f'  Created user: {company_user.full_name}')

        # Get or create tags
        tags = []
        for mood, name in [('positive', 'Great Service'), ('neutral', 'Average'), ('negative', 'Poor Experience')]:
            tag, _ = Tag.objects.get_or_create(
                name=name,
                defaults={'slug': name.lower().replace(' ', '-'), 'mood': mood}
            )
            tags.append(tag)

        # Create reviews
        review_titles = [
            'Great experience overall',
            'Could be better',
            'Terrible customer service',
            'Highly recommend!',
            'Not worth the money'
        ]

        review_count = 0
        for company in companies[:3]:
            for i in range(3):
                review = Review.objects.create(
                    user=random.choice([user1, user2]),
                    company=company,
                    title=review_titles[i % len(review_titles)],
                    body=f'This is a sample review for {company.name}. The service was {random.choice(["excellent", "good", "fair", "poor"])} and I would {random.choice(["definitely", "probably", "never"])} recommend it to others.',
                    rating=random.randint(1, 5),
                    status='approved',
                    is_hidden=False
                )
                review.tags.set(random.sample(tags, random.randint(1, 2)))
                review_count += 1

        self.stdout.write(f'  Created {review_count} reviews')

        # Create a pending claim request
        claim, created = CompanyClaim.objects.get_or_create(
            user=company_user,
            company=companies[0],
            defaults={
                'status': CompanyClaim.Status.PENDING,
                'verification_method': CompanyClaim.VerificationMethod.EMAIL,
                'verification_email': 'rep@techcorp.com',
                'requester_name': 'TechCorp Representative',
                'requester_role': 'Marketing Director',
                'requester_notes': 'I am authorized to represent TechCorp Inc.'
            }
        )
        if created:
            self.stdout.write(f'  Created pending claim for {companies[0].name}')

        # Create an already approved claim (link a company to a user)
        approved_company = companies[1]
        if not approved_company.claimed_by:
            # Create claim first
            approved_claim, _ = CompanyClaim.objects.get_or_create(
                user=user2,
                company=approved_company,
                defaults={
                    'status': CompanyClaim.Status.APPROVED,
                    'verification_method': CompanyClaim.VerificationMethod.EMAIL,
                    'verification_email': 'jane@globalbank.com',
                    'reviewed_by': None,  # Would be admin
                    'reviewed_at': timezone.now()
                }
            )
            # Manually approve
            approved_company.is_verified = True
            approved_company.verified_at = timezone.now()
            approved_company.claimed_by = user2
            approved_company.save()
            self.stdout.write(f'  Approved claim for {approved_company.name} (claimed by {user2.full_name})')

        # Create a company response comment
        if Review.objects.exists():
            review = Review.objects.first()
            Comment.objects.create(
                user=user2,
                review=review,
                message='Thank you for your feedback. We are working to improve our service.',
                is_company_response=True
            )
            self.stdout.write('  Created sample company response')

        self.stdout.write(self.style.SUCCESS('\nSample data created successfully!'))
        self.stdout.write('\nTest accounts:')
        self.stdout.write('  User: +1234567890 / testpass123 (regular user)')
        self.stdout.write('  User: +1234567891 / testpass123 (company rep - approved)')
        self.stdout.write('  User: +1234567892 / testpass123 (pending claim)')
        self.stdout.write('\nURLs to test:')
        self.stdout.write('  /companies/claim/ - Submit claim')
        self.stdout.write('  /companies/register/ - Register new company')
        self.stdout.write('  /companies/dashboard/ - Company dashboard')
        self.stdout.write('  /companies/admin/claims/ - Admin claim list')
