import re
import rsaidnumber
import logging

from odoo import fields

_logger = logging.getLogger(__name__)


def validate_said(id_no: str) -> dict:
    """Validate South Africa Identitification No

    Args:
        id_no (str): The identity no to validate

    Returns:
        dict: a dictionary containing the identity data 
    """

    id_number = rsaidnumber.parse(id_no, False) #eg 8801235111088
    if not id_number.valid:
        return
    
    return dict(
        dob = fields.Datetime.to_string(id_number.date_of_birth),
        gender = id_number.gender.name.lower(),
        citizenship = id_number.citizenship.name
    )
 

def validate_email(email: str) -> bool:
    """Validate a given email to ensure it conforms to email standard

    Returns:
        bool: Returns Truthy or Falsy
    """
    email_re = re.compile(r"""
    ([a-zA-Z][\w\.-]*[a-zA-Z0-9]     # username part
    @                                # mandatory @ sign
    [a-zA-Z0-9][\w\.-]*              # domain must start with a letter
        \.
        [a-z]{2,3}                     # TLD
    )
    """, re.VERBOSE)

    if not email_re.match(email):
        return False
    return True


def format_to_odoo_date(date_str: str) -> str:
    """Formats date format mm/dd/yyyy eg.07/01/1988 to %Y-%m-%d
        OR  date format yyyy/mm/dd to  %Y-%m-%d
    Args:
        date (str): date string to be formated

    Returns:
        str: The formated date
    """
    if not date_str:
        return

    data = date_str.split('/')
    if len(data) > 2 and len(data[0]) ==2: #format mm/dd/yyyy
        try:
            mm, dd, yy = int(data[0]), int(data[1]), data[2]
            if mm > 12: #eg 21/04/2021" then reformat to 04/21/2021"
                dd, mm = mm, dd
            if mm > 12 or dd > 31 or len(yy) != 4:
                return
            return f"{yy}-{mm}-{dd}"
        except Exception:
            return

    if len(data) > 2 and len(data[0]) == 4: #format yyyy/mm/dd
        try:
            yy, mm, dd = int(data[0]), int(data[1]), data[2]
            if mm > 12: #eg 2021/21/04" then reformat to 2021/04/21"
                dd, mm = mm, dd
            if mm > 12 or dd > 31 or len(yy) != 4:
                return
            return f"{yy}-{mm}-{dd}"
        except Exception:
            return


def validate_name(name: str) -> bool:
    """Validate person name

    Args:
        mobile (str):name

    Returns:
        bool: True if valid else false
    """
    if re.match("^[A-Za-z]*$", name):
        return True
    return False


def validate_mobile(mobile:str) -> bool:
    """Validate SA Mobile number

    Args:
        mobile (str): phone no string

    Returns:
        bool: True if valid else false
    """
    if re.match("^((?:\+27|27)|0)(=72|82|73|83|74|84|79|61)(\d{7})$", mobile):
        return True
    return  False


def validate_phone(phone: str) -> bool:
    """Validate SA phone

    Args:
        mobile (str): phone no string

    Returns:
        bool: True if valid else false
    """
    if re.match("^((?:\+27|27)|0)(=11|12|10)(\d{7})$", phone):
        return True
    return False

def validate_passportno(passport: str) -> bool:
    """Validate SA passport no

    Args:
        mobile (str): passport no string

    Returns:
        bool: True if valid else false
    """
    if re.match("^(?!^0+$)[a-zA-Z0-9]{3,20}$", passport):
        return True
    return False