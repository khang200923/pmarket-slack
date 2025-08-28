// @generated automatically by Diesel CLI.

diesel::table! {
    connections (main_chan_id) {
        main_chan_id -> Text,
        ping_chan_id -> Nullable<Text>,
    }
}

diesel::table! {
    global_vars (id) {
        id -> Int4,
        time_now -> Timestamp,
    }
}

diesel::table! {
    market_slack_msg (market_id, channel_id, ts) {
        market_id -> Int4,
        channel_id -> Text,
        ts -> Text,
        main -> Bool,
    }
}

diesel::table! {
    markets (id) {
        id -> Int4,
        #[max_length = 255]
        title -> Varchar,
        description -> Text,
        owner_id -> Text,
        liquidity -> Numeric,
        bought_shares -> Array<Nullable<Numeric>>,
        remind_at -> Timestamp,
        is_resolved -> Bool,
        resolution -> Nullable<Int4>,
        created_at -> Timestamp,
    }
}

diesel::table! {
    ping_managers (chan_id, user_id) {
        chan_id -> Text,
        user_id -> Text,
    }
}

diesel::table! {
    pingers (chan_id, user_id) {
        chan_id -> Text,
        user_id -> Text,
    }
}

diesel::table! {
    trades (id) {
        id -> Int4,
        market_id -> Int4,
        user_id -> Text,
        shares_amount -> Numeric,
        share_index -> Int4,
        balance_change -> Numeric,
        created_at -> Timestamp,
    }
}

diesel::table! {
    users (id) {
        id -> Text,
        balance -> Numeric,
    }
}

diesel::joinable!(market_slack_msg -> markets (market_id));
diesel::joinable!(markets -> users (owner_id));
diesel::joinable!(trades -> markets (market_id));
diesel::joinable!(trades -> users (user_id));

diesel::allow_tables_to_appear_in_same_query!(
    connections,
    global_vars,
    market_slack_msg,
    markets,
    ping_managers,
    pingers,
    trades,
    users,
);
