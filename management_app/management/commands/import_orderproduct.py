
from django.core.management.base import BaseCommand
from management_app.models import OrderModel, OrderLinesModel, ProductModel, ContactModel
from user_app.models import UserModel, ProfileModel, RoleModel
import pandas as pd
from django.utils import timezone
import re
import random


# ---------------- HELPERS ------------------

def clean_product_name(name):
    """Remove trailing numbers like '96 7' from product names."""
    return re.sub(r'\s+\d+\s+\d+$', '', str(name).strip())

def generate_item_code(name):
    name = name.upper()
    m = re.match(r'^([A-Z]+)\s*(\d+)\s*(F\d+)?', name)
    if m:
        return ' '.join(x for x in m.groups() if x)
    # fallback: take first 8 alphanumeric chars
    fallback = re.sub(r'\W+', '', name)[:8]
    return fallback or f"ITEM{int(timezone.now().timestamp())}"


def is_number(x):
    try:
        float(str(x).replace(",", "").strip())
        return True
    except:
        return False
    
def safe_number(x, default=0):
    try:
        if x is None:
            return default
        x = str(x).strip()
        if x == "" or x.lower() == "nan":
            return default
        return float(x)
    except:
        return default

def parse_product_file(product_df):
    """
    Extract bill -> customer -> product lines from messy product Excel.
    Returns generator of dicts: {"bill":..., "customer":..., "products":[{item,qty,rate,total,disc}, ...]}
    """

    # normalize headers
    product_df = product_df.copy()
    product_df.columns = [str(c).strip() for c in product_df.columns]

    # --- UNIVERSAL BILL COLUMN DETECTION ---
    possible_names = ["billno", "bill no", "m-billno", "m-bill no", "bill_no", "billno.0", "mbillno", "mbill"]
    bill_col = None

    # candidate by header names
    for col in product_df.columns:
        if col.lower().strip() in possible_names:
            sample = product_df[col].astype(str).str.strip()
            if sample.str.contains(r"^S\d+", regex=True).any():
                bill_col = col
                break

    # fallback: any column that contains S#### values
    if not bill_col:
        for col in product_df.columns:
            sample = product_df[col].astype(str).str.strip()
            if sample.str.contains(r"^S\d+", regex=True).any():
                bill_col = col
                break

    if not bill_col:
        # last fallback: try common names even without S check
        for col in product_df.columns:
            if "bill" in col.lower():
                bill_col = col
                break

    if not bill_col:
        raise Exception("❌ Could not find Billno column in product file!")

    # --- AUTO-DETECT ITEM / QTY / RATE / TOTAL / DISC COLUMNS ---
    item_col = None
    qty_col = None
    rate_col = None
    total_col = None
    disc_col = None

    # find item/description column
    for col in product_df.columns:
        lc = col.lower()
        if "item" in lc or "description" in lc or "desc" in lc or "description of goods" in lc.replace(" ", ""):
            item_col = col
            break

    # qty/rate/total/discount candidates
    qty_candidates = ["qty", "quantity", "no of item", "no of items", "no. of item", "no.of.item"]
    rate_candidates = ["rate", "mrp", "price", "selling price"]
    total_candidates = ["total", "amount", "product_total", "bill amt", "bill_amt"]
    discount_candidates = ["disc", "discount", "discount amt", "discount_amt"]

    for col in product_df.columns:
        lc = col.lower().strip()
        if not qty_col and any(c == lc or c in lc for c in qty_candidates):
            qty_col = col
        if not rate_col and any(c == lc or c in lc for c in rate_candidates):
            rate_col = col
        if not total_col and any(c == lc or c in lc for c in total_candidates):
            total_col = col
        if not disc_col and any(c == lc or c in lc for c in discount_candidates):
            disc_col = col

    # fallback defaults (use literal names if present)
    qty_col = qty_col or next((c for c in product_df.columns if c.lower().strip() == "qty"), None) or "Qty"
    rate_col = rate_col or next((c for c in product_df.columns if c.lower().strip() == "rate"), None) or "Rate"
    total_col = total_col or next((c for c in product_df.columns if c.lower().strip() == "total"), None) or "Total"
    disc_col = disc_col or next((c for c in product_df.columns if c.lower().strip() in ["disc", "discount"]), None)

    # --- Clean and forward-fill bill numbers so product rows inherit the bill ----
    # convert to strings, strip, replace .0 and empty strings to NaN then ffill
    product_df[bill_col] = product_df[bill_col].astype(str).str.strip().str.replace(".0", "", regex=False)
    product_df[bill_col] = product_df[bill_col].replace({"": pd.NA, "nan": pd.NA, "NaN": pd.NA})
    product_df[bill_col] = product_df[bill_col].ffill().astype(str).str.strip()

    # ensure item_col exists
    if item_col is None:
        # choose a text-like column as fallback (first non-numeric column)
        for col in product_df.columns:
            sample = product_df[col].astype(str).str.strip().head(10)
            if sample.apply(lambda x: bool(re.search(r"[A-Za-z]", x))).any():
                item_col = col
                break
    if item_col is None:
        # as absolute fallback, pick the first column that's not bill_col
        item_col = next(c for c in product_df.columns if c != bill_col)

    def extract_bill(row):
        val1 = str(row.get(bill_col, "")).strip()
        val2 = str(row.get(item_col, "")).strip()

        # Bill appears in M-Billno column
        if re.match(r"^S\d+", val1):
            return val1

        # Bill appears in Item column
        if re.match(r"^S\d+", val2):
            return val2

        return None

    # Build a new bill column from ANY detected bill row
    product_df["real_bill"] = product_df.apply(extract_bill, axis=1)

    # Fill blank rows downward
    product_df["real_bill"] = product_df["real_bill"].ffill()

    grouped = product_df.groupby("real_bill")

    for bill_value, group in grouped:
        bill_value = str(bill_value).strip()

        if not bill_value.startswith("S"):
            continue

        # Convert group to list for ordered processing
        rows = list(group.iterrows())

        customer_name = ""
        products = []
        product_start_pos = None

        # -------- Detect customer row --------
        for pos, (idx, r) in enumerate(rows):
            item_val = str(r.get(item_col, "")).strip()

            qty_val = safe_number(r.get(qty_col))
            rate_val = safe_number(r.get(rate_col))
            total_val = safe_number(r.get(total_col))

            # Customer row = text + no qty/no rate/no total
            if item_val and qty_val == 0 and rate_val == 0 and total_val == 0:
                customer_name = item_val
                product_start_pos = pos + 1   # <-- FIXED
                break

        if product_start_pos is None:
            continue

        # -------- Collect product rows --------
        for pos in range(product_start_pos, len(rows)):
            _, r = rows[pos]

            item_value = str(r.get(item_col, "")).strip()
            if not item_value:
                continue

            qty_val = safe_number(r.get(qty_col))
            rate_val = safe_number(r.get(rate_col))
            total_val = safe_number(r.get(total_col))
            disc_val = safe_number(r.get(disc_col)) if disc_col else 0

            # Accept product even if some values are 0 
            products.append({
                "item": item_value,
                "qty": qty_val,
                "rate": rate_val,
                "total": total_val,
                "disc": disc_val
            })

        if products:
            yield {
                "bill": bill_value,
                "customer": customer_name,
                "products": products
            }


    
