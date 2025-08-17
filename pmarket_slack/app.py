import json
import os
from decimal import Decimal
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import pmarket_slack.pmarket_slack as ps
import pmarket_slack.views as views
import pmarket_slack.utils as utils

load_dotenv()

app = App()

@app.event("app_home_opened")
def handle_app_home_opened(event, client):
    user_id = event["user"]
    ps.try_create_user(user_id)
    view = views.home_view(user_id)
    client.views_publish(
        user_id=user_id,
        view=view
    )

@app.command("/pmarket")
def handle_pmarket_command(ack, command, client):
    user_id = command["user_id"]
    ps.try_create_user(user_id)
    print("a", command["text"])
    ack()
    print("b", command["text"])
    view = views.pmarket_add_view(
        command["text"], 
        channel_id=command["channel_id"],
        thread_ts=command.get("thread_ts", None)
    )
    print("c", command["text"])
    client.views_open(
        trigger_id=command["trigger_id"],
        view=view
    )
    print("d", command["text"])

@app.view("pmarket_add_view")
def handle_pmarket_add(ack, body, view, say):
    print("a2", view["state"])
    values = list(view["state"]["values"].values())
    values = {k: v for d in values for k, v in d.items()}
    title = values["action_title_pmarket_add"]["value"]
    description = values["action_desc_pmarket_add"].get("value", "")
    liquidity = float(values["action_liquidity_pmarket_add"]["value"])
    if liquidity < 100:
        print("aaaaaa")
        ack({
            "response_action": "errors", 
            "errors": {
                "block_liquidity_pmarket_add": "Liquidity must be at least 100"
            }
        })
        return
    user_id = body["user"]["id"]
    user = ps.get_user_data(user_id)
    if user["balance"] < liquidity:
        ack({
            "response_action": "errors", 
            "errors": {
                "block_liquidity_pmarket_add": f"Not enough funds. Balance: {user['balance']:.0f}"
            }
        })
        return
    ack()
    market_id = ps.create_market(
        title,
        description,
        user_id,
        Decimal(liquidity)
    )
    private_metadata = json.loads(view["private_metadata"])
    print(private_metadata)
    view = views.pmarket_view(market_id)
    say(
        channel=private_metadata["channel_id"],
        thread_ts=private_metadata.get("thread_ts"),
        blocks=view["blocks"],
        text=f"New market: {title}",
        metadata={
            "event_type": "pmarket_created",
            "event_payload": {
                "market_id": market_id,
            }
        }
    )

def handle_general_bet(ack, body, yes_or_no: bool):
    ack()
    print(body)
    market_id = int(body['message']['metadata']['event_payload']['market_id'])
    channel_id = body["container"]["channel_id"]
    ts = body["container"]["message_ts"]
    market_data = ps.get_market_data(market_id)
    view = views.bet_view(market_data, 0, yes_or_no, channel_id, ts)
    app.client.views_open(
        trigger_id=body["trigger_id"],
        view=view
    )

@app.action("action_bet_yes")
def handle_bet_yes(ack, body):
    handle_general_bet(ack, body, True)

@app.action("action_bet_no")
def handle_bet_no(ack, body):
    handle_general_bet(ack, body, False)

def handle_general_shares_buy(ack, body, yes_or_no: bool):
    ack()
    private_metadata = json.loads(body["view"]["private_metadata"])
    print("ggfg", private_metadata)
    market_data = private_metadata["market_data"]
    shares_amount = float(body["actions"][0]["value"])
    hashh = body["view"]["hash"]
    view = views.bet_view(
        market_data,
        shares_amount,
        yes_or_no,
        private_metadata["channel_id"],
        private_metadata["ts"]
    )
    app.client.views_update(
        trigger_id=body["trigger_id"],
        view_id=body["view"]["id"],
        view=view,
        hash=hashh
    )

@app.action("action_shares_buy_yes")
def handle_shares_buy_yes(ack, body):
    handle_general_shares_buy(ack, body, True)

@app.action("action_shares_buy_no")
def handle_shares_buy_no(ack, body):
    handle_general_shares_buy(ack, body, False)

def handle_general_bet_view(ack, body, view, yes_or_no: bool):
    values = list(view["state"]["values"].values())
    values = {k: v for d in values for k, v in d.items()}
    private_metadata = json.loads(view["private_metadata"])
    market_id = private_metadata["market_data"]["id"]
    shares_amount = float(values["action_shares_buy_" + ('yes' if yes_or_no else 'no')]["value"])
    bet_amount = utils.bet_amount(
        ps.get_market_data(market_id),
        shares_amount,
        yes_or_no
    )
    user_id = body["user"]["id"]
    user = ps.get_user_data(user_id)
    if user["balance"] < bet_amount:
        ack({
            "response_action": "errors",
            "errors": {
                f"block_shares_buy_{'yes' if yes_or_no else 'no'}": f"Not enough funds. Balance: {user['balance']:.0f}, Bet amount: {bet_amount:.0f}"
            }
        })
        return
    ack()
    ps.create_trade(
        market_id,
        user_id,
        shares_amount,
        0 if yes_or_no else 1
    )
    market_data = ps.get_market_data(market_id)
    print("eeeeeeeeeeeeeeeeeeeee", market_data) 
    view = views.pmarket_view(market_id)
    app.client.chat_update(
        channel=private_metadata["channel_id"],
        ts=private_metadata["ts"],
        blocks=view["blocks"],
        text=f"New trade at market: {market_data['title']}",
        metadata={
            "event_type": "pmarket_created",
            "event_payload": {
                "market_id": market_id,
            }
        }
    )

@app.view("bet_view_yes")
def handle_bet_view_yes(ack, body, view):
    handle_general_bet_view(ack, body, view, True)

@app.view("bet_view_no")
def handle_bet_view_no(ack, body, view):
    handle_general_bet_view(ack, body, view, False)

def main():
    handler = SocketModeHandler(app, app_token=os.environ.get("SLACK_APP_TOKEN"))
    handler.start()

if __name__ == "__main__":
    main()