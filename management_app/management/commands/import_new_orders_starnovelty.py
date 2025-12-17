from django.core.management.base import BaseCommand
from management_app.models import OrderModel, OrderLinesModel, ProductModel, ContactModel
from user_app.models import UserModel, ProfileModel, RoleModel
import pandas as pd
from django.utils import timezone
import re
import random

def generate_item_code(name):
    name = name.upper()
    m = re.match(r'^([A-Z]+)\s*(\d+)\s*(F\d+)?', name)
    if m:
        return ' '.join(x for x in m.groups() if x)
    # fallback: take first 8 alphanumeric chars
    fallback = re.sub(r'\W+', '', name)[:8]
    return fallback or f"ITEM{int(timezone.now().timestamp())}"

def clean_product_name(name):
    # Remove last two integer groups (e.g., "24 7")
    return re.sub(r'\s+\d+\s+\d+$', '', name.strip())

 
 
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
        orderlines_df = pd.read_excel(orderlines_path, header=None)
 
        # Normalize headers (strip spaces)
        orders_df.columns = [c.strip() for c in orders_df.columns]
 
        self.stdout.write(self.style.NOTICE(f"🧾 Found {len(orders_df)} orders."))
 
        # Loop through each order
        for _, order_row in orders_df.iterrows():
            bill_no = str(order_row.get('Bill No', '')).strip()
            if not bill_no or bill_no.lower() == 'nan':
                continue
 
            # --- Handle Customer ---
            customer_name = str(order_row.get('Customer', '')).strip()
            if not customer_name:
                # Generate a generic customer if missing
                customer_name = f"Unknown Customer {bill_no}"
 
            customer_contact = ContactModel.objects.filter(name__iexact=customer_name).first()
            if not customer_contact:
                customer_email = f"{customer_name.replace(' ', '_').lower()}@example.com"
                name_parts = customer_name.split()
                first_name = name_parts[0]
                last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
 
                # Create user
                customer_user, _ = UserModel.objects.get_or_create(
                    email=customer_email,
                    defaults={
                        "first_name": first_name,
                        "last_name": last_name,
                        "is_active": True,
                        "role": RoleModel.objects.get(type="Wholesaler"),
                    }
                )
                ProfileModel.objects.get_or_create(user=customer_user)
 
                # Create contact
                customer_contact = ContactModel.objects.create(
                    user=customer_user,
                    name=customer_name,
                    contact_role=ContactModel.ContactRoleChoices.customer,
                    contact_type="Individual",
                    is_active=True
                )
            else:
                customer_user = customer_contact.user

            # --- Create or update Order ---
            mode = str(order_row.get('Mode', '')).strip().lower()
            pay_type = 'cod' if mode == 'cash' else 'online'

            order, _ = OrderModel.objects.get_or_create(
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

            if OrderLinesModel.objects.filter(order=order).exists():
                self.stdout.write(self.style.NOTICE(f"ℹ️ Order {bill_no} already has lines, skipping line import."))
                
            
            OrderLinesModel.objects.filter(order=order).delete()
            
            # --- Parse products for this bill ---
            products = []
            found_bill = False
            start_products = False

            for _, row in orderlines_df.iterrows():
                vals = [str(v).strip() if pd.notna(v) else '' for v in row.values]
                vals_normalized = [v.upper() for v in vals]


                if bill_no.upper() in vals_normalized:
                    found_bill = True
                    continue
                if not found_bill:
                    continue
                
                if all(v == "" for v in vals):
                    if start_products:
                        start_products =False
                        found_bill = False
                        continue
                    
                first = vals[0].lower()
                if not start_products:
                    if first in ["date", "customer", "add", "po no", "dp name", "transport", "chno", "ch no"]:
                        continue
                    try:
                        float(vals[3])
                        start_products = True
                    except:
                        continue
                    
                if len(vals) < 7:
                    continue

                description = vals[1]
                qty = vals[3]
                unit = vals[4]
                rate = vals[5]
                total = vals[6]

                try:
                    qty_f = float(qty)
                    rate_f = float(rate)
                    total_f = float(total)
                except:
                    continue
                if description == "" or any(description.lower().startswith(x) for x in ["cgst", "sgst", "igst", "round", "total"]):
                    continue

                products.append({
                    "name": description,
                    "qty": qty_f,
                    "unit": unit or "PCS",
                    "rate": rate_f,
                    "total": total_f
                })

            # --- Save products ---
            for p in products:
                self.stdout.write(self.style.NOTICE(f"ℹ️ Saving product: {p['name']}"))
                product, _ = ProductModel.objects.get_or_create(
                    name=clean_product_name(p["name"]),
                    defaults={
                        "short_name": p["name"][:20],
                        "unit": "pcs",
                        "product_price": p["rate"],
                        "retailer_price": p["rate"],
                        "item_code": generate_item_code(p["name"]),
                        "description": "",
                        "product_use_type": "Consumable",
                        "product_type": "Single Product",
                        "is_published": False,
                        "short_description": str(random.randint(1, 50)),
                    }
                )
                product.company_id = 3
                product.save()

                OrderLinesModel.objects.create(
                    order=order,
                    product=product,
                    quantity=p["qty"],
                    selling_price=p["rate"],
                    product_total=p["total"],
                )

            self.stdout.write(self.style.SUCCESS(f"✔ Saved {len(products)} products for Bill {bill_no}"))

        self.stdout.write(self.style.SUCCESS("🎉 Import complete!"))