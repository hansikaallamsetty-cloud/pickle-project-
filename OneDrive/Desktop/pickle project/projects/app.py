"""
Homemade Pickles & Snacks – Taste the Best
Flask E-Commerce Application
Designed for local development with future AWS DynamoDB / EC2 integration.
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import json
import os
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = "pickle-secret-key-change-in-production"

# ─────────────────────────────────────────────
# DATA LAYER
# In-memory store — swap with DynamoDB later.
# DynamoDB tables: Products | Users | Orders | Subscriptions
# ─────────────────────────────────────────────

PRODUCTS = {
    "p001": {
        "id": "p001", "name": "Mango Pickle", "category": "pickles",
        "price": 149, "stock": 30, "rating": 4.8,
        "desc": "Sun-dried raw mangoes marinated in mustard oil & hand-ground spices. Tangy, bold, unforgettable.",
        "short": "Classic tangy raw mango pickle",
        "img": "mango_pickle.png", "weight": "250g"
    },
    "p002": {
        "id": "p002", "name": "Lemon Pickle", "category": "pickles",
        "price": 129, "stock": 25, "rating": 4.6,
        "desc": "Whole lemons slow-cured in turmeric, chilli and sea salt. A sharp, citrusy punch with every bite.",
        "short": "Tangy whole-lemon salt-cured pickle",
        "img": "lemon_pickle.png", "weight": "250g"
    },
    "p003": {
        "id": "p003", "name": "Gongura Pickle", "category": "pickles",
        "price": 169, "stock": 20, "rating": 4.9,
        "desc": "Sorrel leaves blended with fiery red chillies and sesame — Andhra's pride in a jar.",
        "short": "Andhra-style sorrel leaf pickle",
        "img": "gongura_pickle.png", "weight": "250g"
    },
    "p004": {
        "id": "p004", "name": "Garlic Pickle", "category": "pickles",
        "price": 159, "stock": 18, "rating": 4.7,
        "desc": "Whole garlic cloves tempered in chilli oil and vinegar. Bold, aromatic and deeply savory.",
        "short": "Spicy whole-garlic oil pickle",
        "img": "garlic_pickle.png", "weight": "250g"
    },
    "p005": {
        "id": "p005", "name": "Mixed Vegetable Pickle", "category": "pickles",
        "price": 139, "stock": 22, "rating": 4.5,
        "desc": "Carrot, cauliflower, turnip & green chilli mixed in a lip-smacking spiced mustard base.",
        "short": "Colorful medley of crunchy vegetables",
        "img": "mixed_pickle.png", "weight": "300g"
    },
    "p006": {
        "id": "p006", "name": "Amla Pickle", "category": "pickles",
        "price": 119, "stock": 28, "rating": 4.4,
        "desc": "Indian gooseberry preserved with nigella seeds and fenugreek. Tangy, healthy, traditional.",
        "short": "Gooseberry pickle with nigella seeds",
        "img": "amla_pickle.png", "weight": "250g"
    },
    "p007": {
        "id": "p007", "name": "Murukku", "category": "snacks",
        "price": 89, "stock": 40, "rating": 4.7,
        "desc": "Crispy rice-flour spirals seasoned with cumin and sesame — fried to a perfect golden crunch.",
        "short": "Crispy spiral rice-flour snack",
        "img": "murukku.png", "weight": "200g"
    },
    "p008": {
        "id": "p008", "name": "Banana Chips", "category": "snacks",
        "price": 79, "stock": 50, "rating": 4.6,
        "desc": "Thin-sliced raw bananas fried in coconut oil and dusted with black pepper. Kerala-style irresistible.",
        "short": "Coconut-oil fried Kerala banana chips",
        "img": "banana_chips.png", "weight": "150g"
    },
    "p009": {
        "id": "p009", "name": "Chakli", "category": "snacks",
        "price": 99, "stock": 35, "rating": 4.5,
        "desc": "Maharashtrian deep-fried spirals made from rice, urad dal and a blend of warming spices.",
        "short": "Maharashtrian spiced spiral snack",
        "img": "chakli.png", "weight": "200g"
    },
    "p010": {
        "id": "p010", "name": "Mixture", "category": "snacks",
        "price": 69, "stock": 60, "rating": 4.3,
        "desc": "A festive medley of sev, peanuts, curry leaves, fried lentils and spiced puffed rice.",
        "short": "Festive spiced fried mixture",
        "img": "mixture.png", "weight": "200g"
    },
    "p011": {
        "id": "p011", "name": "Masala Peanuts", "category": "snacks",
        "price": 59, "stock": 70, "rating": 4.4,
        "desc": "Crunchy peanuts coated in a fiery besan-spice batter and deep-fried to perfection.",
        "short": "Besan-coated spicy crunchy peanuts",
        "img": "masala_peanuts.png", "weight": "150g"
    },
    "p012": {
        "id": "p012", "name": "Ribbon Pakoda", "category": "snacks",
        "price": 85, "stock": 45, "rating": 4.6,
        "desc": "Long flat ribbon-shaped fried snack made with rice flour and black sesame — light yet satisfying.",
        "short": "Crispy ribbon-shaped rice-flour pakoda",
        "img": "ribbon_pakoda.png", "weight": "200g"
    },
}

# Recommendation map: if user adds a pickle → suggest these snacks (and vice versa)
RECOMMENDATIONS = {
    "pickles": ["p007", "p008", "p009"],  # Murukku, Banana Chips, Chakli
    "snacks":  ["p001", "p002", "p003"],  # Mango, Lemon, Gongura Pickle
}

# In-memory user store — replace with DynamoDB Users table
USERS = {}

# In-memory order store — replace with DynamoDB Orders table
ORDERS = {}

# In-memory subscription store — replace with DynamoDB Subscriptions table
SUBSCRIPTIONS = {}

# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def get_cart():
    """Return the current session cart dict {product_id: quantity}."""
    return session.get("cart", {})

def get_cart_total():
    cart = get_cart()
    total = 0
    for pid, qty in cart.items():
        if pid in PRODUCTS:
            total += PRODUCTS[pid]["price"] * qty
    return total

def get_cart_count():
    return sum(get_cart().values())

def get_recommendations(cart):
    """Return recommended products based on cart contents."""
    categories_in_cart = {PRODUCTS[pid]["category"] for pid in cart if pid in PRODUCTS}
    rec_ids = set()
    for cat in categories_in_cart:
        rec_ids.update(RECOMMENDATIONS.get(cat, []))
    # Remove items already in cart
    rec_ids -= set(cart.keys())
    return [PRODUCTS[pid] for pid in rec_ids if pid in PRODUCTS]

# Inject cart count into all templates
@app.context_processor
def inject_globals():
    return {
        "cart_count": get_cart_count(),
        "current_user": session.get("user"),
    }

# ─────────────────────────────────────────────
# ROUTES — PAGES
# ─────────────────────────────────────────────

@app.route("/")
def index():
    """Home / landing page."""
    featured = ["p001", "p003", "p007", "p008"]
    featured_products = [PRODUCTS[pid] for pid in featured if pid in PRODUCTS]
    return render_template("index.html", featured=featured_products)


@app.route("/products")
def products():
    """Product catalog with category filtering."""
    category = request.args.get("category", "all")
    if category == "all":
        product_list = list(PRODUCTS.values())
    else:
        product_list = [p for p in PRODUCTS.values() if p["category"] == category]
    return render_template("products.html", products=product_list, active_category=category)


@app.route("/product/<pid>")
def product_detail(pid):
    """Single product detail page."""
    product = PRODUCTS.get(pid)
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("products"))
    # Related products (same category, excluding current)
    related = [p for p in PRODUCTS.values()
                if p["category"] == product["category"] and p["id"] != pid][:3]
    return render_template("product_detail.html", product=product, related=related)


# ─────────────────────────────────────────────
# ROUTES — AUTH
# ─────────────────────────────────────────────

@app.route("/register", methods=["GET", "POST"])
def register():
    """User registration. Replace USERS dict with DynamoDB Users table later."""
    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("All fields are required.", "error")
            return render_template("register.html")

        if email in USERS:
            flash("Email already registered. Please login.", "error")
            return render_template("register.html")

        USERS[email] = {
            "id": str(uuid.uuid4()),
            "name": name,
            "email": email,
            "password": password,   # Hash in production!
            "created_at": datetime.now().isoformat(),
        }
        flash("Account created! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """User login."""
    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = USERS.get(email)
        if user and user["password"] == password:
            session["user"] = {"id": user["id"], "name": user["name"], "email": email}
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid email or password.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Logout and clear session."""
    session.clear()
    flash("You've been logged out.", "info")
    return redirect(url_for("index"))


