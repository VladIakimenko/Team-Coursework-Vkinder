# VKinder
## Project description
The purpose of this application is to help vk.com users arrange a date in an easy and unburdensome manner.
It can help people get acquainted and make friends building the matches on the base of their interests and preferences.
The app operates a chatbot that can communicate to users through a vk.com community.
It has wide range of opportunities including the enhanced interest analysis mechanism and complex search algorithms,
thus allowing users to get in touch with people with corresponding views and passions.

## Program composition
* Database - a package responsible for interaction with database 
* main.py - entry point to the application. Puts together the modules and directs the run of the program
* bot.py - the module holds 2 classes responsible for interaction with vk.com API and communication with user
* transformer.py - is in charge of data collection and transformation. It holds linguistic analysis functions required for interests comparison
* vk_scripts - a directory that holds the scripts written in vk script language. The scripts are used to interact with api and ensure speed advantage in comparison with making all requests from the client side. 

## Preparation & Set up
To get started you need:
1. Register a vk.com community on behalf of which communication with users will be held.
2. Get a group token for the chatbot. See [Manual](https://github.com/netology-code/adpy-team-diplom/blob/main/group_settings.md)
3. Get a User token for searching and requesting photos. See [Manual](https://docs.google.com/document/d/1_xt16CMeaEir-tWLbUFyleZl6woEdJt-7eyva1coT3w/edit)  

    
   The tokens are saved and retrieved from ".env" file that should be located at the root directory (where the "main.py" is)
   Please use the following constants:  
   GROUP_ID=...  
   GROUP_TOKEN=...   
   USER_TOKEN=...  
  

3. Set up your PC or server to work with PostgreSQL
4. Edit the "postgres_config.py" in the "Database" package to provide the DB connection details.  
  
Kindly note, that the application does not crate the database itself, so before starting the app use "createdb" command in terminal.

## Requirements
The program has the following dependencies:
- PostgreSQL installed and set up
- DBeaver or equivalent (for database maintenance)
- Python 3.6+
- packages listed in "requirements.txt" ("Pipfile" is also provided for pipenv users)  
You can install them using the command ```pip install requirements.txt```or ```pipenv install```  in the terminal 

## Operation manual
All functions within the program are supplemented with descriptive docstrings and annotations (where possible).
This gives an extensive description on how the program elements interact. This manual rather describes the user interface and interaction with the program.  

Each time a new user writes a text message to the group, the bot analyses the user's sex, age, city and user's interests,
and adds a new user to the database (in case he/she isn't there already). Then the bot checks if there are any matching accounts in the database
and suggests them to the user in a form of a message including:
- name
- link to account
- 3 most pupular (by likes) photos  
If there are no matching accounts saved in the database the app requests vk.com api to search relevant accounts online. Once found, the program checks
if the account has at least 3 photographs, and if so, both proposes the match to the user and saves the account to databse.  

Before sending a suggestion from the database, the application checks if the account is valid, still active and hasn't been deleted, and clears it up from
the database if it doesn't pass the inspection.

After receiving the proposal the user can either request a new one, pressing the "next" button,
add it to "favorites" or "blacklist" (using the corresponding buttons) or request a list of his/her favorites by pressing the "saved" button.
There is also a text command available. User can text "clear favorites" to the dialogue to clear up the data from his/her favorites list.

The conversation timout is set to 10 minutes, which practically means that the bot will keep in mind which is the next offer to be sent only while the dialogue is active.
If no incoming messages received for over 10 minutes, the bot closes up the dialogue to start it a new, when the user comes back. Though the data on user's
blacklist and favorites is retained and saved to database.

The application uses a multi-threading syntax allowing simultaneous communication with several users. A new dialogue is opened for every new user to insure
no interferences or miss-addressed replies occur.
