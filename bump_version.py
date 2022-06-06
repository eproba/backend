from datetime import datetime

from scouts_exams.scouts_exams import __version__ as old_version_str

old_version = {
    "year": int(old_version_str.split(".")[0]),
    "month": int(old_version_str.split(".")[1]),
    "day": int(old_version_str.split(".")[2]),
    "patch": int(
        old_version_str.split(".")[3] if len(old_version_str.split(".")) > 3 else 0
    ),
}

new_version = {
    "year": datetime.today().year,
    "month": datetime.today().strftime("%m"),
    "day": datetime.today().strftime("%d"),
    "patch": 0
    if old_version["year"] != datetime.today().year
    or old_version["month"] != datetime.today().month
    or old_version["day"] != datetime.today().day
    else old_version["patch"] + 1,
}

with open("scouts_exams/scouts_exams/__init__.py", "w") as f:
    f.write(
        f"__version__ = \"{new_version['year']}.{new_version['month']}.{new_version['day']}{'.'+ str(new_version['patch']) if new_version['patch'] != 0 else ''}\"\n"
    )

print(
    f"Updated version to {new_version['year']}.{new_version['month']}.{new_version['day']}{'.'+ str(new_version['patch']) if new_version['patch'] != 0 else ''}"
)
