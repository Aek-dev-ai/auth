from flask import Flask, request, jsonify
import datetime
import hashlib
import json

app = Flask(__name__)

# Simplified database to store only hardware tokens and expiration dates
hwid_db = {
    # Example token format: AST_[32_CHAR_HASH]
    "AST_288E88324EDE87BF_13_04DB2EDC": {
        "expires": "2025-09-27"
    },
    # Add more tokens as needed
    "AST_ACF7B32BE76F5819_13_60488A74": {
        "expires": "2025-09-25"
    },
    "AST_CB001A4628F30E28_13_9D333AFA": {
        "expires": "2025-09-16"
    },
    "AST_279929305AC764388C009AC93A53BE53": {
        "expires": "2025-09-16"
    },
    "AST_1E9CABDF356C78AA_13_7CBC7363": {
        "expires": "2025-09-25"
    },
    "AST_60F6C05E2C980DEF_13_065937A9": {
        "expires": "2025-09-29"
    }
}

def log_access_attempt(token, success, message=""):
    """Log access attempts for monitoring"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "SUCCESS" if success else "FAILED"
    print(f"[{timestamp}] {status} - Token: {token[:20]}... - {message}")

@app.route("/api/verify", methods=["POST"])
def verify():
    try:
        data = request.get_json()
        if not data:
            log_access_attempt("UNKNOWN", False, "No JSON data provided")
            return jsonify({
                "success": False, 
                "message": "بيانات غير صحيحة - لم يتم إرسال بيانات JSON"
            }), 400

        token = data.get("hwid")  # Client still sends as 'hwid' for compatibility
        
        if not token:
            log_access_attempt("UNKNOWN", False, "No token provided")
            return jsonify({
                "success": False, 
                "message": "لم يتم إرسال رمز التحقق"
            }), 400

        # Check if token exists in database
        user = hwid_db.get(token)
        if not user:
            log_access_attempt(token, False, "Token not found in database")
            return jsonify({
                "success": False, 
                "message": "رمز التحقق غير موجود في النظام"
            }), 404

        # Check expiration date
        try:
            expire_date = datetime.datetime.strptime(user["expires"], "%Y-%m-%d")
            current_date = datetime.datetime.now()
            
            if expire_date < current_date:
                log_access_attempt(token, False, "Token expired")
                return jsonify({
                    "success": False, 
                    "message": f"انتهت صلاحية الرخصة في {user['expires']}"
                }), 403
                
        except ValueError as e:
            log_access_attempt(token, False, f"Invalid date format: {e}")
            return jsonify({
                "success": False, 
                "message": "تاريخ انتهاء الصلاحية غير صحيح"
            }), 500

        # Calculate days until expiration
        days_until_expiry = (expire_date - current_date).days
        
        log_access_attempt(token, True, f"Verification successful - {days_until_expiry} days remaining")
        
        return jsonify({
            "success": True,
            "message": "تم التحقق بنجاح",
            "expires": user["expires"],
            "days_remaining": days_until_expiry
        }), 200

    except Exception as e:
        log_access_attempt("UNKNOWN", False, f"Server error: {str(e)}")
        return jsonify({
            "success": False, 
            "message": "خطأ في الخادم"
        }), 500

@app.route("/api/register", methods=["POST"])
def register():
    """New endpoint to register hardware tokens"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False, 
                "message": "No data provided"
            }), 400

        token = data.get("token")
        expires = data.get("expires", "2025-12-31")  # Default expiration
        
        if not token:
            return jsonify({
                "success": False, 
                "message": "No token provided"
            }), 400

        # Check if token already exists
        if token in hwid_db:
            return jsonify({
                "success": False, 
                "message": "Token already registered"
            }), 409

        # Register new token
        hwid_db[token] = {
            "expires": expires
        }

        log_access_attempt(token, True, "New token registered")
        
        return jsonify({
            "success": True,
            "message": "Token registered successfully",
            "expires": expires
        }), 201

    except Exception as e:
        return jsonify({
            "success": False, 
            "message": f"Registration error: {str(e)}"
        }), 500

@app.route("/api/status", methods=["GET"])
def status():
    """Get server status and statistics"""
    total_tokens = len(hwid_db)
    active_tokens = 0
    expired_tokens = 0
    current_date = datetime.datetime.now()
    
    for token, user in hwid_db.items():
        try:
            expire_date = datetime.datetime.strptime(user["expires"], "%Y-%m-%d")
            if expire_date >= current_date:
                active_tokens += 1
            else:
                expired_tokens += 1
        except:
            expired_tokens += 1
    
    return jsonify({
        "server_status": "online",
        "total_tokens": total_tokens,
        "active_tokens": active_tokens,
        "expired_tokens": expired_tokens,
        "server_time": current_date.strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route("/api/health", methods=["GET"])
def health():
    """Simple health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat()
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "message": "API endpoint not found"
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "success": False,
        "message": "Method not allowed"
    }), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "message": "Internal server error"
    }), 500

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    
    print("="*50)
    print("App'services Authentication Server")
    print("="*50)
    print(f"Server starting on port {port}")
    print(f"Total registered tokens: {len(hwid_db)}")
    print("Available endpoints:")
    print("  POST /api/verify - Verify hardware token")
    print("  POST /api/register - Register new token")
    print("  GET  /api/status - Get server statistics")
    print("  GET  /api/health - Health check")
    print("="*50)
    
    app.run(host='0.0.0.0', port=port, debug=False)










