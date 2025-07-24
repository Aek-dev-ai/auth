from flask import Flask, request, jsonify
import datetime
import os


app = Flask(__name__)

# قاعدة بيانات وهمية
hwid_db = {
    "e8f365275122603ef9ddca50c12018e6902e2c7e21cc369f1b4cfda53c6da1d8": {
        "expires": "2025-08-01"
    }
}

@app.route("/api/verify", methods=["POST"])
def verify():
    data = request.get_json()
    hwid = data.get("hwid")

    user = hwid_db.get(hwid)
    if not user:
        return jsonify({"success": False, "message": "HWID غير موجود"})

    expire_date = datetime.datetime.strptime(user["expires"], "%Y-%m-%d")
    if expire_date < datetime.datetime.now():
        return jsonify({"success": False, "message": "انتهت الصلاحية"})

    token = f"TOKEN-{hwid[:5]}-{expire_date.strftime('%Y%m%d')}"
    return jsonify({"success": True, "token": token})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