# ─────────────────────────────────────────────
# ROUTES — CART
# ─────────────────────────────────────────────

@app.route("/cart")
def cart():
    """Shopping cart page."""
    cart_data = get_cart()
    cart_items = []
    for pid, qty in cart_data.items():
        if pid in PRODUCTS:
            p = PRODUCTS[pid].copy()
            p["qty"] = qty
            p["subtotal"] = p["price"] * qty
            cart_items.append(p)
    total = get_cart_total()
    recommendations = get_recommendations(cart_data)
    return render_template("cart.html", cart_items=cart_items,
                           total=total, recommendations=recommendations)


@app.route("/cart/add/<pid>", methods=["POST"])
def add_to_cart(pid):
    """Add a product to cart (or increment quantity)."""
    if pid not in PRODUCTS:
        flash("Product not found.", "error")
        return redirect(url_for("products"))

    product = PRODUCTS[pid]
    cart = get_cart()
    qty = int(request.form.get("qty", 1))
    current_qty = cart.get(pid, 0)

    if current_qty + qty > product["stock"]:
        flash(f"Only {product['stock']} units available.", "error")
    else:
        cart[pid] = current_qty + qty
        session["cart"] = cart
        flash(f"'{product['name']}' added to cart!", "success")

    # Return to referring page
    return redirect(request.referrer or url_for("products"))


