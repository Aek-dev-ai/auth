from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime
import hashlib
import json
import os
from threading import Lock

app = Flask(__name__)
CORS(app)  # Enable CORS for browser extensions

# JSON file path
TOKENS_FILE = "tokens.json"
# Thread lock for file operations
file_lock = Lock()

def load_tokens():
    """Load tokens from JSON file"""
    try:
        if os.path.exists(TOKENS_FILE):
            with open(TOKENS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Create empty file if it doesn't exist
            save_tokens({})
            return {}
    except Exception as e:
        print(f"❌ Error loading tokens: {e}")
        return {}

def save_tokens(tokens_data):
    """Save tokens to JSON file"""
    try:
        with file_lock:
            # Create backup before saving
            if os.path.exists(TOKENS_FILE):
                backup_file = f"{TOKENS_FILE}.backup"
                os.rename(TOKENS_FILE, backup_file)
            
            with open(TOKENS_FILE, 'w', encoding='utf-8') as f:
                json.dump(tokens_data, f, indent=2, ensure_ascii=False)
            
            # Remove backup if save was successful
            backup_file = f"{TOKENS_FILE}.backup"
            if os.path.exists(backup_file):
                os.remove(backup_file)
            
        return True
    except Exception as e:
        print(f"❌ Error saving tokens: {e}")
        # Restore backup if save failed
        backup_file = f"{TOKENS_FILE}.backup"
        if os.path.exists(backup_file):
            os.rename(backup_file, TOKENS_FILE)
        return False

def get_tokens():
    """Get current tokens from file"""
    return load_tokens()

def log_access_attempt(token, success, endpoint="", message=""):
    """Enhanced logging for access attempts"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "✅ SUCCESS" if success else "❌ FAILED"
    token_display = token[:20] + "..." if len(token) > 20 else token
    endpoint_display = f"[{endpoint}]" if endpoint else ""
    print(f"[{timestamp}] {status} {endpoint_display} - Token: {token_display} - {message}")

def is_token_expired(expire_date_str):
    """Check if a token is expired"""
    try:
        expire_date = datetime.datetime.strptime(expire_date_str, "%Y-%m-%d")
        current_date = datetime.datetime.now()
        return expire_date < current_date, expire_date
    except ValueError:
        return True, None

def calculate_days_remaining(expire_date_str):
    """Calculate days remaining until expiration"""
    try:
        expire_date = datetime.datetime.strptime(expire_date_str, "%Y-%m-%d")
        current_date = datetime.datetime.now()
        return (expire_date - current_date).days
    except ValueError:
        return 0

@app.route("/api/verify", methods=["POST"])
def verify():
    """Desktop application token verification endpoint"""
    try:
        data = request.get_json()
        if not data:
            log_access_attempt("UNKNOWN", False, "API", "No JSON data provided")
            return jsonify({
                "success": False, 
                "message": "بيانات غير صحيحة - لم يتم إرسال بيانات JSON"
            }), 400

        token = data.get("hwid")  # Desktop app sends as 'hwid'
        
        if not token:
            log_access_attempt("UNKNOWN", False, "API", "No token provided")
            return jsonify({
                "success": False, 
                "message": "لم يتم إرسال رمز التحقق"
            }), 400

        # Load tokens from file
        hwid_db = get_tokens()
        
        # Check if token exists in database
        user = hwid_db.get(token)
        if not user:
            log_access_attempt(token, False, "API", "Token not found in database")
            return jsonify({
                "success": False, 
                "message": "رمز التحقق غير موجود في النظام"
            }), 404

        # Check expiration date
        expired, expire_date = is_token_expired(user["expires"])
        if expired:
            log_access_attempt(token, False, "API", f"Token expired on {user['expires']}")
            return jsonify({
                "success": False, 
                "message": f"انتهت صلاحية الرخصة في {user['expires']}"
            }), 403

        if expire_date is None:
            log_access_attempt(token, False, "API", "Invalid date format")
            return jsonify({
                "success": False, 
                "message": "تاريخ انتهاء الصلاحية غير صحيح"
            }), 500

        # Calculate days until expiration
        days_until_expiry = calculate_days_remaining(user["expires"])
        
        log_access_attempt(token, True, "API", f"Verification successful - {days_until_expiry} days remaining")
        
        return jsonify({
            "success": True,
            "message": "تم التحقق بنجاح",
            "expires": user["expires"],
            "days_remaining": days_until_expiry
        }), 200

    except Exception as e:
        log_access_attempt("UNKNOWN", False, "API", f"Server error: {str(e)}")
        return jsonify({
            "success": False, 
            "message": "خطأ في الخادم"
        }), 500

@app.route("/verify-token", methods=["POST"])
def verify_token():
    """Browser extension token verification endpoint"""
    try:
        data = request.get_json()
        token = data.get("token") if data else None
        
        if not token:
            log_access_attempt("UNKNOWN", False, "EXT", "No token provided")
            return jsonify({
                "status": "invalid", 
                "reason": "token_missing"
            }), 400

        # Load tokens from file
        hwid_db = get_tokens()
        
        # Check if token exists in database
        user = hwid_db.get(token)
        if not user:
            log_access_attempt(token, False, "EXT", "Token not found in database")
            return jsonify({
                "status": "invalid", 
                "reason": "token_not_found"
            }), 200  # Return 200 for extension compatibility

        # Check expiration date
        expired, expire_date = is_token_expired(user["expires"])
        if expired:
            log_access_attempt(token, False, "EXT", f"Token expired on {user['expires']}")
            return jsonify({
                "status": "invalid", 
                "reason": "token_expired"
            }), 200

        if expire_date is None:
            log_access_attempt(token, False, "EXT", "Invalid date format")
            return jsonify({
                "status": "invalid", 
                "reason": "date_error"
            }), 200

        days_remaining = calculate_days_remaining(user["expires"])
        log_access_attempt(token, True, "EXT", f"Extension verification successful - {days_remaining} days remaining")
        
        return jsonify({
            "status": "valid",
            "expires": user["expires"]
        }), 200

    except Exception as e:
        log_access_attempt("UNKNOWN", False, "EXT", f"Extension server error: {str(e)}")
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500

@app.route("/api/register", methods=["POST"])
def register():
    """Register new hardware tokens"""
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

        # Validate expiration date format
        try:
            datetime.datetime.strptime(expires, "%Y-%m-%d")
        except ValueError:
            return jsonify({
                "success": False, 
                "message": "Invalid date format. Use YYYY-MM-DD"
            }), 400

        # Load current tokens
        hwid_db = get_tokens()
        
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
        
        # Save to file
        if not save_tokens(hwid_db):
            return jsonify({
                "success": False,
                "message": "Failed to save token to database"
            }), 500

        log_access_attempt(token, True, "REG", f"New token registered with expiry: {expires}")
        
        return jsonify({
            "success": True,
            "message": "Token registered successfully",
            "expires": expires
        }), 201

    except Exception as e:
        log_access_attempt("UNKNOWN", False, "REG", f"Registration error: {str(e)}")
        return jsonify({
            "success": False, 
            "message": f"Registration error: {str(e)}"
        }), 500

@app.route("/api/extend", methods=["POST"])
def extend_token():
    """Extend token expiration date"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "message": "No data provided"
            }), 400

        token = data.get("token")
        new_expires = data.get("expires")
        
        if not token or not new_expires:
            return jsonify({
                "success": False,
                "message": "Token and new expiration date required"
            }), 400

        # Validate date format
        try:
            datetime.datetime.strptime(new_expires, "%Y-%m-%d")
        except ValueError:
            return jsonify({
                "success": False,
                "message": "Invalid date format. Use YYYY-MM-DD"
            }), 400

        # Load current tokens
        hwid_db = get_tokens()
        
        # Check if token exists
        if token not in hwid_db:
            return jsonify({
                "success": False,
                "message": "Token not found"
            }), 404

        # Update expiration date
        old_expires = hwid_db[token]["expires"]
        hwid_db[token]["expires"] = new_expires
        
        # Save to file
        if not save_tokens(hwid_db):
            return jsonify({
                "success": False,
                "message": "Failed to update token in database"
            }), 500
        
        log_access_attempt(token, True, "EXT", f"Token expiry extended from {old_expires} to {new_expires}")
        
        return jsonify({
            "success": True,
            "message": "Token expiration extended successfully",
            "old_expires": old_expires,
            "new_expires": new_expires
        }), 200

    except Exception as e:
        log_access_attempt("UNKNOWN", False, "EXT", f"Extension error: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Extension error: {str(e)}"
        }), 500

