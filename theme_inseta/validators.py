#from snoop import snoop
import datetime
import re
import os

####
# ID CHECKER
####


validations = {
    "gender": {
        0: "female",
        1: "female",
        2: "female",
        3: "female",
        4: "female",
        5: "male",
        6: "male",
        7: "male",
        8: "male",
        9: "male",

    },
    "citizenship": {
        0: "sa",
        1: "other",
    },
    "length": 13,
}

#@snoop
def check_control_bit(id_num):
    evens = []
    odds = []
    id_num = str(id_num)
    # get all digits in the odd positions except the last one
    for x in range(0, len(id_num)):
        if (x + 1) % 2 == 0:
            evens.append(id_num[x])
        # odds.append(id_num[x])
        else:
            odds.append(id_num[x])
    # evens.append(id_num[x])
    #
    odds = odds[0:-1]
    sum_odds = sum([int(o) for o in odds])
    even_num = ''
    for x in evens:
        even_num += str(x)
    # move the evens into a field and multiply by 2
    even_multiplied = int(even_num) * 2
    even_guy = sum(int(x) for x in str(even_multiplied))
    evens_and_odds = int(even_guy) + int(sum_odds)  # 22 + 20 vs 13 + 20?
    control = 10 - int(str(evens_and_odds)[1])
    # control = 10 - int(str(evens_and_odds)[0]) + 1
    last_digit = int(id_num[12])
    if control == last_digit:
        return "Passable"
    else:
        return "Invalid control bit"


def check_gender(id_num):
    try:
        return validations["gender"][int(id_num[6])]
    except:
        return "Invalid gender"

def check_citizenship(id_num):
    try:
        return validations["citizenship"][int(id_num[10])]
    except:
        return "Invalid citizenship status"

def check_date(id_num):
    id_num=str(id_num)
    if int(id_num[0:2]) < 20:
        prefix="20"
    else:
        prefix="19"
    date_string =  prefix+id_num[0:2]+"-"+id_num[2:4]+"-"+id_num[4:6]
    try:
        real_date = datetime.datetime.strptime(date_string, "%Y-%M-%d")
        return real_date
    except:
        return "Invalid birth date"

def check_length(id_num):
    if len(id_num) != validations["length"]:
        return "Invalid ID length"
    else:
        return True


def old_said_check(id_num):
    return_messages = []
    return_messages.append(check_citizenship(id_num))
    return_messages.append(check_date(id_num))
    return_messages.append(check_gender(id_num))
    # return_messages.append(check_control_bit(id_num))
    return return_messages

def said_check(id_num):
    cmd = "python3 /bin/saidcheck.py "+id_num
    x = os.popen(cmd).read()
    # exec("dct="+str(x))
    exec("dct="+str(x))
    # return_messages = []
    # return_messages.append(dct['citizenship'])
    # return_messages.append(dct['day']+dct['month']+dct['year'])
    # return_messages.append(dct['gender'])
    # return_messages.append(dct['Valid'])
    # return return_messages
    return dct


####
# NAME CHECKERS
####

def name_checker(name):
    if re.match("^[A-Za-z]*$", name):
        return "Passable"
    else:
        return "Invalid first/last name"

####
# EMAIL CHECKER
####

def email_checker(email):
    if not re.match("[^@]+@[^@]+\.[^@]+", email):
        return "Invalid email"
    else:
        return "Passable"

####
# mobile num CHECKER
####

def mobile_num_checker(contact_num):
    if not re.match("^((?:\+27|27)|0)(=72|82|73|83|74|84|79|61)(\d{7})$", contact_num):
        return "Invalid Mobile Number"
    else:
        return "Passable"

####
# phone num CHECKER
####

def phone_num_checker(contact_num):
    if not re.match("^((?:\+27|27)|0)(=11|12|10)(\d{7})$", contact_num):
        return "Invalid Phone Number"
    else:
        return "Passable"

##
#PASSPORT NUMBER
##

def check_passport_number(passport):
    if re.match("^(?!^0+$)[a-zA-Z0-9]{3,20}$", passport):
        return "Passable"
    else:
        return "Invalid passport"

passport_check = check_passport_number
