from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

website = Flask(__name__, template_folder="templates", static_folder="static")
website.secret_key = "****"
DB_PATH = "wowfoodsnew.db"
DELIVERY_FEE = Decimal("2.00")
TAX_RATE = Decimal("0.15")


def _calculate_checkout_totals(subtotal):
    subtotal = Decimal(str(subtotal)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    delivery_fee = DELIVERY_FEE if subtotal > 0 else Decimal("0.00")
    tax_amount = (subtotal * TAX_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    order_total = subtotal + delivery_fee + tax_amount
    return float(subtotal), float(delivery_fee), float(tax_amount), float(order_total)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _build_cart_dict(items):
    """Convert order items to session cart format."""
    cart = {}
    for it in items:
        cart[str(it['product_id'])] = {
            'product_id': it['product_id'],
            'product_name': it['product_name'],
            'price': float(it['price_at_purchase']) if it['price_at_purchase'] is not None else 0.0,
            'image_url': it['image_url'],
            'category_name': None,
            'quantity': it['quantity'],
            'stock': it['stock'] if 'stock' in it.keys() else 0
        }
    return cart


def _update_order_total(c, order_id):
    """Recalculate and update order total."""
    total_row = c.execute("SELECT SUM(quantity * price_at_purchase) AS total FROM Order_Items WHERE order_id = ?", (order_id,)).fetchone()
    total = total_row['total'] if total_row and total_row['total'] is not None else 0.0
    c.execute("UPDATE Orders SET total_price = ? WHERE order_id = ?", (total, order_id))
    return total


def _deduct_product_stock(c, items):
    for item in items:
        quantity = int(item['quantity'])
        stock = item['stock']
        if quantity <= 0 or stock is None or stock < quantity:
            return False

    for item in items:
        quantity = int(item['quantity'])
        updated = c.execute(
            "UPDATE Products SET stock = stock - ? WHERE product_id = ? AND stock >= ?",
            (quantity, item['product_id'], quantity)
        )
        if updated.rowcount != 1:
            return False
    return True


def _sync_persisted_cart_to_session(c, user_id):
    """Fetch user's cart order and sync to session."""
    order = c.execute("SELECT order_id FROM Orders WHERE user_id = ? AND status = 'cart' LIMIT 1", (user_id,)).fetchone()
    if order:
        items = c.execute("SELECT oi.order_item_id, oi.product_id, p.product_name, oi.quantity, oi.price_at_purchase, p.image AS image_url, p.stock FROM Order_Items oi LEFT JOIN Products p ON oi.product_id = p.product_id WHERE oi.order_id = ?", (order['order_id'],)).fetchall()
        cart = _build_cart_dict(items)
        session['cart'] = cart
        session.modified = True
        return order['order_id']
    return None


@website.route('/cart', methods=['GET', 'POST'])
def cart_page():
    # POST actions: add to cart (product_id) or purchase (action=purchase)
    if request.method == 'POST':
        # actions: add (default), update, remove, purchase
        product_id = request.form.get('product_id')
        action = request.form.get('action', 'add')

        # normalize product_id when present
        if product_id:
            try:
                product_id = int(product_id)
            except Exception:
                return redirect(request.referrer or url_for('menu_page'))

        # Update quantity for an item
        if action == 'update' and product_id:
            try:
                qty = int(request.form.get('quantity', 1))
            except Exception:
                qty = 1

            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            if qty < 1:
                if is_ajax:
                    return jsonify({'status': 'error', 'message': 'Quantity must be at least 1'}), 400
                return redirect(url_for('cart_page'))

            user_id = session.get('user_id')
            item_price = 0.0
            if user_id:
                connect = get_db()
                c = connect.cursor()
                order = c.execute("SELECT order_id FROM Orders WHERE user_id = ? AND status = 'cart' LIMIT 1", (user_id,)).fetchone()
                if not order:
                    connect.close()
                    if is_ajax:
                        return jsonify({'status': 'error', 'message': 'Cart not found'})
                    return redirect(request.referrer or url_for('cart_page'))
                order_id = order['order_id']
                product = c.execute("SELECT price, stock FROM Products WHERE product_id = ?", (product_id,)).fetchone()
                if qty > 0 and (not product or product['stock'] is None or qty > product['stock']):
                    connect.close()
                    if is_ajax:
                        return jsonify({'status': 'error', 'message': 'Not enough stock available'}), 409
                    return redirect(url_for('cart_page', error='stock'))
                existing = c.execute("SELECT * FROM Order_Items WHERE order_id = ? AND product_id = ?", (order_id, product_id)).fetchone()
                if qty <= 0:
                    if existing:
                        c.execute("DELETE FROM Order_Items WHERE order_item_id = ?", (existing['order_item_id'],))
                else:
                    if existing:
                        c.execute("UPDATE Order_Items SET quantity = ? WHERE order_item_id = ?", (qty, existing['order_item_id']))
                    else:
                        price = float(product['price']) if product['price'] is not None else 0.0
                        item_price = price
                        c.execute("INSERT INTO Order_Items (order_id, product_id, quantity, price_at_purchase) VALUES (?, ?, ?, ?)", (order_id, product_id, qty, price))
                _update_order_total(c, order_id)
                items = c.execute("SELECT oi.order_item_id, oi.product_id, p.product_name, oi.quantity, oi.price_at_purchase, p.image AS image_url FROM Order_Items oi LEFT JOIN Products p ON oi.product_id = p.product_id WHERE oi.order_id = ?", (order_id,)).fetchall()
                connect.commit()
                connect.close()
                cart = _build_cart_dict(items)
                session['cart'] = cart
                session.modified = True
                if is_ajax:
                    current_item = cart.get(str(product_id), {})
                    item_price = float(current_item.get('price', 0.0))
                    return jsonify({'status': 'ok', 'quantity': qty, 'product_id': product_id, 'item_total': float(qty) * item_price, 'cart_total': sum(float(v.get('price', 0.0)) * int(v.get('quantity', 0)) for v in cart.values())})
                return redirect(request.referrer or url_for('cart_page'))

            # guest session cart
            cart = session.get('cart', {})
            key = str(product_id)
            if qty <= 0:
                cart.pop(key, None)
            else:
                connect = get_db()
                c = connect.cursor()
                prod = c.execute("SELECT product_id, product_name, price, image AS image_url, category_id, stock FROM Products WHERE product_id = ? LIMIT 1", (product_id,)).fetchone()
                connect.close()
                if not prod or prod['stock'] is None or qty > prod['stock']:
                    if is_ajax:
                        return jsonify({'status': 'error', 'message': 'Not enough stock available'}), 409
                    return redirect(url_for('cart_page', error='stock'))
                if key in cart:
                    item_price = float(cart[key].get('price', 0.0))
                    cart[key]['quantity'] = qty
                    cart[key]['stock'] = prod['stock']
                else:
                    item_price = float(prod['price']) if prod['price'] is not None else 0.0
                    cart[key] = {
                        'product_id': prod['product_id'],
                        'product_name': prod['product_name'],
                        'price': item_price,
                        'image_url': prod['image_url'],
                        'category_name': None,
                        'quantity': qty,
                        'stock': prod['stock']
                    }
            session['cart'] = cart
            session.modified = True
            if is_ajax:
                return jsonify({'status': 'ok', 'quantity': qty, 'product_id': product_id, 'item_total': float(qty) * item_price, 'cart_total': sum(float(v.get('price', 0.0)) * int(v.get('quantity', 0)) for v in cart.values())})
            return redirect(request.referrer or url_for('cart_page'))

        # Remove item from cart
        if action == 'remove' and product_id:
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            user_id = session.get('user_id')
            if user_id:
                connect = get_db()
                c = connect.cursor()
                order = c.execute("SELECT order_id FROM Orders WHERE user_id = ? AND status = 'cart' LIMIT 1", (user_id,)).fetchone()
                if order:
                    order_id = order['order_id']
                    c.execute("DELETE FROM Order_Items WHERE order_id = ? AND product_id = ?", (order_id, product_id))
                    _update_order_total(c, order_id)
                    items = c.execute("SELECT oi.order_item_id, oi.product_id, p.product_name, oi.quantity, oi.price_at_purchase, p.image AS image_url FROM Order_Items oi LEFT JOIN Products p ON oi.product_id = p.product_id WHERE oi.order_id = ?", (order_id,)).fetchall()
                    connect.commit()
                    connect.close()

                    cart = _build_cart_dict(items)
                    session['cart'] = cart
                    session.modified = True
                    if is_ajax:
                        return jsonify({'status': 'ok', 'removed': True, 'cart_total': sum(float(v.get('price', 0.0)) * int(v.get('quantity', 0)) for v in cart.values())})
                    return redirect(request.referrer or url_for('cart_page'))
                connect.close()
                if is_ajax:
                    return jsonify({'status': 'ok', 'removed': True})
                return redirect(request.referrer or url_for('cart_page'))

            # guest
            cart = session.get('cart', {})
            cart.pop(str(product_id), None)
            session['cart'] = cart
            session.modified = True
            if is_ajax:
                return jsonify({'status': 'ok', 'removed': True, 'cart_total': sum(float(v.get('price', 0.0)) * int(v.get('quantity', 0)) for v in cart.values())})
            return redirect(request.referrer or url_for('cart_page'))

        # Add to cart (default)
        if action == 'add' and product_id:
            connect = get_db()
            c = connect.cursor()
            product = c.execute("""
                                SELECT p.product_id, p.product_name, p.price, p.image AS image_url, p.stock, c.category_name
                                FROM Products p
                                LEFT JOIN Categories c ON p.category_id = c.category_id
                                WHERE p.product_id = ?
                                LIMIT 1
                                """, (product_id,)).fetchone()
            connect.close()

            if not product:
                return redirect(request.referrer or url_for('menu_page'))

            if product['stock'] is None or product['stock'] <= 0:
                return redirect(url_for('cart_page', error='stock'))

            user_id = session.get('user_id')
            # If user is signed in, persist the cart as an Orders row with status 'cart'
            if user_id:
                connect = get_db()
                c = connect.cursor()
                order = c.execute("SELECT order_id FROM Orders WHERE user_id = ? AND status = 'cart' LIMIT 1", (user_id,)).fetchone()
                if order:
                    order_id = order['order_id']
                else:
                    order_date = datetime.now(timezone.utc).isoformat(sep=' ', timespec='seconds')
                    # compute next order_id
                    max_row = c.execute("SELECT MAX(order_id) AS m FROM Orders").fetchone()
                    next_order_id = (max_row['m'] if max_row and max_row['m'] is not None else 0) + 1
                    c.execute("INSERT INTO Orders (order_id, user_id, order_date, total_price, status) VALUES (?, ?, ?, ?, ?)", (next_order_id, user_id, order_date, 0.0, 'cart'))
                    order_id = next_order_id

                # update or insert order item
                existing = c.execute("SELECT * FROM Order_Items WHERE order_id = ? AND product_id = ?", (order_id, product['product_id'])).fetchone()
                if existing:
                    new_qty = existing['quantity'] + 1
                    if new_qty > product['stock']:
                        connect.close()
                        return redirect(url_for('cart_page', error='stock'))
                    c.execute("UPDATE Order_Items SET quantity = ? WHERE order_item_id = ?", (new_qty, existing['order_item_id']))
                else:
                    c.execute("INSERT INTO Order_Items (order_id, product_id, quantity, price_at_purchase) VALUES (?, ?, ?, ?)",
                              (order_id, product['product_id'], 1, float(product['price']) if product['price'] is not None else 0.0))

                # recompute order total
                _update_order_total(c, order_id)

                # fetch order items to mirror session cart for UI
                items = c.execute("SELECT oi.order_item_id, oi.product_id, p.product_name, oi.quantity, oi.price_at_purchase, p.image AS image_url FROM Order_Items oi LEFT JOIN Products p ON oi.product_id = p.product_id WHERE oi.order_id = ?", (order_id,)).fetchall()
                connect.commit()
                connect.close()

                cart = _build_cart_dict(items)
                session['cart'] = cart
                session.modified = True
                return redirect(request.referrer or url_for('menu_page'))

            # not signed-in: keep session-only cart
            cart = session.get('cart', {})
            key = str(product['product_id'])
            if key in cart:
                if cart[key].get('quantity', 0) >= product['stock']:
                    return redirect(url_for('cart_page', error='stock'))
                cart[key]['quantity'] = cart[key].get('quantity', 0) + 1
            else:
                cart[key] = {
                    'product_id': product['product_id'],
                    'product_name': product['product_name'],
                    'price': float(product['price']) if product['price'] is not None else 0.0,
                    'image_url': product['image_url'],
                    'category_name': product['category_name'],
                    'quantity': 1
                }
            session['cart'] = cart
            session.modified = True
            return redirect(request.referrer or url_for('menu_page'))

        # Purchase action
        if action == 'purchase':
            # Only allow purchase when the user is signed in
            if not session.get('user_id'):
                return redirect(url_for('signin_page'))
            user_id = session.get('user_id')
            connect = get_db()
            c = connect.cursor()
            # if a persisted 'cart' order exists for user, mark it as placed
            order = c.execute("SELECT order_id FROM Orders WHERE user_id = ? AND status = 'cart' LIMIT 1", (user_id,)).fetchone()
            if order:
                order_id = order['order_id']
                connect.execute("BEGIN IMMEDIATE")
                items = c.execute("SELECT oi.product_id, oi.quantity, p.stock FROM Order_Items oi LEFT JOIN Products p ON oi.product_id = p.product_id WHERE oi.order_id = ?", (order_id,)).fetchall()
                if not _deduct_product_stock(c, items):
                    connect.rollback()
                    connect.close()
                    return redirect(url_for('cart_page', error='stock'))
                # mark order as pending shipping
                c.execute("UPDATE Orders SET status = 'Pending' WHERE order_id = ?", (order_id,))
                # ensure total_price is up-to-date
                total_row = c.execute("SELECT SUM(quantity * price_at_purchase) AS total FROM Order_Items WHERE order_id = ?", (order_id,)).fetchone()
                subtotal = total_row['total'] if total_row and total_row['total'] is not None else 0.0
                _, _, _, total = _calculate_checkout_totals(subtotal)
                c.execute("UPDATE Orders SET total_price = ? WHERE order_id = ?", (total, order_id))
                # record payment as Paid
                pay_row = c.execute("SELECT MAX(payment_id) AS m FROM Payments").fetchone()
                next_pay_id = (pay_row['m'] if pay_row and pay_row['m'] is not None else 0) + 1
                payment_date = datetime.now(timezone.utc).isoformat(sep=' ', timespec='seconds')
                c.execute("INSERT INTO Payments (payment_id, order_id, amount_paid, payment_date, payment_status) VALUES (?, ?, ?, ?, ?)", (next_pay_id, order_id, total, payment_date, 'Paid'))
                connect.commit()
                connect.close()
                session.pop('cart', None)
                return redirect(url_for('accounts_page'))

            # fallback: no persisted order found — try to purchase session cart
            cart = session.get('cart')
            if not cart:
                connect.close()
                return redirect(url_for('cart_page'))

            connect.execute("BEGIN IMMEDIATE")
            stock_items = []
            for item in cart.values():
                product = c.execute("SELECT stock FROM Products WHERE product_id = ?", (item['product_id'],)).fetchone()
                stock_items.append({
                    'product_id': item['product_id'],
                    'quantity': int(item.get('quantity', 1)),
                    'stock': product['stock'] if product else None
                })
            if not _deduct_product_stock(c, stock_items):
                connect.rollback()
                connect.close()
                return redirect(url_for('cart_page', error='stock'))

            # create new order from session cart
            order_date = datetime.now(timezone.utc).isoformat(sep=' ', timespec='seconds')
            total = 0.0
            for k, v in cart.items():
                qty = int(v.get('quantity', 1))
                price = float(v.get('price', 0.0))
                total += qty * price
            _, _, _, total = _calculate_checkout_totals(total)

            # create a new order with explicit next order_id and status Pending
            status = 'Pending'
            max_row = c.execute("SELECT MAX(order_id) AS m FROM Orders").fetchone()
            next_order_id = (max_row['m'] if max_row and max_row['m'] is not None else 0) + 1
            c.execute("INSERT INTO Orders (order_id, user_id, order_date, total_price, status) VALUES (?, ?, ?, ?, ?)", (next_order_id, user_id, order_date, total, status))
            order_id = next_order_id
            for key, item in cart.items():
                product_id = item['product_id']
                qty = int(item.get('quantity', 1))
                price = float(item.get('price', 0.0))
                c.execute("INSERT INTO Order_Items (order_id, product_id, quantity, price_at_purchase) VALUES (?, ?, ?, ?)", (order_id, product_id, qty, price))
            # record payment as Paid
            pay_row = c.execute("SELECT MAX(payment_id) AS m FROM Payments").fetchone()
            next_pay_id = (pay_row['m'] if pay_row and pay_row['m'] is not None else 0) + 1
            payment_date = datetime.now(timezone.utc).isoformat(sep=' ', timespec='seconds')
            c.execute("INSERT INTO Payments (payment_id, order_id, amount_paid, payment_date, payment_status) VALUES (?, ?, ?, ?, ?)", (next_pay_id, order_id, total, payment_date, 'Paid'))

            connect.commit()
            connect.close()
            session.pop('cart', None)
            return redirect(url_for('accounts_page'))

    # GET: render cart view (existing behavior)
    cart_items = []
    if session.get('user_id'):
        connect = get_db()
        c = connect.cursor()
        order = c.execute("SELECT order_id FROM Orders WHERE user_id = ? AND status = 'cart' LIMIT 1", (session.get('user_id'),)).fetchone()
        if order:
            items = c.execute("SELECT oi.product_id, p.product_name, oi.quantity, oi.price_at_purchase, p.image AS image_url, p.stock FROM Order_Items oi LEFT JOIN Products p ON oi.product_id = p.product_id WHERE oi.order_id = ?", (order['order_id'],)).fetchall()
            for it in items:
                cart_items.append({
                    'product_id': it['product_id'],
                    'product_name': it['product_name'],
                    'quantity': it['quantity'],
                    'price': float(it['price_at_purchase']) if it['price_at_purchase'] is not None else 0.0,
                    'image_url': it['image_url'],
                    'stock': it['stock'] or 0
                })
        connect.close()
    else:
        if session.get('cart'):
            cart_items = list(session.get('cart', {}).values())
            connect = get_db()
            c = connect.cursor()
            for item in cart_items:
                stock_row = c.execute("SELECT stock FROM Products WHERE product_id = ?", (item['product_id'],)).fetchone()
                item['stock'] = stock_row['stock'] or 0 if stock_row else 0
            connect.close()

    cart_total = sum(float(item.get('price', 0.0)) * int(item.get('quantity', 0)) for item in cart_items)
    cart_total, delivery_fee, tax_amount, order_total = _calculate_checkout_totals(cart_total)
    return render_template(
        'Cart.html',
        cart_items=cart_items,
        cart_total=cart_total,
        delivery_fee=delivery_fee,
        tax_rate=float(TAX_RATE),
        tax_amount=tax_amount,
        order_total=order_total,
        current_user=session.get('full_name')
    )

@website.route("/signin", methods=["GET", "POST"])
def signin_page():
    # if already signed in, show accounts page instead
    if session.get('user_id'):
        return redirect(url_for('accounts_page'))

    error = None
    formdata = {}
    if request.method == 'POST':
        formdata = {k: v for k, v in request.form.items()}

        if request.form.get('full_name'):
            full_name = request.form.get('full_name', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            date_of_birth = request.form.get('date_of_birth')
            wants_offers = 1 if request.form.get('wants_offers') else 0

            if password != confirm_password:
                error = 'Passwords do not match'
            elif len(password) < 8:
                error = 'Password must be at least 8 characters long'
            else:
                connect = get_db()
                c = connect.cursor()
                existing = c.execute("SELECT user_id FROM Users WHERE email = ? LIMIT 1", (email,)).fetchone()
                if existing:
                    error = 'An account with that email already exists'
                else:
                    next_id = c.execute("SELECT COALESCE(MAX(user_id), 0) + 1 FROM Users").fetchone()[0]
                    c.execute("""
                        INSERT INTO Users
                            (user_id, full_name, email, password_hash, date_of_birth, wants_offers, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (next_id, full_name, email, generate_password_hash(password),
                               date_of_birth, wants_offers,
                               datetime.now(timezone.utc).isoformat(sep=' ', timespec='seconds')))
                    connect.commit()
                    connect.close()
                    return redirect(url_for('signin_page'))
                connect.close()

        if error:
            return render_template('Signin.html', users=[], error=error, formdata=formdata,
                                   current_user=session.get('full_name'))

        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')

        connect = get_db()
        c = connect.cursor()
        user = c.execute("""
                        SELECT *
                        FROM Users
                        WHERE email = ?
                        LIMIT 1
                        """, (email,)).fetchone()
        connect.close()

        if user:
            # Verify the password hash stored by the Users schema.
            try:
                stored = user['password_hash']
            except Exception:
                stored = None

            verified = False
            if stored:
                try:
                    verified = check_password_hash(stored, password)
                except Exception:
                    verified = (stored == password)
            else:
                # no password stored: fail
                verified = False

            if verified:
                # set temporary session (signed-in) -- persists until sign out or browser close depending on config
                session['user_id'] = user['user_id']
                session['full_name'] = user.get('full_name') if isinstance(user, dict) or hasattr(user, 'get') else user['full_name']
                return redirect(url_for('accounts_page'))
            else:
                error = 'Invalid credentials'
        else:
            # account does not exist: keep form info and show error
            error = 'Account not found'

    # provide list of users for template if needed and pass formdata and current user
    connect = get_db()
    c = connect.cursor()
    users = c.execute("""
                        SELECT *
                        FROM Users AS u
                        ORDER BY u.user_id
                        """).fetchall()
    connect.close()
    return render_template('Signin.html', users=users, error=error, formdata=formdata, current_user=session.get('full_name'))

@website.route("/")
def home_page():
    connect = get_db()
    c = connect.cursor()
    popular = c.execute("""
                        SELECT p.product_id,
                            p.product_name,
                            p.price,
                            p.image AS image_url,
                            p.stock,
                            c.category_name,
                            SUM(oi.quantity) AS total_units_sold,
                            SUM(oi.quantity * oi.price_at_purchase) AS total_revenue
                        FROM Products p
                            LEFT JOIN Categories c ON p.category_id = c.category_id
                            LEFT JOIN Order_Items oi ON p.product_id = oi.product_id
                        GROUP BY p.product_id
                        ORDER BY total_units_sold DESC
                        """).fetchall()
    connect.close()
    return render_template('Wowfoods.html', popular=popular, current_user=session.get('full_name'))

@website.route("/menu")
def menu_page():
    connect = get_db()
    c = connect.cursor()
    categories = c.execute("""
                            SELECT *
                            FROM Categories 
                            ORDER BY category_id ASC
                            """).fetchall()
    products = c.execute("""
                        SELECT p.product_id,
                            p.category_id,
                            c.category_name,
                            p.product_name,
                            p.price,
                            p.description,
                            p.image AS image_url,
                            p.stock
                        FROM Products AS p
                        LEFT JOIN Categories AS c
                            ON p.category_id = c.category_id
                        ORDER BY p.product_id ASC
                            """).fetchall()
    connect.close()
    return render_template('Menu.html', categories=categories, products=products, current_user=session.get('full_name'))

@website.route("/accounts")
def accounts_page():
    # protect accounts page: only accessible when signed in
    if not session.get('user_id'):
        return redirect(url_for('signin_page'))

    connect = get_db()
    c = connect.cursor()
    accounts = c.execute("""
                        SELECT *
                        FROM Users
                        ORDER BY user_id
                        """).fetchall()
    # optionally fetch orders for the signed-in user
    user_orders = c.execute("""
                        SELECT o.*
                        FROM Orders o
                        WHERE o.user_id = ? AND o.status != 'cart'
                        ORDER BY o.order_date DESC
                        """, (session.get('user_id'),)).fetchall()
    # fetch order items for these orders
    order_items = c.execute("""
                        SELECT oi.order_id, oi.product_id, oi.quantity, oi.price_at_purchase, p.product_name
                        FROM Order_Items oi
                        JOIN Orders o ON oi.order_id = o.order_id
                        LEFT JOIN Products p ON oi.product_id = p.product_id
                        WHERE o.user_id = ? AND o.status != 'cart'
                        ORDER BY oi.order_id ASC
                        """, (session.get('user_id'),)).fetchall()
    # fetch payments for these orders
    payments = c.execute("""
                        SELECT pay.payment_id, pay.order_id, pay.amount_paid, pay.payment_date, pay.payment_status
                        FROM Payments pay
                        JOIN Orders o ON pay.order_id = o.order_id
                        WHERE o.user_id = ? AND o.status != 'cart'
                        ORDER BY pay.payment_id ASC
                        """, (session.get('user_id'),)).fetchall()
    # group items by order_id for easy template rendering
    items_by_order = {}
    for it in order_items:
        items_by_order.setdefault(it['order_id'], []).append(dict(it))
    payments_by_order = {}
    for p in payments:
        payments_by_order.setdefault(p['order_id'], []).append(dict(p))
    connect.close()
    return render_template('Accounts.html', accounts=accounts, user_orders=user_orders, order_items=items_by_order, payments=payments_by_order, current_user=session.get('full_name'), delete_error=request.args.get('delete_error'))


@website.route('/delete-account', methods=['POST'])
def delete_account():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('signin_page'))

    if request.form.get('confirm_delete') != 'yes':
        return redirect(url_for('accounts_page', delete_error='confirmation'))

    password = request.form.get('password', '')
    connect = get_db()
    c = connect.cursor()
    user = c.execute("SELECT password_hash FROM Users WHERE user_id = ?", (user_id,)).fetchone()
    if not user or not password:
        connect.close()
        return redirect(url_for('accounts_page', delete_error='password'))

    stored_password = user['password_hash']
    try:
        password_matches = check_password_hash(stored_password, password)
    except (TypeError, ValueError):
        password_matches = stored_password == password

    if not password_matches:
        connect.close()
        return redirect(url_for('accounts_page', delete_error='password'))

    try:
        c.execute("DELETE FROM Payments WHERE order_id IN (SELECT order_id FROM Orders WHERE user_id = ?)", (user_id,))
        c.execute("DELETE FROM Order_Items WHERE order_id IN (SELECT order_id FROM Orders WHERE user_id = ?)", (user_id,))
        c.execute("DELETE FROM Orders WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM Users WHERE user_id = ?", (user_id,))
        connect.commit()
    except sqlite3.Error:
        connect.rollback()
        connect.close()
        raise
    connect.close()
    session.clear()
    return redirect(url_for('home_page'))


@website.route('/signout', methods=['POST'])
def signout():
    session.pop('user_id', None)
    session.pop('full_name', None)
    # # Also clear any temporary cart when signing out
    # session.pop('cart', None)
    return redirect(url_for('home_page'))


# Error Handlers
@website.errorhandler(404)
def handle_404(error):
    return render_template('Error.html',
                           error_code=404,
                           error_title='Page Not Found',
                           error_message='Sorry, the page you\'re looking for doesn\'t exist.',
                           error_details='The URL might be incorrect or the page may have been removed.',
                           current_user=session.get('full_name')), 404


@website.errorhandler(500)
def handle_500(error):
    return render_template('Error.html',
                           error_code=500,
                           error_title='Server Error',
                           error_message='Oops! Something went wrong on our end.',
                           error_details='Our team has been notified. Please try again later.',
                           current_user=session.get('full_name')), 500


@website.errorhandler(403)
def handle_403(error):
    return render_template('Error.html',
                           error_code=403,
                           error_title='Access Forbidden',
                           error_message='You don\'t have permission to access this resource.',
                           error_details='If you believe this is a mistake, please contact support.',
                           current_user=session.get('full_name')), 403


@website.errorhandler(400)
def handle_400(error):
    return render_template('Error.html',
                           error_code=400,
                           error_title='Bad Request',
                           error_message='The request could not be understood by the server.',
                           error_details='Please check your input and try again.',
                           current_user=session.get('full_name')), 400


if __name__ == "__main__":
   print("\n\033[1;95m- LOADING... -\033[0m\n")
   website.run(debug=True, port=5000)