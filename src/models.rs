use diesel::prelude::*;
use bigdecimal::BigDecimal;
use chrono::NaiveDateTime;

#[derive(Queryable, Selectable)]
#[diesel(table_name = crate::schema::users)]
#[diesel(check_for_backend(diesel::pg::Pg))]
pub struct User {
    pub id: String,
    pub balance: BigDecimal,
}

#[derive(Queryable, Selectable)]
#[diesel(table_name = crate::schema::markets)]
#[diesel(check_for_backend(diesel::pg::Pg))]
pub struct Market {
    pub id: i32,
    pub title: String,
    pub description: String,
    pub owner_id: String,
    pub liquidity: BigDecimal,
    pub bought_shares: Vec<Option<BigDecimal>>,
    pub remind_at: NaiveDateTime,
    pub is_resolved: bool,
    pub resolution: Option<i32>,
    pub created_at: NaiveDateTime,
}

#[derive(Queryable, Selectable, Insertable)]
#[diesel(table_name = crate::schema::market_slack_msg)]
#[diesel(check_for_backend(diesel::pg::Pg))]
pub struct MarketSlackMsg {
    pub market_id: i32,
    pub channel_id: String,
    pub ts: String,
    pub main: bool,
}

#[derive(Queryable, Selectable)]
#[diesel(table_name = crate::schema::trades)]
#[diesel(check_for_backend(diesel::pg::Pg))]
pub struct Trade {
    pub id: i32,
    pub market_id: i32,
    pub user_id: String,
    pub shares_amount: BigDecimal,
    pub share_index: i32,
    pub balance_change: BigDecimal,
    pub created_at: NaiveDateTime,
}

#[derive(Insertable)]
#[diesel(table_name = crate::schema::users)]
#[diesel(check_for_backend(diesel::pg::Pg))]
pub struct NewUser {
    pub id: String,
    pub balance: BigDecimal,
}

#[derive(Insertable)]
#[diesel(table_name = crate::schema::markets)]
#[diesel(check_for_backend(diesel::pg::Pg))]
pub struct NewMarket {
    pub title: String,
    pub description: String,
    pub owner_id: String,
    pub liquidity: BigDecimal,
    pub remind_at: NaiveDateTime,
}

#[derive(Insertable)]
#[diesel(table_name = crate::schema::trades)]
#[diesel(check_for_backend(diesel::pg::Pg))]
pub struct NewTrade {
    pub market_id: i32,
    pub user_id: String,
    pub shares_amount: BigDecimal,
    pub share_index: i32,
    pub balance_change: BigDecimal,
}