import html2text
from curl_cffi import requests as cffi_requests
from .status_codes import *

def get_hesco_bill(params : dict):
    session = cffi_requests.Session(impersonate="chrome")
    try:
	print(f"Checking bill for: {params}")
        session.get("https://bill.pitc.com.pk/hescobill/general", timeout=25)
        response = session.post(
            "https://bill.pitc.com.pk/hescobill/general",
            params=params,
            timeout=60
        )
        if response.status_code != 200 or response.text.lower().find("bill not found") != -1:
            print(f"Failed to fetch bill, kindly check the number again or try later")
            return {"status": BILL_NOT_FOUND}

        converter = html2text.HTML2Text()
        converter.ignore_links = True
        converter.ignore_images = True
        converter.ignore_tables = False
        converter.body_width = 0

        markdown = converter.handle(response.text)
        start = markdown.find("CONSUMER DETAIL")
        end = markdown.find("BILL HISTORY")
        if start != -1 and end != -1:
            markdown = markdown[start:end + 1000]

        return {"data": markdown.strip(), "status": SUCCESSFUL}

    except TimeoutError as e:
        print(f"Error fetching bill due to timeout: {TIMEOUT}")
        return {"status": TIMEOUT}

    except Exception as e:
        print(f"Error fetching bill: {UNEXPECTED_ISSUE}")
        return {"status": UNEXPECTED_ISSUE}
