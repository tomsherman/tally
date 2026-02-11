# Tally

Tally is a command line tool for tracking team scores during a fitness challenge. Fitness activities performed by users in a team are retrieved from Strava and daily score are assigned based on a point system. The point system is provided in the section below.

## Point System

All point values below are the **defaults**. They can be changed during "Configure challenge" (see [Configuration](#configuration)).

### Daily Active Time Cap

Each user's total active time per day can be capped (default: 360 minutes / 6 hours). Time beyond the cap is ignored for scoring. Set to 0 during initialization to disable the cap.

### User Points

For users, points are calculated based on the (capped) total active time from all activities on a given day. When multiple activities overlap in time (e.g. a watch and phone both record the same run), the overlapping period is only counted once.

- **Base points**: 1 point per full hour of active time (configurable via `base_points_per_hour`).
- **Threshold bonuses** (configurable via `point_thresholds`):

| Active Time  | Bonus Points |
|--------------|-------------|
| ≥ 30 minutes | +5          |
| ≥ 1 hour     | +2          |
| ≥ 2 hours    | +1          |

With the defaults, a user active for exactly 1 hour earns 1 (base) + 5 (30 min threshold) + 2 (60 min threshold) = **8 points**.

#### Streak Bonus

An additional 5 bonus points (configurable) are awarded for every 7 consecutive days (configurable) where the user earned more than 0 points. Consecutive-day intervals do not overlap.

### Team Points

The team points for a given day are the sum of all users' points in the team for that day.

#### Team Bonus

A team is awarded 5 additional points (configurable) for a given day if **all** users in the team earned more than 0 points that day.

## Configuration

Scoring and tracking options are set during **Configure challenge** (initialization) and stored in the database with the challenge. There is no config file; run the tool and choose "Configure challenge" to set or change:

| Option | Description |
|--------|-------------|
| Max daily active minutes | Cap on active minutes per person per day that count for points. Enter 0 for no cap (default: 360 = 6 hours). |
| Base points per hour | Base points per full hour of active time. |
| Point thresholds | Bonus points at time thresholds (e.g. 30 min → 5 pts); defined in code, not prompted. |
| User streak bonus / interval | Bonus points for each completed streak of consecutive active days, and the number of days in that interval. |
| Team bonus points | Bonus when all team members are active that day. |
| Strava request interval | Delay in seconds between Strava API requests (rate limiting). |

## Installation

1. Go to the [releases](https://github.com/titanjack36/tally/releases) page.
2. Download the zipped executable under the Assets section.
    1. MacOS: click on the `tally-macos-<version>.zip` file
    2. Windows: click on the `tally-windows-<version>.zip` file
3. Unzip the contents into a folder.
4. Run the executable:
   - MacOS/Linux: `./tally`
   - Windows: `tally.exe`

## How to use

1. Create clubs on Strava for each team. **Users in the club must set their activities to be viewable by other users of the club**. Verify this by checking that their activity appears in the club activity feed.
2. Create a Strava 'service account' and add it to each club. The account will be used to fetch activities from clubs.
3. Create a user registration spreadsheet from [user_team_registration_template.csv](./templates/user_team_registration_template.csv). It should contain the columns `team_name`, `team_id`, `user_name`, and `user_link`. Do not edit or move the column names.
4. Fill the spreadsheet with user and club (team) information, for example:

| team_name | team_id | user_name | user_link |
|-----------|---------|-----------|-----------|
| Team 1    | 532944  | John Doe  | https://www.strava.com/athletes/12432 |
| Team 2    | 234954  | Jane Doe  | https://www.strava.com/athletes/32543 |

5. Download the spreadsheet as a CSV file.
6. Run `tally` to start the tool.
7. When prompted, select the `Configure challenge` option to configure a new challenge.

```
? Select an operation (Use arrow keys)
 » Configure challenge
   Track activities
   Calculate scores
   Delete all data
   Export activity data
   Import activity data
   Exit
```

8. Enter the name, start date, time zone, and scoring/tracking options for the challenge according to the prompts. Scoring options include the daily active time cap (in minutes), base points per hour, streak bonus, team bonus, and Strava request interval (press Enter to accept defaults).
9. When asked to select a user list, choose the CSV file that was downloaded in the previous step. Ensure that the selected CSV file is filled correctly. Partially filled rows will be skipped.
10. Next, select the `Track activities` option to track new activities since the start of the challenge. It is recommended to run this command at least once a week since activities older than about 2 weeks may no longer appear in the Strava club feed. Each run also **reconciles** the last 5 days: activities that were updated on Strava are overwritten in the database, and activities that were deleted on Strava are removed from the database.
11. After activities have been tracked, select the `Calculate scores` option to calculate the team scores for the challenge. When prompted for the scoring end date, it is recommended to use yesterday's date since the scoring for today may be incomplete.

### Reviewing and Updating Activities

1. To view the list of tracked activities for all users, run `tally` and select the `Export activity data` option.
2. Upload the exported CSV file to a shared spreadsheet to users can review the activities.
3. Create a form to allow users to submit updates to their activities. The form should contain fields for the columns `link`, `user_link`, `title`, `workout_type`, `date`, and `active_time`. Users should copy over values from the exported activity list while filling the form. Note that date must be in the format `YYYY-MM-DD` and active time must be in the format similar to `1h 15m` or `45m`.
4. When activity updates have been submitted, the form should output a spreadsheet similar to the following:

| link | user_link | title | workout_type | date | active_time |
|------|-----------|-------|--------------|------|-------------|
| https://www.strava.com/activities/153453453 | https://www.strava.com/athletes/34234 | Afternoon Run | Run | 2025-07-01 | 1h 15m |
| https://www.strava.com/activities/534834912 | https://www.strava.com/athletes/45343 | Night Run | Run | 2025-07-02 | 45m |

5. Download the spreadsheet as a CSV file.
6. Run `tally` to start the tool.
7. When prompted, select the `Import activity data` option to import the activity updates.
8. When prompted, select the CSV file that was downloaded in the previous step.

## Local Development

### Prerequisites

- Python 3.10+
    - MacOS: install with `brew install python`
    - Windows: Download from https://www.python.org/downloads/windows/
- pipx
    - MacOS: install with `brew install pipx && pipx ensurepath`
    - Windows: `python3 -m pip install --user pipx; pipx ensurepath`
        - If you get an error `pipx: command not found`, you may need to add your python Scripts folder (e.g. `C:\Users\<username>\AppData\Local\Programs\Python\<version>\Scripts`) to your system path.
- tkinter
    - MacOS: install with `brew install python-tk`
    - Windows: should be included with the Python installation
- Google Chrome (used by Selenium to automate fetching from Strava)
    - Download from https://www.google.com/chrome/

### Setup

1. Clone this repository
2. Create a virtual environment with `python -m venv venv`
3. Activate the virtual environment with `source venv/bin/activate`
4. Install the dependencies with `pip install -r requirements.txt`
5. Create an [editable install](https://setuptools.pypa.io/en/latest/userguide/development_mode.html) of the package with `pip install -e .`
6. Install [pre-commit](https://pre-commit.com/) hooks with `pre-commit install`
7. Run the tool with `python -m tally`

### Installing from Source

1. Clone or download this repository
2. Install the command line tool
    1. MacOS: Run `chmod +x scripts/install.sh && scripts/install.sh`
    2. Windows: Run `scripts\install.ps1`
        1. If you get an error `install.ps1 cannot be loaded because running scripts is disabled on this system`, run a PowerShell terminal as an administrator and enter `Set-ExecutionPolicy RemoteSigned`
3. Run `tally` to start the tool

### Building an Executable

1. Run the build script
    1. MacOS: Run `chmod +x scripts/build.sh && scripts/build.sh`
    2. Windows: Run `scripts\build.ps1`
        1. If you get an error `build.ps1 cannot be loaded because running scripts is disabled on this system`, run a PowerShell terminal as an administrator and enter `Set-ExecutionPolicy RemoteSigned`
2. The executable will be saved in the `dist/tally` directory. When distributing the executable, keep the `_internal` folder and `tally` executable together.

### Running Tests

To run all test cases, use:

```bash
$ python -m pytest
```

To run a specific test case, use:

```bash
$ python -m pytest <path_to_test_file>::<test_class>::<test_method>
# e.g. python -m pytest tests/tally/score/test_user_active_time.py::TestGetUserActiveTime::test_timezone_conversion_america_los_angeles_boundary
```

### Project Structure

```
tally/
├── src/
│   └── tally/
│       ├── cli.py                       # Entry point for the command line tool
│       ├── config.py                    # Runtime config applied from DB challenge (apply_challenge_config)
│       ├── actions/                     # Each subdirectory represents a different operation
│       │   ├── export/
│       │   ├── initialize/
│       │   ├── load/
│       │   ├── reset/
│       │   ├── score/
│       │   │   └── point_system.py      # Rules for calculating user and team points
│       │   └── track/
│       ├── models/                      # Database ORM and schema validation models
│       ├── services/
│       │   ├── db.py                    # Database connection and operations
│       │   └── strava.py               # Connects with Strava to fetch user activities
│       └── utils/                       # Common helper functions
├── tests/                               # Unit tests
├── scripts/                             # Install and build scripts
├── templates/                           # Expected file formats for input files
├── data/                                # Database storage (created at runtime)
└── logs/                                # Debug logs (created at runtime)
```