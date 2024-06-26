'''A script that creates a notification setup page for our dashboard.'''

from os import environ as ENV

from dotenv import load_dotenv
import streamlit as st
from boto3 import client

TAG_ARNS = {'Action': 'arn:aws:sns:eu-west-2:129033205317:c10-games-action-tag',
            'Adventure': 'arn:aws:sns:eu-west-2:129033205317:c10-games-adventure-tag',
            "Casual": 'arn:aws:sns:eu-west-2:129033205317:c10-games-casual-tag',
            "City Builder": 'arn:aws:sns:eu-west-2:129033205317:c10-games-city-builder-tag',
            "Fantasy": 'arn:aws:sns:eu-west-2:129033205317:c10-games-fantasy-tag',
            'Indie': 'arn:aws:sns:eu-west-2:129033205317:c10-games-indie-tag',
            "Puzzle": 'arn:aws:sns:eu-west-2:129033205317:c10-games-puzzle-tag',
            "RPG": 'arn:aws:sns:eu-west-2:129033205317:c10-games-rpg-tag',
            "Simulation": 'arn:aws:sns:eu-west-2:129033205317:c10-games-simulation-tag',
            "Sports": 'arn:aws:sns:eu-west-2:129033205317:c10-games-sports-tag',
            "Singleplayer": 'arn:aws:sns:eu-west-2:129033205317:c10-games-singleplayer-tag',
            "Multiplayer": 'arn:aws:sns:eu-west-2:129033205317:c10-games-multiplayer-tag'}


def verify_email(email_address: str, config):
    '''Checks if an email is already verified,
    if not it is verified.'''
    ses = client(
        "ses", aws_access_key_id=config["AWS_KEY"], aws_secret_access_key=config["AWS_SECRET"], region_name=config['AWS_REGION'])

    if email_address not in ses.list_identities(IdentityType='EmailAddress')["Identities"]:
        res = ses.verify_email_identity(EmailAddress=email_address)
        return res
    return None


def subscribe_to_topic(email_address: str, config, topic_name: str):
    '''Subscribes a given email to a given topic.'''
    sns = client(
        "sns", aws_access_key_id=config["AWS_KEY"], aws_secret_access_key=config["AWS_SECRET"], region_name=config['AWS_REGION'])

    result = sns.subscribe(
        TopicArn=TAG_ARNS[topic_name],
        Protocol='email',
        Endpoint=email_address,
        ReturnSubscriptionArn=True
    )
    return result


if __name__ == "__main__":
    st.set_page_config(page_title='GameScraper',
                       page_icon=":space_invader:", layout="wide")

    load_dotenv()

    tags = list(TAG_ARNS.keys())

    st.title("New Release Notifications")
    st.write("---")
    st.subheader(
        "_Get daily updates about new games released in your favourite genres!_")

    with st.form(key='my_form'):
        st.header('Select the topics you want to subscribe to:')

        selected = []
        for tag in tags:
            ticked = st.checkbox(tag)
            if ticked:
                selected.append(tag)
        email = st.text_input("Enter email here:")
        submit_button = st.form_submit_button(label='Submit')

        if submit_button:
            if email == '':
                st.write("No email provided!")
            else:
                try:
                    verify_email(email, ENV)
                    st.write("You have subscribed!")
                    st.write(f"You are now tracking: {', '.join(selected)}")
                    for topic in selected:
                        subscribe_to_topic(email, ENV, topic)
                except:
                    st.write("The email was invalid, try again!")

    with st.sidebar:
        st.title("Navigation Station :rocket:")
        st.write("---")
        st.page_link("Home.py")
        st.page_link("pages/Epic.py")
        st.page_link("pages/GOG.py")
        st.page_link("pages/Steam.py")
        st.page_link("pages/Search.py")
        st.write("---")
        st.page_link("pages/Daily_Notifications.py")
        st.page_link("pages/Weekly_Report.py")
        st.write("---")
