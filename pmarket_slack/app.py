from datetime import datetime
import os
import json
import schedule
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
    ack()
    view = views.pmarket_add_view(
        command["text"], 
        channel_id=command["channel_id"],
        thread_ts=command.get("thread_ts", None),
        creator_id=user_id
    )
    client.views_open(
        trigger_id=command["trigger_id"],
        view=view
    )

@app.view("pmarket_add_view")
def handle_pmarket_add(ack, body, view, say):
    values = list(view["state"]["values"].values())
    values = {k: v for d in values for k, v in d.items()}
    title = values["action_title_pmarket_add"]["value"]
    description = values["action_desc_pmarket_add"].get("value", " ")
    if description is None:
        description = " "
    liquidity = float(values["action_liquidity_pmarket_add"]["value"])
    if liquidity < 100:
        ack({
            "response_action": "errors", 
            "errors": {
                "block_liquidity_pmarket_add": "Liquidity must be at least 100"
            }
        })
        return
    remind_at = values["action_remind_pmarket_add"]["selected_date"]
    remind_at = datetime.strptime(remind_at, "%Y-%m-%d")
    if remind_at <= datetime.now():
        ack({
            "response_action": "errors", 
            "errors": {
                "block_remind_pmarket_add": "Resolution date must be in the future"
            }
        })
        return
    remind_at = int(remind_at.timestamp())
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
    private_metadata = json.loads(view["private_metadata"])
    market_id = ps.create_market(
        title,
        description,
        user_id,
        Decimal(liquidity),
        remind_at
    )
    view = views.pmarket_view(market_id)
    res = say(
        channel=private_metadata["channel_id"],
        thread_ts=private_metadata.get("thread_ts"),
        blocks=view["blocks"],
        text=f"New market: \"{title}\"",
        metadata={
            "event_type": "pmarket_created",
            "event_payload": {
                "market_id": market_id,
            }
        }
    )
    channel_id = res["channel"]
    ts = res["message"]["ts"]
    ps.create_market_slack_msg(market_id, channel_id, ts, True)

def handle_general_trade(ack, body, buy_or_sell: bool, yes_or_no: bool):
    ack()
    market_id = int(body['message']['metadata']['event_payload']['market_id'])
    channel_id = body["container"]["channel_id"]
    ts = body["container"]["message_ts"]
    market_data = ps.get_market_data(market_id)
    user_id = body["user"]["id"]
    user = ps.get_user_data(user_id)
    balance = user["balance"]
    user_position = ps.get_positions(market_id).get(user_id, [0, 0])
    view = views.trade_view(market_data, balance, user_position, 0, buy_or_sell, yes_or_no, channel_id, ts)
    app.client.views_open(
        trigger_id=body["trigger_id"],
        view=view
    )

@app.action("action_buy_yes")
def handle_buy_yes(ack, body):
    handle_general_trade(ack, body, True, True)

@app.action("action_buy_no")
def handle_buy_no(ack, body):
    handle_general_trade(ack, body, True, False)

@app.action("action_sell_yes")
def handle_sell_yes(ack, body):
    handle_general_trade(ack, body, False, True)
    
@app.action("action_sell_no")
def handle_sell_no(ack, body):
    handle_general_trade(ack, body, False, False)

