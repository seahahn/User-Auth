# ❇️ AI Play User-Auth

API server responsible for user accounts and authentication-related functions in AI Play.

## :one: Stack

- Python 3.8.12
- Django 4.0.3
- PostgreSQL (ElephantSQL)
- AWS S3
- JWT
- Swagger

<br/>

## :two: Deployment Platform and Server Address

- Platform: Heroku
- Address: [https://ai-play-user-auth.herokuapp.com](https://ai-play-user-auth.herokuapp.com)

<br/>

## :three: API Specification

- DOCS: [https://aiplay-user-auth.herokuapp.com/userauth/swagger/](https://aiplay-user-auth.herokuapp.com/userauth/swagger/)

| Method                     | URL (BASE_URL = /userauth) | Description                                    |
| -------------------------- | -------------------------- | ---------------------------------------------- |
| Email, Nickname Check      |                            |                                                |
| POST                       | /email_check               | Send email verification code when signing up   |
| POST                       | /email_confirm             | Check email verification code when signing up  |
| GET                        | /nickname_check            | Update project structure                       |
| Login, Sign Up, Withdrawal |                            |                                                |
| POST                       | /login                     | User login processing                          |
| POST                       | /signup                    | User sign-up processing                        |
| POST                       | /inactive                  | User withdrawal processing                     |
| CSRF Token & JWT           |                            |                                                |
| GET                        | /index                     | Generate CSRF Token when accessing the web app |
| GET                        | /refresh_jwt               | Refresh JWT token during user access           |
| GET                        | /remove_jwt                | Delete token when user logs out                |
| User Information Change    |                            |                                                |
| POST                       | /nickname_change           | Change user nickname                           |
| POST                       | /profile_pic_change        | Change user profile picture                    |
| POST                       | /pw_change                 | Change user password                           |
| POST                       | /search_pw                 | Issue a temporary password for the user        |

<br/>

## 4️⃣ Troubleshooting Records

- [https://github.com/AI-Play/User-Auth/discussions](https://github.com/AI-Play/User-Auth/discussions)

<br/>

## :five: Development Environment Preparation

<details>
  <summary><b>Preparation</b></summary>

```
// Create a new virtual environment
// 1. Move to the directory which has python version we need to use
// 2. Create a new virtual environment
python -m venv /path/to/new/virtual/environment

// 3. Activate the virtual environment
source /path/to/new/virtual/environment/bin/activate

// 4. Install required packages
pip install -r requirements.txt

# 5. Execute the command to create static files for Swagger UI -> check that files are created under the 'staticfiles' directory
python manage.py collectstatic
```

##### Set up local environment

```
// 1. Prepare Docker PostgreSQL image and run the container
// https://hub.docker.com/_/postgres
docker run -p 5432:5432 --name postgres -e POSTGRES_PASSWORD=aiplay -d postgres
// ※ Caution: Only create and run the container, and do not interfere with other processes as DB setup will be performed in step 2

// 2. Run DJango migration
// Migration file already exists in userauth's models.py (0001_initial.py)
// Executing the following command will set up the DB
python manage.py migrate

// 3. Check if DB tables have been created

// 4. If it doesn't work, run the script at the bottom of dbscript.sql in the Architecture Repo to create triggers
```

##### Run the development server

```
python manage.py runserver
```

</details>
