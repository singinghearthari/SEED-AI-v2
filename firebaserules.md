# Firebase Security Rules

To properly secure your Firestore database, you must enforce security rules that ensure users can only read and write their own data. Since SEED AI uses Firebase Authentication, we can match the `user_id` associated with the documents against the `request.auth.uid`.

Here are the complete Firestore rules for the SEED AI application, covering all the collections utilized by the backend agents (`farm_memory`, `conversation_history`, `execution_logs`, and `disease_history`):

```javascript
rules_version = '2';

service cloud.firestore {
  match /databases/{database}/documents {

    // 1. Farm Memory (User Profiles & Farm Context)
    // Document ID exactly matches the user's Auth UID.
    match /farm_memory/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }

    // 2. Conversation History
    // Documents have auto-generated IDs, but contain a 'user_id' field.
    match /conversation_history/{docId} {
      allow read, update, delete: if request.auth != null && resource.data.user_id == request.auth.uid;
      allow create: if request.auth != null && request.resource.data.user_id == request.auth.uid;
    }

    // 3. Execution Logs (Agent Traces & Telemetry)
    // Documents have auto-generated IDs, but contain a 'user_id' field.
    match /execution_logs/{docId} {
      allow read, update, delete: if request.auth != null && resource.data.user_id == request.auth.uid;
      allow create: if request.auth != null && request.resource.data.user_id == request.auth.uid;
    }

    // 4. Disease History (Vision Agent Logs)
    // Documents have auto-generated IDs, but contain a 'user_id' field.
    match /disease_history/{docId} {
      allow read, update, delete: if request.auth != null && resource.data.user_id == request.auth.uid;
      allow create: if request.auth != null && request.resource.data.user_id == request.auth.uid;
    }
    
    // Default Deny: Block access to any other collections not explicitly defined above
    match /{document=**} {
      allow read, write: if false;
    }
  }
}
```

### How to Apply These Rules
1. Go to the [Firebase Console](https://console.firebase.google.com/).
2. Select your SEED AI project.
3. In the left-hand menu, navigate to **Build > Firestore Database**.
4. Click on the **Rules** tab.
5. Paste the rules provided above, replacing any existing rules.
6. Click **Publish**.

*(Note: Your media storage utilizes Supabase, so Firebase Storage rules are not required for image uploads.)*
