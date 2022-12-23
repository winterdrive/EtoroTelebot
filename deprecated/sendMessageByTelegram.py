import requests
import shutil


# function returning time in hh:mm:ss
def convertTime(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return "%d:%02d:%02d" % (hours, minutes, seconds)


def main():
    # returns a tuple
    total, used, free = shutil.disk_usage("/")
    text = "【Alert!】" + "\n" + ("Disk usage: ") + str(round((used / total) * 100, 2)) + "%" + "\n" + (
            "Total size: %d GiB" % (total // (2 ** 30))) + "\n" + ("Used: %d GiB" % (used // (2 ** 30))) + "\n" + (
                   "Free size: %d GiB" % (free // (2 ** 30)))
    TOKEN = "5495772446:AAGcdNXEy5BbBo-QGxLcALw2HV-__mrcqlo"
    CHATID = "-1001423405758"

    url = f"https://api.telegram.org/bot{TOKEN}"
    params = {"chat_id": CHATID, "text": text}

    # print("Total size: %d GiB" % (total // (2**30)))
    # print("Used: %d GiB" % (used // (2**30)))
    # print("Free size: %d GiB" % (free // (2**30)))
    req = requests.get(url + "/sendMessage", params=params)


if __name__ == '__main__':
    main()
