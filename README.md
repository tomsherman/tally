# Tally

Tally is a command line tool for tracking team scores during a fitness challenge. Fitness activities performed by users in a team are retrieved from Strava and daily score are assigned based on a point system. The point system is provided in the section below.

## Point System

### User Points

For users, the points are calculated based on the total active time from all activities on a given day.

| Active Time  | Points Awarded                    |
|--------------|-----------------------------------|
| < 30 minutes | 0 points                          |
| ≥ 30 minutes | 5 points                          |
| ≥ 1 hour     | 7 points                          |
| ≥ 2 hours    | 8 points + 1 point per hour after |

#### Bonus Points 

An additional 5 points are awarded to the user for each 7 consecutive days where the user is active (i.e. has received more than 0 points). The consecutive days cannot overlap, so at most 5 bonus points per week can be awarded to a user.

### Team Points

The team points for a given day are calculated by summing the points of all users in the team for that day.

#### Bonus Points

A team is awareded 5 additional points for a given day if all users in the team are active for that day (i.e. have received more than 0 points).

## Configuration

Tally has **no compiled-in defaults**. You must provide a `config.yaml` file and pass it with `--config` every time you run the tool (both from source and when using the executable).

1. Copy [config.example.yaml](./config.example.yaml) to `config.yaml`.
2. Edit `config.yaml` to set scoring rules, daily cap, and Strava rate limiting.
3. Run the tool with: `tally --config config.yaml` (or `tally --config /path/to/your/config.yaml`).

| Key | Description |
|-----|-------------|
| `max_daily_active_seconds` | Max active seconds per person per day that count for points. Omit or set to `null` to disable the cap. Example: `21600` (6 hours). |
| `base_points_per_hour` | Base points per full hour of active time. |
| `point_thresholds` | List of `{minutes, points}` for bonus points at each threshold (e.g. 30 min → 5 pts). |
| `user_streak_bonus_points` | Bonus points for each completed streak interval. |
| `user_streak_interval_days` | Consecutive days required for a streak bonus. |
| `team_bonus_points` | Bonus points when all team members are active that day. |
| `strava_request_interval_seconds` | Delay between Strava API requests (rate limiting). |

## Installation

1. Go to the [releases](https://github.com/titanjack36/tally/releases) page.
2. Download the zipped executable under the Assets section.
    1. MacOS: click on the `tally-macos-<version>.zip` file
    2. Windows: click on the `tally-windows-<version>.zip` file
3. Unzip the contents `.zip` file into a folder.
4. Copy `config.example.yaml` to `config.yaml` in the same folder (or elsewhere) and edit as needed.
5. Run the executable with a path to your config file, for example:
   - MacOS/Linux: `./tally --config config.yaml`
   - Windows: `tally.exe --config config.yaml`

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
6. Run `tally --config config.yaml` to start the tool (use the path to your config file).
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

8. Enter the name, start date and time zone for the challenge according to the prompts.
9. When asked to select a user list, choose the CSV file that was downloaded in the previous step. Ensure that the selected CSV file is filled correctly. Partially filled rows will be skipped.
10. Next, select the `Track activities` option to track new activities since the start of the challenge. It is recommended to run this command every week since activities older than 2 weeks may not be displayed in the club activity feed. Note that the number of saved activities may be less than the number of activities fetched from Strava as some activities may have occurred before the start of the challenge.
11. After activities have been tracked, select the `Calculate scores` option to calculate the team scores for the challenge. When prompted for the scoring end date, it is recommended to use yesterday's date since the scoring for today may be incomplete.

### Reviewing and Updating Activities

1. To view the list of tracked activities for all users, run `tally --config config.yaml` and select the `Export activity data` option.
2. Upload the exported CSV file to a shared spreadsheet to users can review the activities.
3. Create a form to allow users to submit updates to their activities. The form should contain fields for the columns `link`, `user_link`, `title`, `workout_type`, `date`, and `active_time`. Users should copy over values from the exported activity list while filling the form. Note that date must be in the format `YYYY-MM-DD` and active time must be in the format similar to `1h 15m` or `45m`.
4. When activity updates have been submitted, the form should output a spreadsheet similar to the following:

| link | user_link | title | workout_type | date | active_time |
|------|-----------|-------|--------------|------|-------------|
| https://www.strava.com/activities/153453453 | https://www.strava.com/athletes/34234 | Afternoon Run | Run | 2025-07-01 | 1h 15m |
| https://www.strava.com/activities/534834912 | https://www.strava.com/athletes/45343 | Night Run | Run | 2025-07-02 | 45m |

5. Download the spreadsheet as a CSV file.
6. Run `tally --config config.yaml` to start the tool.
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
7. Run the tool with `python -m tally --config config.yaml` (create `config.yaml` from `config.example.yaml` if needed)

### Installing from Source

1. Clone or download this repository
2. Install the command line tool
    1. MacOS: Run `chmod +x scripts/install.sh && scripts/install.sh`
    2. Windows: Run `scripts\install.ps1`
        1. If you get an error `install.ps1 cannot be loaded because running scripts is disabled on this system`, run a PowerShell terminal as an administrator and enter `Set-ExecutionPolicy RemoteSigned`
3. Run `tally --config config.yaml` to start the tool (copy and edit `config.example.yaml` to create `config.yaml`)

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
├── config.example.yaml                  # Example config; copy to config.yaml and pass with --config
├── src/
│   ├── tally/
│   │   ├── config.py                    # Loads configuration from config.yaml (no compiled defaults)
│   │   ├── actions/                     # Each subdirectory represents a different operation performed by the tool
│   │   │   ├── export/
│   │   │   ├── initialize/
│   │   │   ├── load/
│   │   │   ├── reset/
│   │   │   ├── score/
│   │   │   │   ├── point_system.py      # Rules for calculating user and team points
│   │   │   ├── track/
│   │   ├── models/                      # Database ORM and schema validation models
│   │   ├── services/
│   │   │   ├── db.py                    # Database connection and operations
│   │   │   ├── strava.py                # Connects with Strava to fetch user activities
│   │   ├── utils/                       # Common helper functions
│   │   ├── cli.py                       # Entry point for the command line tool
│   ├── tests/                           # Unit tests for the tool
│   ├── scripts/                         # Automate the process of installing the command line tool
│   ├── templates/                       # Defines the expected file format for input files to the command line tool
│   ├── data/                            # Database storage for user, team and activity data
│   ├── logs/                            # Debug logs for each execution of the tool
```