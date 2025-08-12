from flask import Flask, request, jsonify
import datetime

app = Flask(__name__)

# قاعدة بيانات HWID
hwid_db = {
    "34a37ee231d2b456967f731c824db3fef1bbbb42c0c866c7d4ee316ffdf737cc": {
        "expires": "2025-09-27"
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
    },
        "8e20d083856e2707156b1106afdbe319ed0a060c9fb46a6038bb19e96781683d": {
        "expires": "2025-09-10"
    },
        "a26ad2e2edd0d5434c50ff06d37dfdb8abbc50166cf769fe93c6e50531ea03c5": {
        "expires": "2025-09-09"
    },
        "0430a19babd27fbbdc25f5897d90af66bb14a49caca86b1c0829b23f5f0ecb3d": {
        "expires": "2025-09-09"
    },
        "a288ba73013e32b6ef977540bbeba5788d9c95fa2846a04efda80314c1f916e3": {
        "expires": "2025-09-09"
    },  
        "5bfda8ef00c6f0814ff4ae9fee2d6888e1a01eaa9dd041e3cbfd0940eb7f2b7f": {
        "expires": "2025-09-09"
    },
        "ce80f95f1e2d642797d89eaacf6bf87143de086861f1861b96a2a03fd1b9208a": {
        "expires": "2025-09-09"
    },  
       "2a01520b17ea5b06bc560570eb600be85fab24ad34ce4acac48435d486b63538": {
        "expires": "2025-09-11"
    },
       "dfca4e97d1bdb95446232816a8e8a9779f8f34bdf546d08fe4d06cab5a6250c3": {
        "expires": "2025-09-11"
    },
      "6436ecb5c5deab50039ab1e0518e9c93e44a181452b58fa8b8e740670a3d6a31": {
        "expires": "2025-09-11"
    },
      "379d36340c50d01abcdef7f07398b8e19c2457cd7c98d47dc41a3f2bee2237a5": {
        "expires": "2025-09-11"
    },
      "d0e830a04bb599827ad00532301e24aa2d6a6bffe77afaafb314122ddc79711b": {
        "expires": "2025-09-11"
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












