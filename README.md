NS Router Ingestion App

This is the "Input" side of the router automation factory.

1. Setup

Create a Next.js app: npx create-next-app@latest ns-scanner

Install deps: npm install react-webcam firebase lucide-react @google/generative-ai

Copy the files into the structure provided.

2. Environment Variables (.env.local)

Create a .env.local file in the root:

# Get from Google AI Studio (Free)
GOOGLE_API_KEY="AIzaSy..."

# Get from Firebase Console
NEXT_PUBLIC_FIREBASE_API_KEY="..."
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN="..."
NEXT_PUBLIC_FIREBASE_PROJECT_ID="..."
# ... (add other firebase config vars)


3. Deploy

Push to GitHub.

Import to Vercel.

Add the Environment Variables in Vercel Settings.

Open the link on your phone.

4. Usage

Open App.

Point camera at Router Label.

Click Capture.

Verify S/N and SSID are correct (edit if needed).

Click Save.

The data is now in Firestore, ready for the Python Robot to read.