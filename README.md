# Shopping List Web-App

## How to set it up

### Installing Python interpreter
> If you don't have a Python interpreter already, you'll need to install one. 
> There are different ways of doing so, and I'll show you how to do it with one of them. 
---
1. Search `Python download` in your search engine, or [click on this link](https://www.python.org/downloads/). If you're using something else than Windows, you'll find downloads for your OS under "Looking for Python with a different OS?".
2. Click "Download" and install it when the download has finished.

### Installing all extensions (HTML CSS Support, JavaScript, Python)
> In your IDE, there are a few extensions that you need. Here we'll be going through installing all of them.
---
1. Open [Visual Studio Code](https://code.visualstudio.com) (assuming it's already downloaded, which is usually the case for Windows users) or any other IDE of your choice.
2. Go to the extensions tab.
3. Search `HTML CSS Support`. Install the extension published by `ecmel` and enable it.
4. Search `JavaScript (ES6) code snippets`. Install the extension published by `charalampos karypidis` and enable it.
5. Search `Python`. Install the extension published by `Microsoft` and enable it.

### Downloading all libraries for Python
> Before running the code, we need to install every library for Python that was used in the project.
---
1. In your terminal, run `pip install -r requirements.txt`. If you get an error here about the `pip` command not being found, the issue is likely with environment variables. [This video can help you with that](https://www.youtube.com/watch?v=oa7YR5GpJ0A).

### MySQL: The database
> MySQL is a database, and databases are helpful for storing information.
---
1. Search `MySQL Download`, or [click here](https://dev.mysql.com/downloads/installer/).
2. Download and install the version you need. Remember the password you set in the setup.
3. Open MySQL and log in. Then, type the command `CREATE DATABASE your_database` (replace your_database with the name you want your database to have).
4. In Visual Studio Code, make a new file called `.env`. Paste this in your file:
```.env
# Change your_username with root, your_password with your password, and your_database with the name of your database.
db_path=your_username:your_password@localhost/your_database
```
Check out the `.env.example` file to see a template of how the entire file should look like. 

### Stripe API key
> This is where you'll get the API key (for testing, meaning we're using fake money) for using the checkout in the Web-App.
---
1. Go to [stripe](https://dashboard.stripe.com/test/apikeys) and sign up if you don't already have an account.
2. Copy the `Secret key` and paste it in your `.env` file. Check out the `.env.example` file to see a template of how the entire file should look like. 

### Google login API key (OAuth2)
> Google login is used to log in and create users in the Web-App securely.
> While this might look like at lot of steps, it only takes about 5-10 minutes to set up.
---
1. Go to [Google Cloud](https://console.cloud.google.com)
2. Make new project. Click on APIs & Services.
3. Go to Enable APIs & services and click ENABLE APIS AND SERVICES.
4. Search for People API, click on it and enable it.
5. Go back to Enable APIs & services and click on OAuth consent screen.
6. Select the User Type.
7. Click create.
8. Type in name in App name.
9. Type in your email in User support email.
10. Type in your email again in email addresses under Developer contact information
11. Click SAVE AND CONTINUE
12. Add scopes: openid ./auth/userinfo.email ./auth/userinfo.profile
13. Click SAVE AND CONTINUE
14. You don't need to add any users
15. Click SAVE AND CONTINUE
16. Check info
17. If everything looks okay, click BACK TO DASHBOARD
18. Click on Credentials
19. Click on CREATE CREDENTIALS and select OAuth client ID.
20. From Application Type, select Web application. Name can be whatever you want.
21. Add your URI under Authorized redirect URIs (Link to your website). You can add multiple.
22. Since I used a development server, mine is: `http://localhost:5000/auth/google/callback`
23. Copy CLIENT_ID and paste it in your `.env` file. Do the same with CLIENT_SECRET. Check out the `.env.example` file to see a template of how the entire file should look like. 
25. Click CREATE.
