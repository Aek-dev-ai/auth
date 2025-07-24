from flask import Flask, request, jsonify
import datetime

app = Flask(__name__)

# قاعدة بيانات وهمية
hwid_db = {
    "ABC123-HWID": {
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
    app.run()

