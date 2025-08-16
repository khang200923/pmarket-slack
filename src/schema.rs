// @generated automatically by Diesel CLI.

diesel::table! {
    markets (id) {
        id -> Int4,
        #[max_length = 255]
        title -> Varchar,
        description -> Text,
        owner_id -> Text,
        liquidity -> Numeric,
        bought_shares -> Array<Nullable<Numeric>>,
        is_resolved -> Bool,
        resolution -> Nullable<Int4>,
        created_at -> Timestamp,
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

diesel::joinable!(markets -> users (owner_id));
diesel::joinable!(trades -> markets (market_id));
diesel::joinable!(trades -> users (user_id));

diesel::allow_tables_to_appear_in_same_query!(
    markets,
    trades,
    users,
);
