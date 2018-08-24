import os
import time
import re
import random

from slackclient import SlackClient

CLIENT_KEY = os.environ.get("SLACK_BAKER_TOKEN")
BOT_ID = os.environ.get("BAKER_BOT_ID")
STEVE_ID = 'U1UN7J3E2'
AT_BOT = '<@{}>'.format(BOT_ID)
slack_client = SlackClient(CLIENT_KEY)


def choose_baker(channel, user):
    # choose a baker from the list
    channel_data = slack_client.api_call(
      "channels.info",
      channel=channel,
    )

    bakers = channel_data['channel']['members']
    bakers.remove(BOT_ID)

    # allow steve to be chosen 5% of the time
    steve_in = random.randrange(100) < 5
    if not steve_in:
        bakers.remove(STEVE_ID)

    baker = random.choice(bakers)
    slack_client.api_call(
        'chat.postMessage',
        channel=channel,
        text='<!here>, This weeks Star Baker is.......'.format(user),
        as_user=True
    )

    # Pause for dramatic effect...
    time.sleep(random.randrange(2, 6))

    slack_client.api_call(
        'chat.postMessage',
        channel=channel,
        text='<@{}>!!'.format(baker),
        as_user=True
    )


COMMANDS = {
    "choose": choose_baker,
}


def handle_command(command, channel, user):
    """
    Receives commands directed at the bot and determines if they
    are valid commands. If so, then acts on the commands. If not,
    returns back what it needs for clarification.
    """
    print(command, channel, user)

    cmd, *args = [s.strip() for s in command.split(" ") if s.strip()]
    impl = COMMANDS.get(cmd)

    if not impl:
        return

    impl(channel, user, *args)


def parse_slack_output(slack_rtm_output):
    """
    The Slack Real Time Messaging API is an events firehose.
    this parsing function returns None unless a message is
    directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if not output:
                continue

            text = output.get('text', '').strip()
            if text.startswith(AT_BOT):
                # return text after the @ mention, whitespace removed
                return (
                    output['text'].split(AT_BOT)[1].strip().lower(),
                    output['channel'],
                    output['user'],
                )

    return None, None, None


if __name__ == "__main__":
    if slack_client.rtm_connect():
        print("Let the Bake off commence")

        while True:
            command, channel, user = parse_slack_output(slack_client.rtm_read())

            if command and channel and user:
                handle_command(command, channel, user)

            time.sleep(1)
