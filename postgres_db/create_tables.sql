CREATE TABLE IF NOT EXISTS stores (
    id   UUID NOT NULL PRIMARY KEY,
    name VARCHAR(255)
    );

CREATE TABLE IF NOT EXISTS addresses (
    id       UUID                       NOT NULL PRIMARY KEY,
    store_id UUID REFERENCES stores(id) ON DELETE CASCADE NOT NULL,
    address  VARCHAR(255)               NOT NULL
    );

CREATE TABLE IF NOT EXISTS packages (
    id            UUID                          NOT NULL PRIMARY KEY,
    address_id    UUID REFERENCES addresses(id) ON DELETE CASCADE NOT NULL,
    description   VARCHAR(255)                  NOT NULL,
    pickup_before TIMESTAMP                     NOT NULL,
    amount        INT                           NOT NULL,
    price         INT                           NOT NULL
    );

CREATE TABLE IF NOT EXISTS orders (
    id            UUID   NOT NULL PRIMARY KEY,
    chat_id       BIGINT NOT NULL,
    random_number BIGINT NOT NULL
    );

CREATE TABLE IF NOT EXISTS order_packages (
    order_id   UUID REFERENCES orders(id)   ON DELETE CASCADE NOT NULL,
    package_id UUID REFERENCES packages(id) ON DELETE CASCADE NOT NULL
    );

CREATE TABLE IF NOT EXISTS partners (
    chat_id BIGINT NOT NULL PRIMARY KEY
    );

CREATE TABLE IF NOT EXISTS partner_addresses (
    partner_id BIGINT REFERENCES partners(chat_id) ON DELETE CASCADE NOT NULL,
    address_id UUID   REFERENCES addresses(id)     ON DELETE CASCADE NOT NULL
    );

CREATE TABLE IF NOT EXISTS partner_packages (
    partner_id BIGINT REFERENCES partners(chat_id) ON DELETE CASCADE NOT NULL,
    package_id UUID   REFERENCES packages(id)      ON DELETE CASCADE NOT NULL
    );

CREATE TABLE IF NOT EXISTS partner_orders (
    partner_id BIGINT REFERENCES partners(chat_id) ON DELETE CASCADE NOT NULL,
    order_id   UUID   REFERENCES orders(id)        ON DELETE CASCADE NOT NULL
    );
