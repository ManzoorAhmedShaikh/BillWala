from langchain_core.tools import tool
from scraper.bill_scraper_bot import get_hesco_bill

@tool
def fetch_hesco_bill(consumer_id : str = "", reference_no : str = "") -> str:
    """The user provides either their 'Customer ID (appno)' or 'Reference No (refno)', based on that,
    the method will create a payload that will later use on for fetching the bill. Using that, it will 
    fetch the bill from the 'https://bill.pitc.com.pk/hescobill' website and get its content which will be
    used for analysis and answering user concerns."""

    bill_content = ""
    if consumer_id:
        params = {"appno": consumer_id}
    else:
        params = {"refno": reference_no}

    response = get_hesco_bill(params = params)
    if response.get("status") == 0:
        # The bill fetched properly.
        bill_content = response.get("data")
    
    elif response.get("status") == 1:
        """
        The bill is not able to fetched, either the provided ID 
        (Consumer or Reference No) is incorrect or server is down.
        """
        bill_content = "BILL NOT FOUND"
    
    elif response.get("status") == 2:
        """
        The bill is not able to fetched due to timeout of server, 
        Kindly try again in a while.
        """
        bill_content = "BILL NOT FETCHED DUE TO TIMEOUT, TRY AGAIN LATER"

    elif response.get("status") == 3:
        """
        The bill is not able to fetched due to some unexpected error, 
        Kindly try again in a while.
        """
        bill_content = "BILL NOT FETCHED DUE TO AN UNEXPECTED ERROR, TRY AGAIN LATER"
    
    return bill_content