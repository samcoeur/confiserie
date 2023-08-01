


CREATE TABLE deliveries (
   cart_id INTEGER NOT NULL,
   customer_id INTEGER NOT NULL,
   customername text(120),
   delivery_address varchar(150) NOT NULL,
   date date not null,
   note text(200) ,
   FOREIGN KEY (cart_id) REFERENCES carts(id),
   FOREIGN KEY (customer_id) REFERENCES customers (user_id)
);