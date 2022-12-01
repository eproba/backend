import re
from datetime import datetime

from scouts_exams.scouts_exams import __version__ as old_version_str


def update_version_strings(file_path, _new_version):
    version_regex = re.compile(r"(^_*?version_*?\s*=\s*['\"])(\d+\.\d+\.\d+)")
    with open(file_path, "r+") as f:
        content = f.read()
        f.seek(0)
        f.write(
            re.sub(
                version_regex,
                lambda match: "{}{}".format(match.group(1), _new_version),
                content,
            )
        )
        f.truncate()


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

update_version_strings(
    "scouts_exams/scouts_exams/__init__.py",
    f"{new_version['year']}.{new_version['month']}.{new_version['day']}{'.' + str(new_version['patch']) if new_version['patch'] != 0 else ''}",
)

print(
    f"Updated version to {new_version['year']}.{new_version['month']}.{new_version['day']}{'.' + str(new_version['patch']) if new_version['patch'] != 0 else ''}"
)
