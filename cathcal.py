import requests
import datetime
import boto3
import os
import json


def format_url(url):
    d = datetime.datetime.today() - datetime.timedelta(hours=4)
    print('Current date and time: ', d)

    formatted_url = url.format(d.year, d.month, d.day)
    print("formatted Url ", formatted_url)

    return formatted_url


def retrieve_celebrations():
    calapi_response = requests.get(format_url("http://calapi.inadiutorium.cz/api/v0/en/calendars/general-en/{}/{}/{}"),
                                   timeout=1)
    calapi_response_json = calapi_response.json()
    print('calapi response ', json.dumps(calapi_response_json, indent=2))

    celebrations = calapi_response_json['celebrations']

    message = ''
    i = 1
    for c in celebrations:
        message = message + '[' + str(i) + '] '
        message = message + c.get('title') + ' (' + c.get('rank') + ', ' + c.get('colour') + ')\n'
        i += 1

    print('calapi message:', message)
    return message


def retrieve_readings():
    ewtn_response = requests.get(format_url("https://www.ewtn.com/se/readings/readingsservice.svc/day/{}-{}-{}/en"),
                                 timeout=1)
    ewtn_response_json = ewtn_response.json()
    print('ewtn response ', json.dumps(ewtn_response_json, indent=2))

    reading_groups = ewtn_response_json.get('ReadingGroups')
    response = ''
    for i in range(0, len(reading_groups)):
        group = reading_groups[i]
        name = (group['Name'] + ' readings ', 'Readings')[group['Name'] is None]
        note = '(' + group['Note'] + ')' if group['Note'] is not None else ''
        readings = group['Readings']
        verses = retrieve_individual_verses(readings)
        response = response + '\n' + name + note + verses + '\n'

    return response


def retrieve_individual_verses(readings):
    message = ''
    for i in range(0, len(readings)):
        text = readings[i]['Citations'][0]['Reference']
        message = message + "\n" + text
    return message


def retrieve_readings_verses_url():
    d = datetime.datetime.today() - datetime.timedelta(hours=4)
    date = d.strftime('%m%d%Y')
    today = date[:-4] + date[-2:]
    return "http://www.usccb.org/bible/readings/" + today + ".cfm"


def deliver_message(message):
    if 'SNS_ENABLED' in os.environ:
        if os.environ['SNS_ENABLED'] == 'TRUE':
            sns = boto3.client('sns')
            sns_response = sns.publish(
                TopicArn=os.environ['ARN_TOPIC'],
                Message=message
            )
            print(sns_response)
        else:
            print('SNS_ENABLED is false:\n' + message)
    else:
        print('Could not find SNS_ENABLED env var')


def lambda_handler(event, context):
    message = 'CathCal>\nToday\'s celebration(s):\n' + retrieve_celebrations()
    # message = message + retrieve_readings()
    message = message + "\n" + retrieve_readings_verses_url()

    print('final message:', message)

    deliver_message(message)

    return {
        'statusCode': 200,
        'body': ''
    }


def myconverter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()


# remove below for deployment
# def main():
#     lambda_handler(None, None)
#
#
# main()
