import os
import pymongo
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from order import Order
from datetime import datetime, timezone
from dotenv import load_dotenv
# app.py (TOP of file)
import os, ssl, certifi
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

# ensure libs that use the stdlib ssl module also use certifi
ssl_ctx = ssl.create_default_context(cafile=certifi.where())
ssl._create_default_https_context = lambda: ssl_ctx

load_dotenv(".env")

app = Flask(__name__)
CORS(app)

client = MongoClient(os.getenv('MONGO_ORDERS'))
db = client["TapIt"]
orders = db["ORDERS"]
orderNumbers = db["ORDER_NUMBERS"]

@app.route("/api/order_complete", methods=["POST"])
def order_complete():
    data = request.json
    if not data:
        return jsonify({"message": "Error with request"}), 400

    name = data.get("name")
    phoneNumber = data.get("phoneNumber")
    email = data.get("email")
    url = data.get("url")
    numCards = int(data.get("numCards"))
    paymentMethod = data.get("paymentMethod")
    deliveryMethod = data.get("delivery")
    note = data.get("note")

    # if user selected delivery
    street = data.get("street")
    city = data.get("city")
    state = data.get("state")
    zipCode = data.get("zip")

    if not name:
        return jsonify({"message": "Missing firstName"}), 400
    elif not phoneNumber:
        return jsonify({"message": "Missing phoneNumber"}), 400
    elif not email:
        return jsonify({"message": "Missing email"}), 400
    elif not url:
        return jsonify({"message": "missing url"}), 400
    elif not numCards:
        return jsonify({"message": "Missing numCards"}), 400
    elif not paymentMethod:
        return jsonify({"message": "Missing paymentMethod"}), 400
    
    orderNum = get_next_order_number()
    if deliveryMethod != "Campus":
        total = (numCards * 9.99) + 5
        new_order = Order(orderNum, name, phoneNumber, email, url, numCards, paymentMethod, total, deliveryMethod, note, street, city, state, zipCode)
    else:
        total = numCards * 9.99
        new_order = Order(orderNum, name, phoneNumber, email, url, numCards, paymentMethod, total, note)
  
    try:
        send_receipt(email, orderNum, total, numCards, f"{name}")
        order_notify("info@tapitcard.org", orderNum, f"{name}", new_order, total, numCards)
    except Exception as e:
    # log but don’t fail the order creation
        print("Email error:", e)

    return jsonify({"message": "Order #{orderNum} placed successfully"}), 200

def get_next_order_number():
    doc = orderNumbers.find_one_and_update(
        {"_id": "orderNumber"},
        [  # <-- pipeline form
          {"$set": {
              "seq": { "$add": [ { "$ifNull": ["$seq", 1000] }, 1 ] }  # 1001 on first run
          }}
        ],
        upsert=True,
        return_document=pymongo.ReturnDocument.AFTER
    )
    return doc["seq"]

