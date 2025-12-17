from django.core.management.base import BaseCommand
from management_app.models import OrderModel, OrderLinesModel, ProductModel,ContactModel
from user_app.models import UserModel,ProfileModel, RoleModel
import pandas as pd
from django.utils import timezone


class Command(BaseCommand):
    help = "Import Sales Orders and Order Lines from Excel files"

    def add_arguments(self, parser):
        parser.add_argument('--orders', type=str, required=True, help='Path to Sales Order Excel file')
        parser.add_argument('--orderlines', type=str, required=True, help='Path to Product Lines Excel file')

    def handle(self, *args, **kwargs):
        orders_path = kwargs['orders']
        orderlines_path = kwargs['orderlines']

        # Load Excel files
        orders_df = pd.read_excel(orders_path)
        orderlines_df = pd.read_excel(orderlines_path)

        self.stdout.write(self.style.NOTICE(f"🧾 Found {len(orders_df)} orders."))

        # Loop through each order in the first file
        for _, order_row in orders_df.iterrows():
            bill_no = str(order_row.get('Bill No ')).strip()

            if not bill_no or bill_no.lower() == 'nan':
                continue
            
            # --- Handle Customer ---
            customer_name = str(order_row.get('Customer') or '').strip()
            customer_email = f"{customer_name.replace(' ', '_').lower()}@example.com"
            customer_user = None
            customer_contact = None

            if customer_name:
                # Try to find contact first
                customer_contact = ContactModel.objects.filter(name__iexact=customer_name).first()
                
                name_parts = customer_name.split()
                first_name = name_parts[0] if len(name_parts) > 0 else ""
                last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

                if not customer_contact:
                    # Create a user for this customer
                    customer_user, _ = UserModel.objects.get_or_create(
                        email=customer_email,
                        defaults={
                            "first_name": first_name,
                            "last_name": last_name,
                            "is_active": True,
                            "role": RoleModel.objects.get(type="Retailer"),
                        },
                    )

                    # Create profile if missing
                    ProfileModel.objects.get_or_create(user=customer_user)

                    # Create the Contact record
                    customer_contact = ContactModel.objects.create(
                        user=customer_user,
                        name=customer_name,
                        contact_role=ContactModel.ContactRoleChoices.customer,
                        contact_type="Individual",
                        is_active=True,
                    )

                    self.stdout.write(self.style.SUCCESS(f"🧍 Created new customer: {customer_name}"))
                else:
                    customer_user = customer_contact.user
            else:
                self.stdout.write(self.style.WARNING("⚠️ No customer name found in row"))
                
            mode = str(order_row.get('Mode')).strip().lower() if order_row.get('Mode') else ''

            # Map Excel values to your model choices
            if mode == 'credit':
                pay_type = 'online'
            elif mode == 'cash':
                pay_type = 'cod'
            else:
                pay_type = 'cod'

            # --- Create or Update OrderModel ---
            order, created = OrderModel.objects.get_or_create(
                order_number=bill_no,
                defaults={
                    'order_date': order_row.get('Date', timezone.now().date()),
                    'shipping_address': order_row.get('Area', ''),
                    'discount_amt': order_row.get('Discount', 0.0),
                    'product_total': order_row.get('Bill Amt', 0.0),
                    'final_total': order_row.get('Bill Amt', 0.0),
                    'main_price': order_row.get('Total', 0.0),
                    'customer': customer_user,
                    'order_status': order_row.get('Order Status', 'delivered'),
                    'pay_type': pay_type,
                    'sale_status': 'Sales Order',
                    'created_at': timezone.now(),
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Created Order: {bill_no}"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️ Updated existing Order: {bill_no}"))

            # --- Find product lines for this order ---
            matching_lines = orderlines_df[orderlines_df['Bill No.'].astype(str).str.strip() == bill_no]

            # Keep track of unique product IDs to avoid duplicates
            added_products = set()

            for _, line in matching_lines.iterrows():
                product = None
                product_id = line.get('Product ID')
                product_name = str(line.get('ProductHeader') or '').strip()

                # If a product ID exists, try that first
                if product_id and not pd.isna(product_id):
                    product = ProductModel.objects.filter(id=int(product_id)).first()

                # If not found, try by name
                if not product and product_name:
                    product = ProductModel.objects.filter(name__iexact=product_name).first()

                # --- Auto-create product if missing ---
                if not product and product_name:
                    prefix = "SGS"

                    # Maintain in-memory counters for prefixes
                    if not hasattr(self, '_product_counters'):
                        self._product_counters = {}
                    counters = self._product_counters

                    if prefix not in counters:
                        counters[prefix] = 1

                    item_code = f"{prefix}{str(counters[prefix]).zfill(3)}"
                    counters[prefix] += 1

                    product_price = float(line.get('Rate') or 0.0)
                    discounted_price = float(line.get(' ') or 0.0)  # assuming same if not provided

                    product, _ = ProductModel.objects.get_or_create(
                        name=product_name,
                        defaults={
                            "short_name": "",
                            "unit": "pcs",
                            "product_price": product_price,
                            "retailer_price": discounted_price,
                            "item_code": item_code,
                            "description": "",
                            "product_use_type": "Consumable",
                            "product_type": "Single Product",
                            "is_published": False,
                        }
                    )

                    self.stdout.write(self.style.SUCCESS(f"🆕 Created new product: {product_name} ({item_code})"))

                elif not product:
                    self.stdout.write(self.style.ERROR(f"🚫 Product not found or created: {product_name}, skipping."))
                    continue

                OrderLinesModel.objects.create(
                    order=order,
                    product=product,
                    quantity=line.get('Qnty.', 0.0),
                    selling_price=line.get('Rate', 0.0),
                    product_total=line.get('Gross Amt.', 0.0),
                )

            self.stdout.write(self.style.SUCCESS(f"➡️ Added {len(matching_lines)} product lines for Order {bill_no}"))

        self.stdout.write(self.style.SUCCESS("🎉 Import complete!"))