# ---------------- MAIN COMMAND ------------------

class Command(BaseCommand):
    help = "Import Orders and Product Lines correctly"

    def add_arguments(self, parser):
        parser.add_argument('--orders', type=str, required=True)
        parser.add_argument('--product', type=str, required=True)

    def handle(self, *args, **kwargs):

        orders_path = kwargs['orders']
        product_path = kwargs['product']

        # read files
        orders_df = pd.read_excel(orders_path)
        product_df = pd.read_excel(product_path)

        # normalize headers
        orders_df.columns = [str(c).strip() for c in orders_df.columns]
        product_df.columns = [str(c).strip() for c in product_df.columns]

        # --- CLEAN ORDERS: REMOVE BLANK OR INVALID BILL NUMBERS ---
        # Convert Bill No to string and clean
        if "Bill No" not in orders_df.columns and "BillNo" in orders_df.columns:
            orders_df.rename(columns={"BillNo": "Bill No"}, inplace=True)

        orders_df["Bill No"] = orders_df["Bill No"].astype(str).str.strip().str.replace(".0", "", regex=False)

        # Remove blank or NaN bill numbers
        orders_df = orders_df[
            (orders_df["Bill No"].notna()) &
            (orders_df["Bill No"].str.strip() != "") &
            (orders_df["Bill No"].str.lower() != "nan")
        ]

        # Keep only rows that start with S (your bill format)
        orders_df = orders_df[orders_df["Bill No"].str.startswith("S")].copy()
        orders_df["Bill No"] = orders_df["Bill No"].astype(str).str.strip()

        self.stdout.write(self.style.NOTICE(f"🧾 Found {len(orders_df)} orders."))

        # ---- PARSE PRODUCT FILE ----
        parsed_products = list(parse_product_file(product_df))
        product_map = {p["bill"]: p for p in parsed_products}

        # debug print keys (optional)
        # print("Parsed product bills:", list(product_map.keys()))

        # ---- LOOP ORDERS ----
        for _, order_row in orders_df.iterrows():

            bill_no = str(order_row.get("Bill No") or "").strip()
            self.stdout.write(self.style.SUCCESS("=====billno=====> {bill_no}"))

            if not bill_no:
                continue

            # ---- CUSTOMER HANDLING ----
            customer_name = str(order_row.get("Customer") or "").strip()

            customer_user = None
            customer_contact = None

            if customer_name:
                customer_contact = ContactModel.objects.filter(name__iexact=customer_name).first()

                if not customer_contact:
                    first_name, last_name = (customer_name.split()[0], " ".join(customer_name.split()[1:])) if " " in customer_name else (customer_name, "")

                    customer_user, _ = UserModel.objects.get_or_create(
                        email=f"{customer_name.replace(' ', '_').lower()}@example.com",
                        defaults={"first_name": first_name, "last_name": last_name, "is_active": True,
                                  "role": RoleModel.objects.get(type="Retailer")}
                    )
                    ProfileModel.objects.get_or_create(user=customer_user)
                    customer_contact = ContactModel.objects.create(
                        user=customer_user,
                        name=customer_name,
                        contact_role=ContactModel.ContactRoleChoices.customer,
                        contact_type="Individual",
                        is_active=True
                    )
                else:
                    customer_user = customer_contact.user

            # ---- CREATE / GET ORDER ----
            order, created = OrderModel.objects.get_or_create(
                order_number=bill_no,
                defaults={
                    "order_date": order_row.get("Date", timezone.now().date()),
                    "shipping_address": order_row.get("Area", ""),
                    "discount_amt": order_row.get("Discount", 0.0),
                    "product_total": order_row.get("Bill Amt", 0.0),
                    "final_total": order_row.get("Bill Amt", 0.0),
                    "main_price": order_row.get("Total", 0.0),
                    "customer": customer_user,
                    "order_status": order_row.get("Order Status", "delivered"),
                    "pay_type": "online" if str(order_row.get("Mode")).lower() == "credit" else "cod",
                    "sale_status": "Sales Order",
                    "created_at": timezone.now(),
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Created Order: {bill_no}"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️ Existing Order found: {bill_no}"))

            # ---- GET PRODUCT LINES FOR THIS BILL ----
            if bill_no not in product_map:
                self.stdout.write(self.style.WARNING(f"❌ No product lines found for Bill {bill_no}"))
                continue

            bill_data = product_map[bill_no]
            products = bill_data["products"]

            products_added = 0

            OrderLinesModel.objects.filter(order=order).delete()
            
            for p in products:
                # cleaned_name = clean_product_name(p["item"])
                
                cleaned_name = clean_product_name(p["item"]).strip()

                # ---- SKIP CUSTOMER NAME ----
                if cleaned_name.lower() == bill_data["customer"].lower():
                    continue

                # ---- SKIP BLANK / NAN PRODUCTS ----
                if cleaned_name.lower() == "nan" or cleaned_name.strip() == "":
                    continue
              
                qty_val = int(safe_number(p.get("qty", 0)))
                rate_val = float(safe_number(p.get("rate", 0)))
                total_val = float(safe_number(p.get("total", 0)))
                disc_val = float(safe_number(p.get("disc", 0)))


                # ---- PRINT LINE BEFORE SAVING ----
                self.stdout.write(
                    self.style.NOTICE(
                        f"📦 {cleaned_name} → Qty: {qty_val} | Rate: {rate_val} | Total: {total_val}"
                    )
                )

                product, _ = ProductModel.objects.get_or_create(
                    name=cleaned_name,
                    defaults={
                        "short_name": cleaned_name[:20],
                        "unit": "pcs",
                        "product_price": float(p.get("rate") or 0),
                        "retailer_price": float(p.get("rate") or 0),
                        "item_code": generate_item_code(cleaned_name),
                        "description": "",
                        "product_use_type": "Consumable",
                        "product_type": "Single Product",
                        "is_published": False,
                    }
                )
                product.company_id = 2 # Saubhagyam
                product.save()
            
                OrderLinesModel.objects.create(
                    order=order,
                    product=product,
                    quantity=qty_val,
                    selling_price=rate_val,
                    discount=disc_val,
                    product_total=total_val,
                )

                products_added += 1
                # self.stdout.write(self.style.NOTICE(f"📦 {cleaned_name} (Qty: {qty_val})"))
             
            
            self.stdout.write(self.style.SUCCESS(f"➡️ Added {products_added} product lines for Order {bill_no}"))

        self.stdout.write(self.style.SUCCESS("🎉 All orders and products imported successfully!"))
