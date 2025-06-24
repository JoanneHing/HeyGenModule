from dotenv import load_dotenv
load_dotenv()

import os
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import webbrowser
from datetime import datetime, timedelta
import uuid
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Start flask app
app = Flask(__name__)
# Enable CORS
CORS(app)

# Load environment variables
HEYGEN_API_KEY = os.getenv('HEYGEN_API_KEY')

# If the Heygen API key is not set, raise an error
if not HEYGEN_API_KEY:
    raise ValueError("HEYGEN_API_KEY environment variable is not set.")

# Define the base URL for the Heygen API
HEYGEN_API_BASE_URL = "https://api.heygen.com/v1"

# Set a default timeout for sessions
SESSION_TIMEOUT = timedelta(minutes=60)

# Use dictionary to store sessions details
sessions = {}

class SessionManager:
    """Session management to track active sessions"""
    @staticmethod
    def create_session(session_data):
        """Create a new session with the provided session data."""
        # Generate a unique session ID and store session details
        session_id = str(uuid.uuid4())
        sessions[session_id] = {
            **session_data,
            'created_at': datetime.now(),
            'last_accessed': datetime.now()
        }
        return session_id
    
    @staticmethod
    def get_session(session_id):
        """Get session details by session ID"""
        session = sessions.get(session_id)
        # Check if session exists
        if not session:
            return None
        
        # Check if session is expired
        if datetime.now() - session['last_accessed'] > SESSION_TIMEOUT:
            SessionManager.cleanup_session(session_id)
            return None
        
        # Update last accessed time
        session['last_accessed'] = datetime.now()
        return session
    
    @staticmethod
    def cleanup_session(session_id):
        """Clean up a session by session ID"""
        sessions.pop(session_id, None)

    @staticmethod
    def cleanup_expired_sessions():
        """Clean up all expired sessions"""
        expired_sessions = [
            session_id for session_id, session in sessions.items()
            if datetime.now() - session['last_accessed'] > SESSION_TIMEOUT
        ]

        for session_id in expired_sessions:
            SessionManager.cleanup_session(session_id)
            logger.info(f"Session {session_id} has been cleaned up due to inactivity.")

def heygen_api_request(endpoint, method='POST', data=None):
    """Make a request to the Heygen API."""
    url = f"{HEYGEN_API_BASE_URL}/{endpoint}"
    headers = {
        "x-api-key": HEYGEN_API_KEY,
        "Content-Type": "application/json"
    }

    #logging for debugging
    logger.info(f"Making {method} request to: {url}")
    logger.info(f"Headers: {dict(headers)}")  # Log headers (API key will be masked)
    logger.info(f"Request payload: {json.dumps(data, indent=2) if data else 'None'}")

    try:
        if method == 'POST':
            response = requests.post(url, headers=headers, json=data, timeout=30)
        elif method == 'GET':
            response = requests.get(url, headers=headers, params=data, timeout=30)
        else:
            raise ValueError("Unsupported HTTP method.")

        # Log response details
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        
        # Get detailed error from response
        try:
            response_json = response.json()
            logger.info(f"Response body: {json.dumps(response_json, indent=2)}")
        except:
            logger.info(f"Response text: {response.text}")

        response.raise_for_status()
        return response.json(), response.status_code
    
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error: {e}")
        try:
            error_response = response.json()
            logger.error(f"Error response from Heygen: {json.dumps(error_response, indent=2)}")
            return error_response, response.status_code
        except:
            logger.error(f"Error response text: {response.text}")
            return {"error": f"HTTP {response.status_code}: {response.text}"}, response.status_code
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Request Error: {e}")
        return {"error": str(e)}, 500
    
# Error handlers     
@app.errorhandler(400)
def bad_request(error):
    """Handle 400 Bad Request errors."""
    logger.error(f"Bad request: {error}")
    return jsonify({"error": "Bad request"}), 400

