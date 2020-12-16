""" By Oscar K. Sandoval (https://github.com/mtfalls/) """
#!/usr/bin/env python
import sys
import math
import random
import decimal
import time
from timeit import default_timer as timer
from datetime import datetime
import mechanize
from bs4 import BeautifulSoup
import tweepy
from current_vg import * # current VG particpants and round dates
# from secrets_feh import * #TODO: Change before VG to secrets
from secrets_poets import * #TODO: Change before VG to secrets


# main method (called every 30 minutes)
def check_gauntlet():
    # start timer
    start_time = timer()

    # set encoding to utf-8
    reload(sys)
    sys.setdefaultencoding('utf8')

    # Use mechanize to set the locale's select value to 'en-US'
    br = mechanize.Browser()
    #br.set_handle_robots(False)
    #br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    br.open(vg_url)

    # select locale form
    br.select_form(action="/voting_gauntlet/locale")
    control = br.form.find_control("locale")

    # iterate through locale select options until "en-US" appears, then set to true
    for item in control.items:
        if item.name == "en-US":
                item.selected = True

    # submit form
    br.submit()

    # Use BeautifulSoup to parse the response
    r = br.response().read()
    soup = BeautifulSoup(r, 'html.parser')
    #print(p.prettify());

    # find all p elements (which contain the current scores)
    p = soup.find_all("p")

    # Get Variables for Current Round
    time_now = datetime.now()
    print("time_now: " + str(time_now))
    round_1_start = datetime.strptime(round_1_start_raw, '%b %d %Y %I:%M%p')
    round_1_end = datetime.strptime(round_1_end_raw, '%b %d %Y %I:%M%p')
    round_2_start = datetime.strptime(round_2_start_raw, '%b %d %Y %I:%M%p')
    round_2_end = datetime.strptime(round_2_end_raw, '%b %d %Y %I:%M%p')
    round_3_start = datetime.strptime(round_3_start_raw, '%b %d %Y %I:%M%p')
    round_3_end = datetime.strptime(round_3_end_raw, '%b %d %Y %I:%M%p')

    # Check if test VG or real VG

    if not (vg_test):
        # round 1 variables
        if (round_1_start < time_now < round_1_end):
            print("Currently Round 1")
            round_start = round_1_start
            unit_dict = {round_1_unit_1: False, round_1_unit_2: False, round_1_unit_3: False, round_1_unit_4: False, round_1_unit_5: False, round_1_unit_6: False, round_1_unit_7: False, round_1_unit_8: False}
            round_name = 'Round 1'
        # round 2 variables
        elif (round_2_start < time_now < round_2_end):
            print("Currently Round 2")
            round_start = round_2_start
            unit_dict = {round_2_unit_1: False, round_2_unit_2: False, round_2_unit_3: False, round_2_unit_4: False}
            round_name = 'Round 2'
        # round 3 variables
        elif (round_3_start < time_now < round_3_end):
            print("Currently Round 3")
            round_start = round_3_start
            unit_dict = {round_3_unit_1: False, round_3_unit_2: False}
            round_name = 'Final Round'
        else:
            print("Current time in between rounds. Ending execution.")
            return (-1)
    else: 
        print("Testing VG")
        print("Currently Round 3")
        round_start = round_3_start
        unit_dict = {round_3_unit_1: False, round_3_unit_2: False}
        round_name = 'Final Round'

    # all round variables
    count = len(unit_dict)

    # get units' current score by interating through all p elements
    for (x, y) in pairwise_list(p):
        # 1) iterate through keys (unit names)
        # 2) if x contains the unit name and the dict's value is False,
        #    then y contains the unit's current round score
        # 3) save value in dictionary
        # 4) reduce value of count by 1
        x_text = x.get_text()
        # if "L" in x_text and "f" in x_text:
        #     print("Changing text to Lif")
        #     x_text = "Lif"
        # if "Black" in x_text and "Knight" in x_text:
        #     print("Changing text to BlackKnight")
        #     x_text = "BlackKnight"
        # if "Death" in x_text and "Knight" in x_text:
        #     print("Changing text to DeathKnight")
        #     x_text = "DeathKnight"
        #Test before VG if False
        if (vg_now):
            print("VG is NOW!!!")
            y_text = y.get_text()
        else:
            print("VG is NOT now!!!")
            y_text = format (random.randint(0, 10000), ',d')
        # Iterate through keys to update their values
        for key in unit_dict:
            # Check for Male Robin, then Female Robin
            # if (x_text == 'Robin') and (not unit_dict['MRobin']):
            #    print("Key: " + key + "| Value:" + y_text )
            #    unit_dict['MRobin'] = y_text
            #    count -= 1
            # elif (x_text == 'Robin') and (not unit_dict['FRobin']):
            #    print("Key: " + key + "| Value:" + y_text )
            #    unit_dict['FRobin'] = y_text
            #    count -= 1
            if (x_text == key) and (not unit_dict[key]):
                print("Key: " + key + "| Value:" + y_text )
                unit_dict[key] = y_text
                count -= 1
        # stop searching for scores if all units are accounted for (when count is 0)
        if not count:
            break

    # custom sort dictionary values into a list
    # TODO: change every VG
    keyorder = [round_1_unit_1, round_1_unit_2, round_1_unit_3, round_1_unit_4, round_1_unit_5, round_1_unit_6, round_1_unit_7, round_1_unit_8]
    unit_scores = sorted(unit_dict.items(), key=lambda i:keyorder.index(i[0]))
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print(unit_scores)

    # Twitter authentication
    auth = tweepy.OAuthHandler(C_KEY, C_SECRET)
    auth.set_access_token(A_TOKEN, A_TOKEN_SECRET)
    api = tweepy.API(auth)

    # calculate disadvantage multiplier based on hour of round
    # divmod is a little complex so,
    # 1) divide the total seconds from time_elapsed into hours (60*60)
    # 2) divmod return a list with the quotient as [0] and remainder as [1]
    time_elapsed =  time_now - round_start
    current_hour = divmod(time_elapsed.total_seconds(), 60*60)[0]
    hours_remain = 45 - current_hour
    print("hours_remain: " + str(hours_remain))
    multiplier = (current_hour * 0.2) + 3.2

    # pairwise compare units in battle to detect disadvantages
    for (a, b) in pairwise_compare(unit_scores):

        # obtain name of units battling
        a_name = a[0]
        b_name = b[0]

        # obtain integer from string literal
        a_score = int(a[1].replace(',', ''))
        b_score = int(b[1].replace(',', ''))

        # variables for checking if multiplier is up for either team
        disadvantage_a = float(truncate(float(a_score) / float(b_score),4))
        disadvantage_b = float(truncate(float(b_score) / float(a_score),4))
        print("disadvantage_a: %f | disadvantage_b: %f") % (disadvantage_a, disadvantage_b)
        # Tweet if multiplier is active for losing team (other team has 3% more flags)
        try:
            if (disadvantage_a > 1.01): # Team B is losing
                tweet_multiplier(b_name, multiplier, hours_remain, vg_hashtag, round_name, api)
            elif (disadvantage_b > 1.01): # Team A is losing
                tweet_multiplier(a_name, multiplier, hours_remain, vg_hashtag, round_name, api)
            else:
                hour_or_hours = one_hour_string(hours_remain)
                tweet_tie = "No multiplier for #Team%s vs. #Team%s (%s in %s\'s %s)" % (a_name, b_name, hour_or_hours, vg_hashtag, round_name)
                api.update_status(tweet_tie)
                print("#Team%s #Team%s are tied" % (a_name, b_name))
        except:
            # Print out timestamp in the event of failure
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print("Tweet failed at %s for #Team%s #Team%s" % (timestamp, a_name, b_name))

    # End of Log
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("End of successful check: %s" % timestamp)

    # close mechanize browser
    br.close()

    # return time elapsed
    end_time = timer()
    time_elapsed = int(math.floor(end_time - start_time))
    print(time_elapsed)
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    return (time_elapsed)

