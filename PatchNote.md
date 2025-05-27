# TerryBoo

## Update Ver Diary

### 2025 05 20

- 0.0.1
  - Created the project and import basic functions into the project.

### 2025 05 21

- Created services folder and added fansExpSystem.py and gumiSleep.py for preperation of Exp system and Sleep alarm.
- Created krskKmskBotDb.db

### 2025 05 22

- 0.0.2
  - Insert table breakLawTime with GumiTime and FoxTime, which can add the law breaking time of the two users.
  - The reminder of lawBreaking will only pop once.

- Under Developing
  - my_rank command: Can make a picture now, but the font size and the layout is not good, need adjustment.
  - exp_system: created table in the db, but no any functions created yet, and the rank card won't receive anything.

### 2025 05 26

- 0.0.3
  - Rank Card Styling is done. /rank my_rank
  - Added Custom Settings with color. (RGB) /rank set_card_color
  - User Exp System is done. With on_message add exp(1 to 5) with 1 min CD.
  - Users now can get check the rank via commands.

### 2025 05 27

- 0.0.3b
  - Rank Card name font size adjustment. (<8 or >32 will be small) now change to <8 is large and >32 is small
  - The lvling up announcement will now represent in #command-spamming channel.