@app.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors."""
    logger.error(f"Not found: {error}")
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_server_error(error):
    """Handle 500 Internal Server Error."""
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

# Define the API endpoints
@app.route('/api/avatar/start', methods=['POST'])
def start_session():
    """Start a new avatar streaming session."""
    try:
        logger.info("Received request to start a new avatar session.")
        
        # Validate request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
        
        # Updated with proper avatar_id and quality parameters
        avatar_id = data.get('avatar_id', "Marianne_Chair_Sitting_public")
        quality = data.get('quality', "medium")

        if not avatar_id or not quality:
            return jsonify({"error": "Missing required parameters"}), 400
        
        logger.info(f"Starting session with avatar_id: {avatar_id}, quality: {quality}")

        # Step 1: Create a new streaming session
        payload = {
            "avatar_id": avatar_id,
            "quality": quality,
            "version": "v2"
        }

        result, status_code = heygen_api_request("streaming.new", method='POST', data=payload)

        if status_code != 200:
            logger.error(f"Failed to create session: {result}")
            return jsonify(result), status_code
        
        if "data" not in result:
            logger.error(f"Invalid response from Heygen API: {result}")
            return jsonify({"error": "Invalid response from Heygen API"}), 500
        
        session_data = result["data"]
        logger.info(f"Session created successfully: {session_data}")

        # Step 2: Create API token for backend operations (optional - only needed for additional backend calls)
        api_token = None
        try:
            token_result, token_status = heygen_api_request("streaming.create_token", method='POST')
            if token_status == 200 and "data" in token_result:
                api_token = token_result["data"]["token"]
                logger.info("API token created successfully")
            else:
                logger.warning(f"Could not create API token: {token_result}")
        except Exception as e:
            logger.warning(f"API token creation failed (non-critical): {e}")
            # Continue without API token - the access_token is sufficient for streaming
        
        # Step 3: Start the avatar session
        start_payload = {
            "session_id": session_data["session_id"]
        }

        start_result, start_status = heygen_api_request("streaming.start", method='POST', data=start_payload)

        if start_status != 200:
            logger.error(f"Failed to start session: {start_result}")
            return jsonify({"error": "Failed to start avatar session", "details": start_result}), start_status

        logger.info(f"Session started successfully: {start_result}")

        # Step 4: Store complete session data
        complete_session_data = {
            **session_data,
            "api_token": api_token,
            "quality": quality,
            "avatar_id": avatar_id,
            "status": "started"
        }

        # Store session details with SessionManager
        local_session_id = SessionManager.create_session(complete_session_data)
        logger.info(f"Session stored with local ID: {local_session_id}")

        # Step 5: Prepare response with all necessary data
        response = {
            "local_session_id": local_session_id,
            "session_id": session_data["session_id"],
            "api_token": api_token,
            "access_token": session_data.get("access_token"),  # This is crucial for frontend
            "url": session_data.get("url"),
            "ice_servers": session_data.get("ice_servers", []),
            "quality": quality,
            "avatar_id": avatar_id,
            "status": "started"
        }
        
        # Verify we have the access_token
        if not response["access_token"]:
            logger.error("No access_token received from HeyGen API")
            return jsonify({"error": "No access_token received from HeyGen API"}), 500
        
        # Auto open viewer in browser
        if data.get('open_viewer', True):
            try:
                viewer_url = f"http://localhost:5173/viewer?local_session_id={local_session_id}"
                webbrowser.open(viewer_url)
                logger.info(f"Viewer opened: {viewer_url}")
            except Exception as e:
                logger.error(f"Failed to open viewer: {str(e)}")

        # Clean up expired sessions
        SessionManager.cleanup_expired_sessions()

        logger.info(f"Session {local_session_id} started and ready for streaming.")
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Error starting session: {str(e)}")
        return jsonify({"error": f"Failed to start session: {str(e)}"}), 500

@app.route('/api/avatar/speak', methods=['POST'])
def speak():
    """Send a text for the avatar to speak."""
    try:
        logger.info("Received request to make avatar speak.")
        
        # Validate request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request data. Request body is required"}), 400
        
        text = data.get("text", "").strip()
        local_session_id = data.get("local_session_id")

        if not text:
            return jsonify({"error": "Input text is required"}), 400
        
        # Limit the length of the input text
        # !Can try to breakdown response to smaller chunks instead of taking in huge text
        if len(text) > 1000:
            return jsonify({"error": "Input text exceeds maximum length of 1000 characters"}), 400
        
        if not local_session_id:
            return jsonify({"error": "Session ID is required"}), 400
        
        # Get the session details
        session = SessionManager.get_session(local_session_id)
        # Check if session exists
        if not session:
            return jsonify({"error": "Session not found or has expired"}), 404
        
        # Task type is repeat so the avatar will repeat the same text
        payload = {
            "session_id": session['session_id'],
            "text": text,
            "task_type": "repeat"
        }

        result, status_code = heygen_api_request("streaming.task", method='POST', data=payload)

        if status_code == 200:
            logger.info(f"Avatar speaking: {text}")

        return jsonify(result), status_code
    
    except Exception as e:
        logger.error(f"Error making avatar speak: {str(e)}")
        return jsonify({"error": f"Failed to make avatar speak: {str(e)}"}), 500
    
@app.route('/api/avatar/stop', methods=['POST'])
def stop_session():
    """Stop an avatar streaming session."""
    try:
        logger.info("Received request to stop avatar session.")

        data = request.get_json() or {}
        local_session_id = data.get("local_session_id")

        if not local_session_id:
            return jsonify({"error": "Session ID is required"}), 400
        
        session = SessionManager.get_session(local_session_id)
        if not session:
            return jsonify({"error": "Session not found or has expired"}), 404
        
        payload = {
            "session_id": session['session_id']
        }

        result, status_code = heygen_api_request("streaming.stop", method='POST', data=payload)

        # Clean up the local session
        SessionManager.cleanup_session(local_session_id)

        logger.info(f"Session {local_session_id} stopped.")
        return jsonify(result), status_code
    
    except Exception as e:
        logger.error(f"Error stopping session: {str(e)}")
        return jsonify({"error": f"Failed to stop session: {str(e)}"}), 500
    
@app.route('/api/avatar/sessions', methods=['GET'])
def list_sessions():
    """List all active avatar streaming sessions."""
    try:
        logger.info("Received request to list all active sessions.")
        
        # Clean up expired sessions before listing
        SessionManager.cleanup_expired_sessions()

        active_sessions = [
            {
                "local_session_id": sid,
                "session_id": session["session_id"],
                "api_token": session.get("api_token"),  # API token for backend operations
                "access_token": session.get("access_token"),  # LiveKit access token for streaming
                "url": session.get("url"),
                "ice_servers": session.get("ice_servers", []),
                "created_at": session["created_at"].isoformat(),
                "last_accessed": session["last_accessed"].isoformat()
            }
            for sid, session in sessions.items()
        ]
        
        # Return the list of active sessions and the number of active sessions
        return jsonify({"active_sessions": active_sessions, "count": len(active_sessions)})
    
    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}")
        return jsonify({"error": f"Failed to list sessions: {str(e)}"}), 500
    
# Define the root endpoint
if __name__ == '__main__':
    port = int(os.getenv('PORT', 3001))
    debug = os.getenv("FLASK_ENV") == "development"
    
    logger.info(f"Starting Heygen API server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=debug)