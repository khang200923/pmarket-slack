CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY, -- Slack ID
    balance DECIMAL(16, 4) NOT NULL DEFAULT 0.0000 CHECK (balance >= 0)
);

CREATE TABLE IF NOT EXISTS markets (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    owner_id TEXT NOT NULL REFERENCES users(id),
    liquidity DECIMAL(16, 4) NOT NULL CHECK (liquidity >= 0),
    bought_shares DECIMAL(16, 4)[] NOT NULL 
    CHECK (array_length(bought_shares, 1) = 2)
    CHECK (array_position(bought_shares, NULL) IS NULL)
    CHECK (bought_shares[1] >= 0 AND bought_shares[2] >= 0)
    DEFAULT ARRAY[0.0000, 0.0000],
    is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    resolution INT DEFAULT NULL, -- NULL when is_resolve is yes means N/A
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    market_id INT NOT NULL REFERENCES markets(id),
    user_id TEXT NOT NULL REFERENCES users(id),
    shares_amount DECIMAL(16, 4) NOT NULL, -- positive if bought, negative if sold
    share_index INT NOT NULL CHECK (share_index >= 0 AND share_index < 2), -- 0 for Yes, 1 for No
    balance_change DECIMAL(16, 4) NOT NULL, -- adds directly to balance
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);