def send_receipt(to_email, orderNum, total, name, numCards, logo_url="https://tapitcard.org/logo.png"):
    preheader = f"Thanks for your order, {name} — order #{orderNum}."
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="x-apple-disable-message-reformatting">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TapIt – Order Confirmation</title>
</head>
<body style="margin:0; padding:0; background:#f4f7fa;">
  <!-- Hidden preview text -->
  <div style="display:none; visibility:hidden; opacity:0; color:transparent; height:0; width:0; overflow:hidden; mso-hide:all;">{preheader}</div>

  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#f4f7fa;">
    <tr>
      <td align="center" style="padding:20px;">
        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="max-width:650px; width:100%; background:#ffffff; border-radius:12px; overflow:hidden;">
          <!-- Header -->
          <tr>
            <td align="center" style="background:#0b0c10; color:#ffffff; padding:30px 20px;">
              <div style="font-size:28px; line-height:1.2; margin-bottom:10px;">🎉✨🎊</div>
              <img src="{logo_url}" width="120" alt="TapIt Logo" style="display:block; border:0; outline:none; text-decoration:none; height:auto; margin:0 auto 15px;">
              <h2 style="margin:0; font-family:Arial, Helvetica, sans-serif; font-size:22px; line-height:1.4; font-weight:700; color:#ffffff;">
                Thanks for your order, <span style="font-weight:700;">{name}</span>!
              </h2>
            </td>
          </tr>

          <!-- Content -->
          <tr>
            <td style="padding:25px; font-family:Arial, Helvetica, sans-serif; color:#333333;">
              <h1 style="margin:0 0 10px; font-size:24px; line-height:1.3; color:#3a86ff;">Connecting has never been easier 🚀</h1>
              <p style="margin:0 0 18px; font-size:16px; line-height:1.6;">
                Thank you for trusting <strong>TapItCard.org</strong>. You’re getting the fastest way to connect, and you’re helping us fund scholarships ❤️.
              </p>

              <!-- Order summary -->
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#f0f4ff; border-radius:8px;">
                <tr>
                  <td style="padding:20px; font-size:15px; line-height:1.6; color:#333333;">
                    <p style="margin:0 0 8px;"><span style="font-weight:bold; color:#000000;">Order #:</span> {orderNum}</p>
                    <p style="margin:0 0 8px;"><span style="font-weight:bold; color:#000000;">Date:</span> {datetime.now(timezone.utc).date().isoformat()}</p>
                    <p style="margin:0 0 8px;"><span style="font-weight:bold; color:#000000;">Number of Cards:</span> {numCards}</p>
                    <p style="margin:0;"><span style="font-weight:bold; color:#000000;">Total:</span> ${total} <em>(owed within 24 hours if unpaid)</em></p>
                    <p style="margin:0;"><span style="font-weight:bold; color:#000000;">If you opted for Zelle or Venmo:</span> $9.99 <em>Please pay amount to (818) 568-7294 via Zelle/Venmo</em></p>
                  </td>
                </tr>
              </table>

              <p style="margin:18px 0 12px; font-size:15px; line-height:1.6;">
                Check out our other TapIt NFC options:
                Tesla key cards 🔑🚗, LinkedIn/GitHub/Linktree/portfolio 🌐, social media 📱, and even prank cards 🤡.
              </p>

              <p style="margin:0 0 18px; text-align:center; font-size:18px; line-height:1.6;">
                💼 LinkedIn &nbsp; • &nbsp; 💻 GitHub &nbsp; • &nbsp; 🌐 Website &nbsp; • &nbsp; 😂 Pranks
              </p>

              <p style="margin:0; font-size:15px; line-height:1.6;">
                Please send your payment within <strong>24 hours</strong> via your chosen method.
                We’ll notify you again once your order is ready for pickup or shipping 📦.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td align="center" style="background:#fafafa; border-top:1px solid #dddddd; padding:15px;">
              <p style="margin:0; font-family:Arial, Helvetica, sans-serif; font-size:12px; line-height:1.6; color:#777777;">© 2025 TapItCard.org. All rights reserved.</p>
              <p style="margin:0; font-family:Arial, Helvetica, sans-serif; font-size:12px; line-height:1.6; color:#777777;">Tap smart. Tap fast. TapIt 🚀</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    message = Mail(
        from_email=("info@tapitcard.org", "TapIt Store"),
        to_emails=to_email,
        subject=f"Your receipt · Order #{orderNum}",
        html_content=html,
        # plain_text_content=(
        #     f"Thanks for your order, {name}!\n"
        #     f"Order #: {orderNum}\nDate: {datetime.now(timezone.utc).date().isoformat()}\n"
        #     "We’ll email you again when your order is ready for pickup or shipping."
        # ),
    )
    sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
    sg.send(message)

def order_notify(to_email, orderNum, name, order, total, numCards):
    html = f"""
    <h2>New order #{orderNum}</h2>
    <p><strong>Name:</strong> {name}</p>
    <p><strong>Date:</strong> {datetime.now(timezone.utc).date().isoformat()}</p>
    <p><strong>Number of Cards:</strong> {numCards}</p>
    <p><strong>Total:</strong> ${total}</p>
    <p>Delivery Method: {order.deliveryMethod}</p>
    <p>Street: {order.street}</p>
    <p>City: {order.city}</p>
    <p>State: {order.state}</p>
    <p>Zip Code: {order.zipCode}</p>
    """

    message = Mail(
        from_email=('info@tapitcard.org', 'TapIt Store'),
        to_emails=to_email,
        subject=f"New Order Placed · Order #{orderNum}",
        html_content=html
    )
    sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
    sg.send(message)



if __name__ == "__main__":
    app.run(debug=True)