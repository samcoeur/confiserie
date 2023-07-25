


CREATE TABLE orders (
   cart_id INTEGER NOT NULL,
   product_id INTEGER NOT NULL,
   product_name varchar(100) NOT NULL,
   units INTEGER NOT NULL,
   cost DECIMAL(10,2) NOT NULL,
   FOREIGN KEY (product_id) REFERENCES products (id),
   FOREIGN KEY (cart_id) REFERENCES carts (id)
);