def one_hour_string(hours_remain):
    if (hours_remain > 1):
        return "%d+ hours remain" % hours_remain
    elif (hours_remain == 1):
        return "Less than one hour remains"

def unit_details(name):
    # Get unit quote
    ## Get unit quote url
    quote_url = "Assets/%s/%s_Quotes.txt" % (name, name)
    ## Parse text file line by line into list, then select random quote
    quotes = open(quote_url).read().splitlines()
    secure_random = random.SystemRandom()
    quote = secure_random.choice(quotes)

    # Get unit img_url
    img_url = "Assets/%s/%s_Preview.png" % (name, name)
    unit_details = [quote, img_url]
    print("QuoteURL: " + quote_url + "| ImageURL: " + img_url + " | pizza")
    return unit_details

def tweet_multiplier(name, multiplier, hours_remain, vg_hashtag, round_name, api):
    # Tweet with image
    #try:
    # Get unit details
    current_details = unit_details(name)
    quote = current_details[0]
    img_url = current_details[1]
    hour_or_hours = one_hour_string(hours_remain)
    message = '#Team%s is losing with a %.1fx multiplier up!\n"%s"\n(%s in %s\'s %s)' % (name, multiplier, quote, hour_or_hours, vg_hashtag, round_name)
    print(message)
    # Attach image to tweet
    print("here1")
    media_list = list()
    print("here2")
    response = api.media_upload(img_url)
    print("here3")
    media_list.append(response.media_id_string)
    print("here4")
    api.update_status(status=message, media_ids=media_list)

    # Plaintext tweet
    #except:
    #    message = '#Team%s is losing with a %.1fx multiplier up!\n(%s %s Hour %d)' % (name, multiplier, vg_hashtag, round_name, current_hour)
    #    api.update_status(message)

def pairwise_list(iterable):
    it = iter(iterable)
    a = next(it, None)
    for b in it:
        yield (a, b)
        a = b

def pairwise_compare(iterable):
    it = iter(iterable)
    for x in it:
        yield (x, next(it))

# copy-pasted from https://stackoverflow.com/a/783927
def truncate(f, n):
    '''Truncates/pads a float f to n decimal places without rounding'''
    s = '{}'.format(f)
    if 'e' in s or 'E' in s:
        return '{0:.{1}f}'.format(f, n)
    i, p, d = s.partition('.')
    return '.'.join([i, (d+'0'*n)[:n]])

# It's showtime
if __name__ == "__main__":
    #Check scores every hour
    voting = True;
    while voting:
        time_elapsed = check_gauntlet()
        if (time_elapsed == -1):
            voting = False
        else:
            time.sleep(60*60 - time_elapsed)