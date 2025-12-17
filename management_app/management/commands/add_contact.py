import pandas as pd
from django.core.management.base import BaseCommand
from management_app.models import ContactModel
from user_app.models import CountryModel, UserModel, ProfileModel, AddressModel,RoleModel

class Command(BaseCommand):
    help = "Import customers and addresses from Excel into UserModel, ProfileModel, ContactModel, and AddressModel"

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Path to the Excel file containing customer data'
        )

    def handle(self, *args, **options):
        file_path = options['file']

        try:
            df = pd.read_excel(file_path)
            df = df.fillna('')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading Excel file: {e}"))
            return

        users_created = 0
        profiles_created = 0
        contacts_created = 0
        addresses_added = 0

        for index, row in df.iterrows():
            # ----- Extract User fields -----
            name = row.get('Name') if pd.notna(row.get('Name')) else ''
            email = row.get('Email') if pd.notna(row.get('Email')) else None
            phone_no = row.get('Mobile') if pd.notna(row.get('Mobile')) else None
            firm_name = row.get('Contact') if pd.notna(row.get('Contact')) else ''

            if phone_no:
                # Remove .0 if Excel stored it as float
                if isinstance(phone_no, float):
                    phone_no = str(int(phone_no))
                else:
                    phone_no = str(phone_no).strip()

                if not phone_no.startswith('+'):
                    phone_no = '+91' + phone_no       
                    # Skip row if email is missing
            if not email:
                email = f"{name.split()[0] if name else 'test'}@dummyemail.com"
            role = RoleModel.objects.filter(type='Retailer').first()
            # ----- Create or update UserModel -----
            user, created = UserModel.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': name.split()[0] if name else '',
                    'last_name': ' '.join(name.split()[1:]) if name and len(name.split()) > 1 else '',
                    'mobile_no': phone_no,
                    'firm_name': firm_name,
                    'is_active': True,
                    'role': role
                }
            )
            if created:
                users_created += 1
            else:
                # Update existing user safely
                user.first_name = name.split()[0] if name else user.first_name
                user.last_name = ' '.join(name.split()[1:]) if name and len(name.split()) > 1 else user.last_name
                if phone_no:
                    user.mobile_no = phone_no
                user.save()

            # ----- Create or get ProfileModel -----
            profile, _ = ProfileModel.objects.get_or_create(user=user)
            if phone_no:
                existing_profile = ProfileModel.objects.filter(mobile_no=phone_no).exclude(user=user).first()
                if not existing_profile:
                    profile.mobile_no = phone_no
            try:
                profile.save()
                profiles_created += 1
            except:
                self.stdout.write(self.style.WARNING(
                    f"⚠️ Skipping profile mobile_no for user {user.email} due to uniqueness conflict."
                ))

            # ----- ContactModel -----
            contact_role = row.get('contact_role') if pd.notna(row.get('contact_role')) else 'Customer'
            contact_type = row.get('contact_type') if pd.notna(row.get('contact_type')) else 'Individual'
            gstin = row.get('GSTIN No') if pd.notna(row.get('GSTIN No')) else None

            contact, _ = ContactModel.objects.update_or_create(
                user=user,
                defaults={
                    'name': name,
                    'email': email,
                    'phone_no': phone_no,
                    'contact_role': contact_role,
                    'contact_type': contact_type,
                    'gstin': gstin,
                    'is_active': True
                }
            )
            contacts_created += 1

            # ----- Merge addresses -----
            address_parts = []
            for i in range(1, 4):
                add_part = row.get(f'Add{i}')
                if pd.notna(add_part) and str(add_part).strip():
                    address_parts.append(str(add_part).strip())

            if address_parts:
                merged_address = " | ".join(address_parts)
                area = row.get('Area') if pd.notna(row.get('Area')) else ''
                city_field = row.get('City/Distinct') if pd.notna(row.get('City/Distinct')) else ''
                state_field = row.get('States') if pd.notna(row.get('States')) else ''
                pincode_field = row.get('pincode') if pd.notna(row.get('pincode')) else ''

                # Try to find existing address first
                addr = AddressModel.objects.filter(
                    full_name=name,
                    address=merged_address,
                    city=city_field,
                    state=state_field,
                    street=area,
                    postal_code=pincode_field
                ).first()

                if not addr:
                    # Create new if not found
                    addr = AddressModel.objects.create(
                        full_name=name,
                        address=merged_address,
                        city=city_field,
                        state=state_field,
                        street=area,
                        fcity=None,
                        fstate=None,
                        postal_code=pincode_field,
                        mobile=phone_no,
                        is_default=True
                    )
                    print(f"✅ Address created for user {user.email}")
                else:
                    print(f"♻️ Existing address assigned for user {user.email}")

                # Link to user and profile
                user.address.add(addr)
                profile.addresses.add(addr)
                contact.many_address.add(addr)
                addresses_added += 1
                if created:
                    print(f"✅ Address created and assigned for user {user.email}")
                else:
                    print(f"♻️ Existing address assigned for user {user.email}")

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Import complete! Users Created: {users_created}, Profiles Created: {profiles_created}, "
                f"Contacts Created/Updated: {contacts_created}, Addresses Added: {addresses_added}"
            )
        )