@app.route("/api/delete", methods=["POST"])
def delete_token():
    """Delete a token from the database"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "message": "No data provided"
            }), 400

        token = data.get("token")
        
        if not token:
            return jsonify({
                "success": False,
                "message": "Token required"
            }), 400

        # Load current tokens
        hwid_db = get_tokens()
        
        # Check if token exists
        if token not in hwid_db:
            return jsonify({
                "success": False,
                "message": "Token not found"
            }), 404

        # Delete token
        del hwid_db[token]
        
        # Save to file
        if not save_tokens(hwid_db):
            return jsonify({
                "success": False,
                "message": "Failed to delete token from database"
            }), 500
        
        log_access_attempt(token, True, "DEL", "Token deleted successfully")
        
        return jsonify({
            "success": True,
            "message": "Token deleted successfully"
        }), 200

    except Exception as e:
        log_access_attempt("UNKNOWN", False, "DEL", f"Deletion error: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Deletion error: {str(e)}"
        }), 500

@app.route("/api/status", methods=["GET"])
def status():
    """Get server status and statistics"""
    hwid_db = get_tokens()
    total_tokens = len(hwid_db)
    active_tokens = 0
    expired_tokens = 0
    expiring_soon = 0  # Tokens expiring in 7 days
    current_date = datetime.datetime.now()
    
    for token, user in hwid_db.items():
        expired, expire_date = is_token_expired(user["expires"])
        if expired:
            expired_tokens += 1
        else:
            active_tokens += 1
            if expire_date:
                days_remaining = (expire_date - current_date).days
                if days_remaining <= 7:
                    expiring_soon += 1
    
    return jsonify({
        "server_status": "online",
        "total_tokens": total_tokens,
        "active_tokens": active_tokens,
        "expired_tokens": expired_tokens,
        "expiring_soon": expiring_soon,
        "server_time": current_date.strftime("%Y-%m-%d %H:%M:%S"),
        "database_file": TOKENS_FILE
    }), 200

@app.route("/api/health", methods=["GET"])
def health():
    """Simple health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "version": "2.1.0",
        "database": "JSON file"
    }), 200

