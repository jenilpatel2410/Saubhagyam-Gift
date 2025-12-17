import hashlib
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from management_app.models import Cart
from constants import PAYU_DATA
import requests
from management_app.translator import translate_text as t
from management_app.translator import get_lang_code

class GetOrderPaymentLinkAPI(APIView):
    def post(self, request):
        lang = get_lang_code(request)
        if not request.user.is_authenticated:
            return Response(
                {"status": False, "message": t("You're not authorized to perform this action!", lang)},
                status=status.HTTP_403_FORBIDDEN
            )
        cart_id = request.data.get("cart_id", "")
        # Check if cart has items
        if cart_id:
            cart_items = Cart.objects.filter(id=cart_id, user=request.user)
        else:
            cart_items = Cart.objects.filter(user=request.user)

        if not cart_items.exists():
            return Response(
                {"status": False, "message": t("Please add at least one product in cart for checkout", lang)},
                status=status.HTTP_204_NO_CONTENT
            )

        try:
            # PayU credentials
            merchant_key = PAYU_DATA.get("PAYU_KEY")
            salt = PAYU_DATA.get("PAYU_SALT")
            payu_url = PAYU_DATA.get("PAYU_REQUEST_URL")
            response_base_url = PAYU_DATA.get("PAYU_RESPONSE_BASE_URL")

            # Order details
            txnid = request.data.get("txnid")
            amount = str(request.data.get("amount"))  # Ensure string for hashing
            productinfo = request.data.get("productinfo")
            firstname = request.user.first_name or "Customer"
            lastname = request.user.last_name or ""
            email = request.user.email
            user_id = str(request.user.id)
            billing_address = request.data.get("billing_address", "")
            shipping_amount = str(request.data.get("shipping_amount", 0))
            tax_amount = str(request.data.get("tax_amount", 0))
            voucher_code = ""  # request.data.get("voucherCode", "")
            gift_message = cart_id  # request.data.get("giftMessage", "")

            # Phone (avoid extra DB hit if related model exists)
            profile = getattr(request.user, "profilemodel", None)
            phone_no = f"+{profile.mobile_no}" if profile and profile.mobile_no else ""

            # Hash Sequence as per PayU docs (udf1-udf10 must be in order)
            hash_sequence = (
                f"{merchant_key}|{txnid}|{amount}|{productinfo}|{firstname}|{email}|"
                f"{user_id}|{shipping_amount}|{tax_amount}|{voucher_code}|{gift_message}"
                "||||||"
                f"{salt}"
            )

            # Generate hash
            hash_value = hashlib.sha512(hash_sequence.encode("utf-8")).hexdigest()

            # Payload for PayU form POST
            payload = {
                "key": merchant_key,
                "txnid": txnid,
                "amount": amount,
                "productinfo": productinfo,
                "firstname": firstname,
                "lastname": lastname,
                "address1": billing_address,
                "address2": "",
                "zipcode": "",
                "email": email,
                "udf1": user_id,
                "udf2": shipping_amount,
                "udf3": tax_amount,
                "udf4": voucher_code,
                "udf5": gift_message,
                "phone": phone_no,
                "pg": "",
                "drop_category": "EMI,CASH,BNPL",
                "surl": f"{response_base_url}/place-online-orders/",
                "furl": f"{response_base_url}/place-online-orders/",
                "curl": f"{response_base_url}/place-online-orders/",
                "hash": hash_value,
            }

            response = requests.post(payu_url, data=payload)

            return Response({
                "status": True,
                "payment_url": response.url+"/paymentoptions",
                "txn_id": txnid
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(e)
            return Response(
                {"status": False, "message": t(str(e), lang)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