def handle_general_shares_trade(ack, body, buy_or_sell: bool, yes_or_no: bool):
    ack()
    private_metadata = json.loads(body["view"]["private_metadata"])
    market_data = private_metadata["market_data"]
    shares_amount = float(body["actions"][0]["value"])
    hashh = body["view"]["hash"]
    view = views.trade_view(
        market_data,
        private_metadata["balance"],
        private_metadata["user_positions"],
        shares_amount,
        buy_or_sell,
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
    handle_general_shares_trade(ack, body, True, True)

@app.action("action_shares_buy_no")
def handle_shares_buy_no(ack, body):
    handle_general_shares_trade(ack, body, True, False)
    
@app.action("action_shares_sell_yes")
def handle_shares_sell_yes(ack, body):
    handle_general_shares_trade(ack, body, False, True)

@app.action("action_shares_sell_no")
def handle_shares_sell_no(ack, body):
    handle_general_shares_trade(ack, body, False, False)

def handle_general_trade_view(ack, body, view, buy_or_sell: bool, yes_or_no: bool):
    values = list(view["state"]["values"].values())
    values = {k: v for d in values for k, v in d.items()}
    private_metadata = json.loads(view["private_metadata"])
    market_id = private_metadata["market_data"]["id"]
    buysell = "buy" if buy_or_sell else "sell"
    shares_amount = float(values[f"action_shares_{buysell}_" + ('yes' if yes_or_no else 'no')]["value"])
    user_id = body["user"]["id"]
    user = ps.get_user_data(user_id)
    if buy_or_sell:
        bet_amount = utils.bet_amount(
            ps.get_market_data(market_id),
            shares_amount,
            yes_or_no
        )
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
    else:
        user_position = ps.get_positions(market_id).get(user_id, [0, 0])
        position = user_position[0] if yes_or_no else user_position[1]
        if position < shares_amount:
            ack({
                "response_action": "errors",
                "errors": {
                    f"block_shares_sell_{'yes' if yes_or_no else 'no'}": f"Not enough shares. Position: {position:.0f}, Shares to sell: {shares_amount:.0f}"
                }
            })
            return
        ack()
        ps.create_trade(
            market_id,
            user_id,
            -shares_amount,
            0 if yes_or_no else 1
        )
    market_data = ps.get_market_data(market_id)
    view = views.pmarket_view(market_id)
    app.client.chat_update(
        channel=private_metadata["channel_id"],
        ts=private_metadata["ts"],
        blocks=view["blocks"],
        text=f"New trade at market: \"{market_data['title']}\"",
        metadata={
            "event_type": "pmarket_trade",
            "event_payload": {
                "market_id": market_id,
            }
        }
    )

@app.view("buy_view_yes")
def handle_buy_view_yes(ack, body, view):
    handle_general_trade_view(ack, body, view, True, True)

@app.view("buy_view_no")
def handle_buy_view_no(ack, body, view):
    handle_general_trade_view(ack, body, view, True, False)

@app.view("sell_view_yes")
def handle_sell_view_yes(ack, body, view):
    handle_general_trade_view(ack, body, view, False, True)

@app.view("sell_view_no")
def handle_sell_view_no(ack, body, view):
    handle_general_trade_view(ack, body, view, False, False)

@app.action("options_menu")
def handle_options_menu(ack, body):
    ack()
    market_id = int(body['message']['metadata']['event_payload']['market_id'])
    value = body['actions'][0]['selected_option']['value']
    if value == "resolve_yes":
        ps.resolve_market(market_id, 0)
    elif value == "resolve_no":
        ps.resolve_market(market_id, 1)
    elif value == "resolve_na":
        ps.resolve_market(market_id, None)
    else:
        raise ValueError(f"Unknown option value: {value}")
    market_data = ps.get_market_data(market_id)
    view = views.pmarket_view(market_id)
    app.client.chat_update(
        channel=body["container"]["channel_id"],
        ts=body["container"]["message_ts"],
        blocks=view["blocks"],
        text=f"Resolution at market \"{market_data['title']}\"",
        metadata={
            "event_type": "pmarket_resolved",
            "event_payload": {
                "market_id": market_id,
            }
        }
    )

def reminder_job():
    market_ids = ps.get_reminders_and_update_time()
    for market_id in market_ids:
        market_data = ps.get_market_data(market_id)
        owner_id = market_data["owner_id"]
        view = views.reminder_view(market_data)
        conv = app.client.conversations_open(
            users=owner_id
        )["channel"]["id"] # type: ignore
        app.client.chat_postMessage(
            channel=conv,
            blocks=view["blocks"],
            text=f"Reminder for market: \"{market_data['title']}\"",
        )

def main():
    schedule.every().hour.do(reminder_job)
    handler = SocketModeHandler(app, app_token=os.environ.get("SLACK_APP_TOKEN"))
    handler.start()

if __name__ == "__main__":
    main()