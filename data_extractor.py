from pprint import pprint
import tweepy as tw
import urllib.request
import cv2
import pytesseract

def load_config(config_file):
    f = open(config_file, "r")
    content = f.read()
    f.close()
    config_list = content.split("\n")
    config = {}
    for c in config_list:
        if len(c) > 0:
            c_split = c.split(":")
            config[c_split[0]] = c_split[1]

    return config

def conf_api(config):
    consumer_key = config["CONSUMER_KEY"]
    consumer_secret = config["CONSUMER_SECRET"]
    access_token = config["ACCESS_TOKEN"]
    access_token_secret = config["ACCESS_TOKEN_SECRET"]

    auth = tw.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tw.API(auth, wait_on_rate_limit=True)

    return api

def get_tweets(api,count=100):
    tweets = api.user_timeline(id="Minsa_Peru", count=count, include_rts=False, tweet_mode="extended")

    return tweets


def extract_date(line):
    month_dict = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
                  "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12}

    date_line = line.split(" ")

    month = month_dict[date_line[4]]
    if month < 10:
        month = "0" + str(month)
    else:
        month = str(month)
    date = "2020-" + month + "-" + date_line[2]

    return date


def extract_time(line):
    time_line = line.split(" ")
    for word in time_line:
        if ":" in word:
            return word


def extract_cases_by_region(tl):
    regions = ["Lima", "Piura", "La Libertad", "Cajarmarca", "Puno", "Junin", "Cusco", "Arequipa", "Lambayeque",
               "Ancash", "Loreto", "Callao", "nuco", "San Mart", "Ica", "Ayacucho", "Huancavelica", "Ucayali",
               "Apurimac", "Amazonas", "Tacna", "Tumbes", "Moquegua", "Madre de Dios"]

    infections = {}
    for line in tl:
        for region in regions:
            if region in line:
                lst = line.split(": ")
                for j in range(len(lst)):
                    if region in lst[j]:
                        if region == "nuco":
                            infections["Huánuco"] = int(lst[j + 1])
                        elif region == "San Mart":
                            infections["San Martín"] = int(lst[j + 1])
                        else:
                            try:
                                infections[region] = int(lst[j + 1])
                            except Exception:
                                infections[region] = int(lst[j].split(":")[1])
    return infections

def get_total_infected(line):
    split = line.split(" ")
    for word in split:
        if word.isdigit():
            return int(word)

def get_total_discarded(line):
    split = line.split(" ")
    for word in split:
        if word.isdigit():
            return int(word)

def extract_data_from_text(tl):
    date = ""
    time = ""
    confirmed = ""
    discarded = ""

    for i in range(len(tl)):
        if "Situac" in tl[i]:
            date = extract_date(tl[i])
        elif "horas" in tl[i]:
            time = extract_time(tl[i])
        elif "Casos confirmados" in tl[i]:
            confirmed = get_total_infected(tl[i])
        elif "Casos descartados" in tl[i]:
            discarded = get_total_discarded(tl[i])

    infections = extract_cases_by_region(tl)

    data = {"date": date, "time": time, "confirmed": confirmed, "discarded": discarded}
    data.update(infections)

    return data

def process_tweet(it, timestamp, print_itl=False):
    img_url = it["extended_entities"]["media"][0]["media_url"]
    urllib.request.urlretrieve(img_url, f"pulled_images/covid_update-{timestamp}.jpg")

    pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

    img = cv2.imread(f"covid_update-img.jpg")
    img_text = pytesseract.image_to_string(img)

    itl = img_text.split("\n")

    if print_itl:
        pprint(itl)

    data = extract_data_from_text(itl)

    return data


def check_discarded(data1, data2):
    try:
        if (data2["discarded"] > data1["discarded"]):
            d1 = str(data1["discarded"])
            d2 = str(data2["discarded"])
            d2 = list(d2)
            d1 = list(d1)
            new_d2 = d1[0]
            for i in range(1, len(d2)):
                new_d2 += d2[i]
            d2 = new_d2
            data2["discarded"] = int(d2)

        return data2
    except Exception:
        print("[-] Some Exception happened at discarded evaluation")
        pprint(data1)
        pprint(data2)

if __name__ == "__main__":
    config = load_config("config.conf")

    api = conf_api(config)

    tweets = get_tweets(api)

    entries = []

    important_tweets = []
    for tweet in tweets:
        t_json = tweet._json
        if "Reporte" in t_json["full_text"]:
            important_tweets.append(t_json)

    print("[*] Processing Tweet #1")

    it = important_tweets[0]
    data1 = process_tweet(it, "2020-03-15_13:10")

    entries.append(data1)

    for j in range(1, len(important_tweets)):
        print(f"[*] Processing Tweet #{j + 1}")
        it = important_tweets[j]
        if j == 3:
            data2 = process_tweet(it, "2020-03-14_19:20", print_itl=True)

        else:
            data2 = process_tweet(it, "2020-03-14_19:20")

            data2 = check_discarded(data1, data2)

            data1 = data2

            entries.append(data1)

    # pprint(entries)