@app.route("/cart/update/<pid>", methods=["POST"])
def update_cart(pid):
    """Update quantity of a cart item."""
    cart = get_cart()
    qty = int(request.form.get("qty", 1))
    if qty <= 0:
        cart.pop(pid, None)
    elif pid in PRODUCTS:
        cart[pid] = min(qty, PRODUCTS[pid]["stock"])
    session["cart"] = cart
    return redirect(url_for("cart"))


@app.route("/cart/remove/<pid>")
def remove_from_cart(pid):
    """Remove a product from cart."""
    cart = get_cart()
    cart.pop(pid, None)
    session["cart"] = cart
    flash("Item removed from cart.", "info")
    return redirect(url_for("cart"))


# ─────────────────────────────────────────────
# ROUTES — CHECKOUT & ORDERS
# ─────────────────────────────────────────────

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    """Checkout page — shows order summary and simulates payment."""
    if not session.get("user"):
        flash("Please login to checkout.", "error")
        return redirect(url_for("login"))

    cart_data = get_cart()
    if not cart_data:
        flash("Your cart is empty.", "error")
        return redirect(url_for("cart"))

    cart_items = []
    for pid, qty in cart_data.items():
        if pid in PRODUCTS:
            p = PRODUCTS[pid].copy()
            p["qty"] = qty
            p["subtotal"] = p["price"] * qty
            cart_items.append(p)

    total = get_cart_total()

    if request.method == "POST":
        # Simulate payment & deduct inventory
        order_id = "ORD-" + str(uuid.uuid4())[:8].upper()
        order = {
            "id": order_id,
            "user": session["user"],
            "items": cart_items,
            "total": total,
            "status": "Confirmed",
            "placed_at": datetime.now().strftime("%d %b %Y, %I:%M %p"),
            "address": request.form.get("address", ""),
        }
        ORDERS[order_id] = order

        # Deduct stock (inventory update simulation)
        for pid, qty in cart_data.items():
            if pid in PRODUCTS:
                PRODUCTS[pid]["stock"] = max(0, PRODUCTS[pid]["stock"] - qty)

        # Clear cart
        session["cart"] = {}

        flash(f"Order {order_id} placed successfully! 🎉", "success")
        return render_template("order_success.html", order=order)

    return render_template("checkout.html", cart_items=cart_items, total=total)


# ─────────────────────────────────────────────
# ROUTES — SUBSCRIPTIONS
# ─────────────────────────────────────────────

@app.route("/subscribe", methods=["POST"])
def subscribe():
    """Simulate subscription creation."""
    if not session.get("user"):
        flash("Please login to subscribe.", "error")
        return redirect(url_for("login"))

    plan = request.form.get("plan")
    sub_id = "SUB-" + str(uuid.uuid4())[:6].upper()
    SUBSCRIPTIONS[sub_id] = {
        "id": sub_id,
        "user": session["user"],
        "plan": plan,
        "created_at": datetime.now().isoformat(),
        "status": "Active",
    }
    flash(f"Subscribed to '{plan}'! Your box will arrive soon. 🥒", "success")
    return redirect(url_for("index"))


# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
