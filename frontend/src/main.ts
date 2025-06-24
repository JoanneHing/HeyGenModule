import StreamingAvatar, { StreamingEvents } from "@heygen/streaming-avatar";

// DOM elements
const videoElement = document.getElementById("avatarVideo") as HTMLVideoElement;
const loadingDiv = document.getElementById("loading")!;
const errorDiv = document.getElementById("error")!;

// Parameters from URL and session id
const params = new URLSearchParams(window.location.search);
const sessionId = params.get("local_session_id") || params.get("session_id");

// Check if session_id is provided
if (!sessionId) {
  showError("Missing session_id in URL.");
  throw new Error("Missing session_id");
}

// Global avatar instance for cleanup
let avatar: StreamingAvatar | null = null;

main();

async function main() {
  try {
    console.log("Starting avatar streaming with session_id:", sessionId);

    // Fetch active sessions from the backend
    const res = await fetch(`http://localhost:3001/api/avatar/sessions`);

    if (!res.ok) {
      throw new Error(`Failed to fetch sessions: ${res.statusText}`);
    }

    const data = await res.json();
    console.log("Active sessions:", data);

    // Find the session with the provided session_id
    const session = data.active_sessions?.find(
      (s: any) => s.local_session_id === sessionId || s.session_id === sessionId
    );

    if (!session) {
      throw new Error("Session not found in active sessions");
    }

    console.log("Found session:", session);

    // Get the access_token from the session (for streaming connection)
    const accessToken = session.access_token;
    
    if (!accessToken) {
      throw new Error("Session found but access_token is missing");
    }

    console.log("Found access token, initializing avatar streaming...");

    // Request fullscreen mode
    try {
      await document.documentElement.requestFullscreen?.();
    } catch (e) {
      console.warn("Could not enter fullscreen:", e);
    }

    // Initialize the avatar with the access_token
    avatar = new StreamingAvatar({ 
      token: accessToken
    });

    // Set up all event handlers before connecting
    avatar.on(StreamingEvents.STREAM_READY, (event) => {
      console.log("Stream ready event received:", event);
      
      // Handle the stream from the event
      if (event && event.detail) {
        const stream = event.detail;
        console.log("Setting video source to stream:", stream);
        videoElement.srcObject = stream;
        
        // Handle video loading
        videoElement.onloadedmetadata = () => {
          console.log("Video metadata loaded, attempting to play...");
          videoElement.play()
            .then(() => {
              console.log("Video playing successfully");
              showVideo();
            })
            .catch((err) => {
              console.error("Failed to play video:", err);
              showError("Failed to play avatar video. Check browser permissions for autoplay.");
            });
        };
        
        // Handle video errors
        videoElement.onerror = (err) => {
          console.error("Video error:", err);
          showError("Video stream error.");
        };
      } else {
        console.error("No stream in STREAM_READY event");
        showError("No video stream received from avatar.");
      }
    });

    avatar.on(StreamingEvents.STREAM_DISCONNECTED, () => {
      console.log("Stream disconnected");
      videoElement.srcObject = null;
      showError("Avatar disconnected. Closing...");
      
      setTimeout(() => {
        window.close();
      }, 2000);
    });

    // Handle avatar talk events for debugging
    avatar.on(StreamingEvents.AVATAR_START_TALKING, (event) => {
      console.log("Avatar started talking:", event);
    });

    avatar.on(StreamingEvents.AVATAR_STOP_TALKING, (event) => {
      console.log("Avatar stopped talking:", event);
    });

    // Handle general errors
    avatar.on("error" as any, (error: any) => {
      console.error("Avatar error:", error);
      showError(`Avatar error: ${error.message || 'Unknown error'}`);
    });

    console.log("Avatar SDK initialized with access token. The SDK should automatically connect to the existing session.");

    // Add a timeout to detect if the stream doesn't connect
    setTimeout(() => {
      if (!videoElement.srcObject) {
        console.warn("No video stream received within 5 minutes.");
        showError("Connection timeout. The session may have expired or there may be a network issue. Please try restarting the session.");
      }
    }, 300000);

  } catch (err: any) {
    console.error("Error in main function:", err);
    if (err.message?.includes('fetch')) {
      showError("Cannot connect to server. Is the backend running on localhost:3001?");
    } else {
      showError(`Failed to initialize avatar: ${err.message || 'Unknown error'}`);
    }
  }
}

// Show the video element and hide the loading indicator
function showVideo() {
  loadingDiv.style.display = "none";
  videoElement.style.display = "block";
  errorDiv.style.display = "none";
}

// Show an error message and hide the loading indicator
function showError(message: string) {
  loadingDiv.style.display = "none";
  errorDiv.textContent = message;
  errorDiv.style.display = "block";
  videoElement.style.display = "none";
}

// Proper cleanup on page unload
window.addEventListener('beforeunload', () => {
  console.log("Page unloading, cleaning up...");
  
  // Clean up video element
  if (videoElement.srcObject) {
    const stream = videoElement.srcObject as MediaStream;
    stream.getTracks().forEach(track => track.stop());
    videoElement.srcObject = null;
  }
  
  // Clean up avatar instance
  if (avatar) {
    avatar = null;
  }
});
