# Translate Web App

## [Visit the deployed site]()

### Description
The Translate Web App is a tool that allows users to translate words or phrases from English to Chinese and vice versa. Users can input text in the provided form, select the translation direction, and receive the translated text along with its corresponding pinyin (phonetic spelling). The app also features user authentication, a search history page, the ability to delete searches, and the ability to save and unsave translations.

### Features

1. **Translation:** Users can translate text from English to Chinese or from Chinese to English.
2. **Search History:** Users can view their translation history on the "History" page and delete or save searches.
3. **Save/Unsave Searches:** Users can save or unsave translations to easily access them later on the "Saved Searches" page as well as delete searches.
4. **Password Reset:** Users can request a password reset if they forget their password.
5. **Responsive Design:** The app is designed to be responsive and accessible on various devices.

### User Flow

1. **Home Page (/)**
   - Users land on the home page, with a stylistic design.

2. **Translate Page (/translate)**
   - Users navigate to the Translate page where they can input text and choose the translation direction.
   - After submitting the form, users receive the translation and pinyin.

3. **Search History Page (/history)**
   - Users can access their translation history, including saved and unsaved searches.
   - Each entry includes the original word, translation, language, and pinyin.

4. **Saved Searches Page (/saved-searches)**
   - Users can view their saved searches.
   - Each entry includes the original word, translation, language, and pinyin.

5. **Signup (/signup), Login (/login), Logout (/logout)**
   - Users can sign up for an account, log in, and log out.
   - Authentication is required to access certain features.

6. **Password Reset Request (/reset-password-request)**
   - Users can request a password reset by providing their email.
   - An email is sent with instructions to reset the password.

### API

The app uses the Google Cloud Translate API for language detection and translation.

### Technology Stack

- **Frontend:** HTML, CSS, Bootstrap, JavaScript
- **Backend:** Flask (Python)
- **Database:** PostgreSQL
- **Translation API:** Google Cloud Translate
- **Additional Libraries:** Flask-DebugToolbar, Flask-Bcrypt, Xpinyin, Mailjet, Python-dotenv, Font Awesome

### Notes

- The app uses the Mailjet API to send password reset emails.
- User passwords are hashed using Flask-Bcrypt for security.