@app.route("/api/tokens", methods=["GET"])
def list_tokens():
    """List all tokens with their status (admin endpoint)"""
    hwid_db = get_tokens()
    tokens_info = []
    current_date = datetime.datetime.now()
    
    for token, user in hwid_db.items():
        expired, expire_date = is_token_expired(user["expires"])
        days_remaining = calculate_days_remaining(user["expires"]) if not expired else 0
        
        tokens_info.append({
            "token": token[:20] + "...",  # Mask token for security
            "expires": user["expires"],
            "status": "expired" if expired else "active",
            "days_remaining": days_remaining
        })
    
    return jsonify({
        "tokens": tokens_info,
        "count": len(tokens_info)
    }), 200

@app.route("/api/reload", methods=["POST"])
def reload_tokens():
    """Reload tokens from file (admin endpoint)"""
    try:
        hwid_db = load_tokens()
        return jsonify({
            "success": True,
            "message": "Tokens reloaded successfully",
            "count": len(hwid_db)
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to reload tokens: {str(e)}"
        }), 500

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
    
    # Load tokens on startup
    initial_tokens = load_tokens()
    
    print("=" * 60)
    print("🚀 App'services Authentication Server v2.1")
    print("=" * 60)
    print(f"🌐 Server starting on host: 0.0.0.0")
    print(f"🔌 Server starting on port: {port}")
    print(f"💾 Database file: {TOKENS_FILE}")
    print(f"📊 Total registered tokens: {len(initial_tokens)}")
    print(f"🕒 Server time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n📋 Available endpoints:")
    print("  📱 POST /api/verify      - Desktop app token verification")
    print("  🌐 POST /verify-token    - Browser extension token verification")
    print("  ➕ POST /api/register    - Register new token")
    print("  ⏰ POST /api/extend      - Extend token expiration")
    print("  🗑️  POST /api/delete     - Delete token")
    print("  🔄 POST /api/reload      - Reload tokens from file")
    print("  📈 GET  /api/status      - Server statistics")
    print("  💚 GET  /api/health      - Health check")
    print("  📝 GET  /api/tokens      - List all tokens (admin)")
    print("=" * 60)
    print("🔄 CORS enabled for browser extensions")
    print("💾 JSON database with automatic backup")
    print("🔐 Enhanced logging and error handling active")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=False)
