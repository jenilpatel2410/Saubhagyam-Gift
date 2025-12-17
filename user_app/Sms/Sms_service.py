import http.client
import json

class MSG91Service2:
    def __init__(self, authkey):
        self.authkey = authkey

    def send_message(self, template_id, mobiles, var1, var2, short_url=0, real_time_response=0):
        conn = http.client.HTTPSConnection("control.msg91.com")

        # Construct the payload
        payload = {
            "template_id": template_id,
            "short_url": str(short_url),
            "realTimeResponse": str(real_time_response),
            "recipients": [
                {
                    "mobiles": mobiles,
                    "var1": var1,
                    "var2": var2
                }
            ]
        }

        headers = {
            'authkey': self.authkey,
            'accept': "application/json",
            'content-type': "application/json"
        }

        # Convert payload to JSON string
        payload_str = json.dumps(payload)

        # Make the POST request to MSG91
        conn.request("POST", "/api/v5/flow", payload_str, headers)

        # Get the response
        res = conn.getresponse()
        data = res.read()

        return data.decode("utf-8")