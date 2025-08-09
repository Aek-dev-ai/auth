from flask import Flask, request, jsonify
import datetime

app = Flask(__name__)

# قاعدة بيانات HWID
hwid_db = {
    "e8f365275122603ef9ddca50c12018e6902e2c7e21cc369f1b4cfda53c6da1d8": {
        "expires": "2025-08-27"
    },
        "5a491925a4737511524b7428ceaa9c015e7a238a7bfa2af2390fa615dc277c91": {
        "expires": "2025-09-09"
    },
        "d401dcf11fdc70069a79f0dcf6b92d488044bf25b07910d06d7d10ccf7802c0c": {
        "expires": "2025-09-09"
    },
        "d508b5f7297f27d7ff0cb2e48bf053ee4c706a39bdd7410b0d416708ca20d486": {
        "expires": "2025-09-09"
    },
        "1553f5a133eea27922c5ab7cef59ec14a439e119bbaaecf7ab5d94b59e16708a": {
        "expires": "2025-09-09"
    },
        "9887cf12d902e331783056df967afe25f0c19ce5e79ee772bea9c820ca88b42a": {
        "expires": "2025-09-09"
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
    return jsonify({
        "success": True,
        "message": "تم التحقق بنجاح",
        "expires": user["expires"]  # Explicitly include expiration date
    })

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

