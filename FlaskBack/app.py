from flask import Flask, request, jsonify
from flask_cors import CORS
import random 
import pickle
import ipaddress
import re
import urllib.request
from bs4 import BeautifulSoup
import socket
import requests
import whois
from datetime import date, datetime
from dateutil.parser import parse as date_parse
from urllib.parse import urlparse
import ipaddress
import tldextract

app = Flask(__name__)
CORS(app)

# # Load the model from the pickle file
# with open('gradient_boosting_model.pkl', 'rb') as model_file:
#     loaded_model = pickle.load(model_file)

# # Input URL
# url = "https://www.google.com/search?sca_esv=570824042&q=Cricket+World+Cup&oi=ddle&ct=258250781&hl=en-GB&si=ALGXSlZS0YT-iRe81F2cKC9lM9KWTK4y0m5Atx8g9YliNNw2meNqPtE-K8lRFYYPrhwmSx-u0DodTY3iqTMTnbKkEHARHZi9cENGop5mAmczrlqBj_mfuZM%3D&sa=X&ved=0ahUKEwi8yNbG5d2BAxUMZ94KHdtTBxIQPQgC&biw=1536&bih=750&dpr=1.25"  # Replace with the URL you want to predict


# import ipaddress
# import re
# import urllib.request
# from bs4 import BeautifulSoup
# import socket
# import requests
# import google
# import whois
# from datetime import date, datetime
# import time
# from dateutil.parser import parse as date_parse
# from urllib.parse import urlparse

# Function to extract the domain from a URL
def getDomain(url):
    domain = urlparse(url).netloc
    if re.match(r"^www.", domain):
        domain = domain.replace("www.", "")
    return domain

# Checks for IP address in URL (Have_IP) -- 1(phishing)/0(legitimate)
def havingIP(url):
    try:
        ipaddress.ip_address(url)
        ip = 1
    except:
        ip = 0
    return ip

# Checks the presence of @ in URL (Have_At) -- 1(phishing)/0(legitimate)
def haveAtSign(url):
    if "@" in url:
        at = 1
    else:
        at = 0
    return at

# Finding the length of URL and categorizing (URL_Length) -- 1(phishing)/0(legitimate)
def getLength(url):
    if len(url) < 54:
        length = 0
    else:
        length = 1
    return length

# Gives the number of '/' in URL (URL_Depth) -- if depth is greater than 4, it might be phishing
def getDepth(url):
    s = urlparse(url).path.split('/')
    depth = 0
    for j in range(len(s)):
        if len(s[j]) != 0:
            depth = depth + 1
    return depth

# Checking for redirection '//' in the url (Redirection) -- 1(phishing)/0(legitimate)
def redirection(url):
    pos = url.rfind('//')
    if pos > 6:
        if pos > 7:
            return 1
        else:
            return 0
    else:
        return 0

# Existence of “HTTPS” Token in the Domain Part of the URL (https_Domain) -- 1(phishing)/0(legitimate)
def httpDomain(url):
    domain = urlparse(url).netloc
    if 'https' in domain:
        return 1
    else:
        return 0

# Checking for Shortening Services in URL (Tiny_URL)
shortening_services = r"bit\.ly|goo\.gl|shorte\.st|go2l\.ink|x\.co|ow\.ly|t\.co|tinyurl|tr\.im|is\.gd|cli\.gs|" \
                      r"yfrog\.com|migre\.me|ff\.im|tiny\.cc|url4\.eu|twit\.ac|su\.pr|twurl\.nl|snipurl\.com|" \
                      r"short\.to|BudURL\.com|ping\.fm|post\.ly|Just\.as|bkite\.com|snipr\.com|fic\.kr|loopt\.us|" \
                      r"doiop\.com|short\.ie|kl\.am|wp\.me|rubyurl\.com|om\.ly|to\.ly|bit\.do|t\.co|lnkd\.in|db\.tt|" \
                      r"qr\.ae|adf\.ly|goo\.gl|bitly\.com|cur\.lv|tinyurl\.com|ow\.ly|bit\.ly|ity\.im|q\.gs|is\.gd|" \
                      r"po\.st|bc\.vc|twitthis\.com|u\.to|j\.mp|buzurl\.com|cutt\.us|u\.bb|yourls\.org|x\.co|" \
                      r"prettylinkpro\.com|scrnch\.me|filoops\.info|vzturl\.com|qr\.net|1url\.com|tweez\.me|v\.gd|" \
                      r"tr\.im|link\.zip\.net"

def tinyURL(url):
    match = re.search(shortening_services, url)
    if match:
        return 1
    else:
        return 0

# Function to calculate the age of a domain
def get_domain_age(url):
    domain_info = tldextract.extract(url)
    domain_name = f"{domain_info.domain}.{domain_info.suffix}"

    try:
        domain_info = whois.whois(domain_name)

        if isinstance(domain_info.creation_date, list):
            creation_date = domain_info.creation_date[0]
        else:
            creation_date = domain_info.creation_date

        if isinstance(domain_info.expiration_date, list):
            expiration_date = domain_info.expiration_date[0]
        else:
            expiration_date = domain_info.expiration_date

        if isinstance(creation_date, datetime) and isinstance(expiration_date, datetime):
            age_of_domain = (expiration_date - creation_date).days
            today = datetime.now()
            end = abs((expiration_date - today).days)
            if (((age_of_domain / 30) < 6) or end < 6):
                return 0  # Suspicious
            else:
                return 1  # Not suspicious

    except Exception as e:
        return 0  # Suspicious on error

    return 0  # Default to suspicious if no valid dates found

# Function to check for iframe redirection
def check_iframe_redirection(url):
    try:
        response = requests.get(url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            iframe_tags = soup.find_all('iframe')

            for iframe in iframe_tags:
                iframe_src = iframe.get('src')
                if iframe_src and iframe_src != url:
                    return 1  # iframe redirection detected
            
            return 0  # No redirection found

        else:
            return -1  # Indicates an error occurred during the request

    except Exception as e:
        return -1  # Indicates an error occurred during the request

# Function to check for mouse over effect
def mouseOver(url):
    try:
        response = requests.get(url)

        if response.status_code == 200:
            if re.findall("<script>.+onmouseover.+</script>", response.text):
                return 1  # Mouse over effect detected
            else:
                return 0  # No mouse over effect detected

        else:
            return -1  # Indicates an error occurred during the request

    except Exception as e:
        return -1  # Indicates an error occurred during the request

# Function to check for right-click disable
def disablerightClick(url):
    try:
        response = requests.get(url)

        if response.status_code == 200:
            if re.findall(r"event.button ?== ?2", response.text):
                return 0  # Right-click disabled
            else:
                return 1  # Right-click enabled

        else:
            return -1  # Indicates an error occurred during the request

    except Exception as e:
        return -1  # Indicates an error occurred during the request

# Function to check for URL forwarding
def forwarding(url):
    try:
        response = requests.get(url, allow_redirects=False)

        if response.status_code == 200:
            if len(response.history) > 0:
                return 1  # URL forwarding detected
            else:
                return 0  # No URL forwarding detected

        else:
            return -1  # Indicates an error occurred during the request

    except Exception as e:
        return -1  # Indicates an error occurred during the request

def extract_anchor_tags(url):
    hrefs = []

    try:
        # Send a GET request to the URL
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the HTML content of the page
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all anchor (<a>) elements in the HTML
            anchor_tags = soup.find_all('a')

            # Extract and print the href and text content of clickable anchor tags
            for anchor in anchor_tags:
                href = anchor.get('href')

                # Check if the anchor tag has an href attribute (clickable link)
                if href:
                    # Use a regular expression to check if the href starts with http or https
                    if re.match(r'^https?://', href):
                        hrefs.append(href)
            print(hrefs)

        else:
            print(f"Failed to fetch URL. Status code: {response.status_code}")

    except Exception as e:
        print(f"Error: {e}")

    return hrefs



class FeatureExtraction:
    features = []

    
    def __init__(self,url):
        self.url = url
        try:
            self.response = requests.get(url, timeout=5)
            self.soup = BeautifulSoup(self.response.text, 'html.parser')
        except:
            self.response = None
            self.soup = None

        try:
            self.urlparse = urlparse(url)
            self.domain = self.urlparse.netloc
        except:
            self.urlparse = None
            self.domain = ""

        try:
            self.whois_response = whois.whois(self.domain)
        except:
            self.whois_response = None


        self.features = [
            self.UsingIp(),
            self.longUrl(),
            self.shortUrl(),
            self.symbol(),
            self.redirecting(),
            self.prefixSuffix(),
            self.SubDomains(),
            self.Hppts(),
            self.DomainRegLen(),
            self.Favicon(),
            self.NonStdPort(),
            self.HTTPSDomainURL(),
            self.RequestURL(),
            self.AnchorURL(),
            self.LinksInScriptTags(),
            self.ServerFormHandler(),
            self.InfoEmail(),
            self.AbnormalURL(),
            self.WebsiteForwarding(),
            self.StatusBarCust(),
            self.DisableRightClick(),
            self.UsingPopupWindow(),
            self.IframeRedirection(),
            self.AgeofDomain(),
            self.DNSRecording(),
            self.WebsiteTraffic(),
            self.PageRank(),
            self.GoogleIndex(),
            self.LinksPointingToPage(),
            self.StatsReport()
        ]

        try:
            self.response = requests.get(url)
            self.soup = BeautifulSoup(self.response.text, 'html.parser')
        except:
            pass

        try:
            self.urlparse = urlparse(url)
            self.domain = self.urlparse.netloc
        except:
            pass

        try:
            self.whois_response = whois.whois(self.domain)
        except:
            pass


     # 1.UsingIp
    def UsingIp(self):
        try:
            ipaddress.ip_address(self.url)
            return -1
        except:
            return 1

    # 2.longUrl
    def longUrl(self):
        if len(self.url) < 54:
            return 1
        if len(self.url) >= 54 and len(self.url) <= 75:
            return 0
        return -1

    # 3.shortUrl
    def shortUrl(self):
        match = re.search(r'bit\.ly|goo\.gl|shorte\.st|go2l\.ink|x\.co|ow\.ly|t\.co|tinyurl|tr\.im|is\.gd|cli\.gs|'
                    r'yfrog\.com|migre\.me|ff\.im|tiny\.cc|url4\.eu|twit\.ac|su\.pr|twurl\.nl|snipurl\.com|'
                    r'short\.to|BudURL\.com|ping\.fm|post\.ly|Just\.as|bkite\.com|snipr\.com|fic\.kr|loopt\.us|'
                    r'doiop\.com|short\.ie|kl\.am|wp\.me|rubyurl\.com|om\.ly|to\.ly|bit\.do|t\.co|lnkd\.in|'
                    r'db\.tt|qr\.ae|adf\.ly|goo\.gl|bitly\.com|cur\.lv|tinyurl\.com|ow\.ly|bit\.ly|ity\.im|'
                    r'q\.gs|is\.gd|po\.st|bc\.vc|twitthis\.com|u\.to|j\.mp|buzurl\.com|cutt\.us|u\.bb|yourls\.org|'
                    r'x\.co|prettylinkpro\.com|scrnch\.me|filoops\.info|vzturl\.com|qr\.net|1url\.com|tweez\.me|v\.gd|tr\.im|link\.zip\.net', self.url)
        if match:
            return -1
        return 1

    # 4.Symbol@
    def symbol(self):
        if re.findall("@",self.url):
            return -1
        return 1
    
    # 5.Redirecting//
    def redirecting(self):
        if self.url.rfind('//')>6:
            return -1
        return 1
    
    # 6.prefixSuffix
    def prefixSuffix(self):
        try:
            match = re.findall(r'\-', self.domain)
            if match:
                return -1
            return 1
        except:
            return -1
    
    # 7.SubDomains
    def SubDomains(self):
        dot_count = len(re.findall(r'\.', self.url))
        if dot_count == 1:
            return 1
        elif dot_count == 2:
            return 0
        return -1

    # 8.HTTPS
    def Hppts(self):
        try:
            https = self.urlparse.scheme
            if 'https' in https:
                return 0
            return -1
        except:
            return 1

    # 9.DomainRegLen
    def DomainRegLen(self):
        try:
            expiration_date = self.whois_response.expiration_date
            creation_date = self.whois_response.creation_date
            try:
                if(len(expiration_date)):
                    expiration_date = expiration_date[0]
            except:
                pass
            try:
                if(len(creation_date)):
                    creation_date = creation_date[0]
            except:
                pass

            age = (expiration_date.year-creation_date.year)*12+ (expiration_date.month-creation_date.month)
            if age >=12:
                return 1
            return -1
        except:
            return -1

    # 10. Favicon
    def Favicon(self):
        try:
            for head in self.soup.find_all('head'):
                for head.link in self.soup.find_all('link', href=True):
                    dots = [x.start(0) for x in re.finditer(r'\.', head.link['href'])]
                    if self.url in head.link['href'] or len(dots) == 1 or domain in head.link['href']:
                        return 1
            return -1
        except:
            return -1

    # 11. NonStdPort
    def NonStdPort(self):
        try:
            port = self.domain.split(":")
            if len(port)>1:
                return -1
            return 1
        except:
            return -1

    # 12. HTTPSDomainURL
    def HTTPSDomainURL(self):
        try:
            if 'https' in self.domain:
                return -1
            return 1
        except:
            return -1
    
    # 13. RequestURL
    i, success = 0, 0
    def RequestURL(self):
        try:
            for img in self.soup.find_all('img', src=True):
                dots = [x.start(0) for x in re.finditer(r'\.', img['src'])]
                if self.url in img['src'] or self.domain in img['src'] or len(dots) == 1:
                    success = success + 1
                i = i+1

            for audio in self.soup.find_all('audio', src=True):
                dots = [x.start(0) for x in re.finditer(r'\.', audio['src'])]
                if self.url in audio['src'] or self.domain in audio['src'] or len(dots) == 1:
                    success = success + 1
                i = i+1

            for embed in self.soup.find_all('embed', src=True):
                dots = [x.start(0) for x in re.finditer(r'\.', embed['src'])]
                if self.url in embed['src'] or self.domain in embed['src'] or len(dots) == 1:
                    success = success + 1
                i = i+1

            for iframe in self.soup.find_all('iframe', src=True):
                dots = [x.start(0) for x in re.finditer(r'\.', iframe['src'])]
                if self.url in iframe['src'] or self.domain in iframe['src'] or len(dots) == 1:
                    success = success + 1
                i = i+1

            try:
                percentage = success/float(i) * 100
                if percentage < 22.0:
                    return 1
                elif((percentage >= 22.0) and (percentage < 61.0)):
                    return 0
                else:
                    return -1
            except:
                return 0
        except:
            return -1
    
    # 14. AnchorURL
    def AnchorURL(self):
        try:
            i,unsafe = 0,0
            for a in self.soup.find_all('a', href=True):
                if "#" in a['href'] or "javascript" in a['href'].lower() or "mailto" in a['href'].lower() or not (url in a['href'] or self.domain in a['href']):
                    unsafe = unsafe + 1
                i = i + 1

            try:
                percentage = unsafe / float(i) * 100
                if percentage < 31.0:
                    return 1
                elif ((percentage >= 31.0) and (percentage < 67.0)):
                    return 0
                else:
                    return -1
            except:
                return -1

        except:
            return -1

    # 15. LinksInScriptTags
    def LinksInScriptTags(self):
        try:
            i,success = 0,0
        
            for link in self.soup.find_all('link', href=True):
                dots = [x.start(0) for x in re.finditer(r'\.', link['href'])]
                if self.url in link['href'] or self.domain in link['href'] or len(dots) == 1:
                    success = success + 1
                i = i+1

            for script in self.soup.find_all('script', src=True):
                dots = [x.start(0) for x in re.finditer(r'\.', script['src'])]
                if self.url in script['src'] or self.domain in script['src'] or len(dots) == 1:
                    success = success + 1
                i = i+1

            try:
                percentage = success / float(i) * 100
                if percentage < 17.0:
                    return 1
                elif((percentage >= 17.0) and (percentage < 81.0)):
                    return 0
                else:
                    return -1
            except:
                return 0
        except:
            return -1

    # 16. ServerFormHandler
    def ServerFormHandler(self):
        try:
            if len(self.soup.find_all('form', action=True))==0:
                return 1
            else :
                for form in self.soup.find_all('form', action=True):
                    if form['action'] == "" or form['action'] == "about:blank":
                        return -1
                    elif self.url not in form['action'] and self.domain not in form['action']:
                        return 0
                    else:
                        return 1
        except:
            return -1

    # 17. InfoEmail
    def InfoEmail(self):
        try:
            if re.findall(r"[mail\(\)|mailto:?]", str(self.soup)):
                return -1
            else:
                return 1
        except:
            return -1

    # 18. AbnormalURL
    def AbnormalURL(self):
        try:
            if self.response.text == self.whois_response:
                return 1
            else:
                return -1
        except:
            return -1

    # 19. WebsiteForwarding
    def WebsiteForwarding(self):
        try:
            if len(self.response.history) <= 1:
                return 1
            elif len(self.response.history) <= 4:
                return 0
            else:
                return -1
        except:
             return -1

    # 20. StatusBarCust
    def StatusBarCust(self):
        try:
            if re.findall("<script>.+onmouseover.+</script>", self.response.text):
                return 1
            else:
                return -1
        except:
             return -1

    # 21. DisableRightClick
    def DisableRightClick(self):
        try:
            if re.findall(r"event.button ?== ?2", self.response.text):
                return 1
            else:
                return -1
        except:
             return -1

    # 22. UsingPopupWindow
    def UsingPopupWindow(self):
        try:
            if re.findall(r"alert\(", self.response.text):
                return 1
            else:
                return -1
        except:
             return -1

    # 23. IframeRedirection
    def IframeRedirection(self):
        try:
            if re.search(r"<iframe|frameBorder", self.response.text, re.IGNORECASE):
                return 1
            else:
                return -1
        except:
             return -1

    # 24. AgeofDomain
    def AgeofDomain(self):
        try:
            creation_date = self.whois_response.creation_date
            try:
                if(len(creation_date)):
                    creation_date = creation_date[0]
            except:
                pass

            today  = date.today()
            age = (today.year-creation_date.year)*12+(today.month-creation_date.month)
            if age >=6:
                return 1
            return -1
        except:
            return -1

    # 25. DNSRecording    
    def DNSRecording(self):
        try:
            creation_date = self.whois_response.creation_date
            try:
                if(len(creation_date)):
                    creation_date = creation_date[0]
            except:
                pass

            today  = date.today()
            age = (today.year-creation_date.year)*12+(today.month-creation_date.month)
            if age >=6:
                return 1
            return -1
        except:
            return -1

    # 26. WebsiteTraffic   
    def WebsiteTraffic(self):
        try:
            rank = BeautifulSoup(urllib.request.urlopen("http://data.alexa.com/data?cli=10&dat=s&url=" + self.url).read(), "xml").find("REACH")['RANK']
            if (int(rank) < 100000):
                return 1
            return 0
        except :
            return -1

    # 27. PageRank
    def PageRank(self):
        try:
            prank_checker_response = requests.post("https://www.checkpagerank.net/index.php", {"name": self.domain})

            global_rank = int(re.findall(r"Global Rank: ([0-9]+)", prank_checker_response.text)[0])
            if global_rank > 0 and global_rank < 100000:
                return 1
            return -1
        except:
            return -1
            

    # 28. GoogleIndex
    def GoogleIndex(self):
        try:
            query = f"site:{self.url}"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(f"https://www.google.com/search?q={query}", headers=headers)
            if "did not match any documents" in response.text:
                return -1
            else:
                return 1
        except:
            return 1

    # 29. LinksPointingToPage
    def LinksPointingToPage(self):
        try:
            number_of_links = len(re.findall(r"<a href=", self.response.text))
            if number_of_links == 0:
                return 1
            elif number_of_links <= 2:
                return 0
            else:
                return -1
        except:
            return -1

    # 30. StatsReport
    def StatsReport(self):
        try:
            url_match = re.search(
        r'at\.ua|usa\.cc|baltazarpresentes\.com\.br|pe\.hu|esy\.es|hol\.es|sweddy\.com|myjino\.ru|96\.lt|ow\.ly', self.url)
            ip_address = socket.gethostbyname(self.domain)
            ip_match = re.search(r'146\.112\.61\.108|213\.174\.157\.151|121\.50\.168\.88|192\.185\.217\.116|78\.46\.211\.158|181\.174\.165\.13|46\.242\.145\.103|121\.50\.168\.40|83\.125\.22\.219|46\.242\.145\.98|'
                                r'107\.151\.148\.44|107\.151\.148\.107|64\.70\.19\.203|199\.184\.144\.27|107\.151\.148\.108|107\.151\.148\.109|119\.28\.52\.61|54\.83\.43\.69|52\.69\.166\.231|216\.58\.192\.225|'
                                r'118\.184\.25\.86|67\.208\.74\.71|23\.253\.126\.58|104\.239\.157\.210|175\.126\.123\.219|141\.8\.224\.221|10\.10\.10\.10|43\.229\.108\.32|103\.232\.215\.140|69\.172\.201\.153|'
                                r'216\.218\.185\.162|54\.225\.104\.146|103\.243\.24\.98|199\.59\.243\.120|31\.170\.160\.61|213\.19\.128\.77|62\.113\.226\.131|208\.100\.26\.234|195\.16\.127\.102|195\.16\.127\.157|'
                                r'34\.196\.13\.28|103\.224\.212\.222|172\.217\.4\.225|54\.72\.9\.51|192\.64\.147\.141|198\.200\.56\.183|23\.253\.164\.103|52\.48\.191\.26|52\.214\.197\.72|87\.98\.255\.18|209\.99\.17\.27|'
                                r'216\.38\.62\.18|104\.130\.124\.96|47\.89\.58\.141|78\.46\.211\.158|54\.86\.225\.156|54\.82\.156\.19|37\.157\.192\.102|204\.11\.56\.48|110\.34\.231\.42', ip_address)
            if url_match:
                return -1
            elif ip_match:
                return -1
            return 1
        except:
            return 1
    
    def getFeaturesList(self):
        return self.features


@app.route('/')
def index():
    return "PhishNet API is running. Use the /analyze_url endpoint to POST your data."

@app.route('/analyze_url', methods=['POST'])
def analyze_url():
    try:
        # Get the JSON data from the request
        data = request.json
        url = data['url']

        # Load the machine learning model
        with open('gradient_boosting_model.pkl', 'rb') as model_file:
            loaded_model = pickle.load(model_file)

        # Feature extraction
        feature_extractor = FeatureExtraction(url)
        features = feature_extractor.getFeaturesList()

        # Display all the features and their values
        feature_names = [
            "UsingIp", "longUrl", "shortUrl", "symbol", "redirecting",
            "prefixSuffix", "SubDomains", "Hppts", "DomainRegLen", "Favicon",
            "NonStdPort", "HTTPSDomainURL", "RequestURL", "AnchorURL",
            "LinksInScriptTags", "ServerFormHandler", "InfoEmail", "AbnormalURL",
            "WebsiteForwarding", "StatusBarCust", "DisableRightClick",
            "UsingPopupWindow", "IframeRedirection", "AgeofDomain", "DNSRecording",
            "WebsiteTraffic", "PageRank", "GoogleIndex", "LinksPointingToPage", "StatsReport"
        ]

        print("Feature Extraction Results:")
        for feature_name, feature_value in zip(feature_names, features):
            print(f"{feature_name}: {feature_value}")

        suspicious_flags_count = sum(1 for feature in features if feature == -1)
        print("\nSuspicious Flags Count:", suspicious_flags_count)

        prediction_score = (suspicious_flags_count / len(feature_names)) * 100
        print("Prediction Score (Custom Features):", prediction_score, "%")

        # Use the loaded model to get the probability score
        model_probability_score = loaded_model.predict_proba([features])[0][1]  # Assuming malicious class at index 1

        print("Model Probability Score:", model_probability_score)

        # Combine the scores (you can adjust the weights as needed)
        combined_score = (0.8 * prediction_score) + (0.2 * model_probability_score)

        print("Combined Prediction Score:", combined_score)

        # Make the final prediction based on the combined score
        if combined_score >= 50:
            result = "The website is suspicious."
        else:
            result = "The website is safe."

        # Check if the number of suspicious flags is in the range [17, 18]
        if suspicious_flags_count >= 17:
            caution = "Caution! Suspicious website detected"
        else:
            caution = "We guess it is a safe website"

        response_data = {
            "message": "Analysis complete",
            "result": result,
            "caution": caution,
            "prediction_score": (100 - prediction_score),
            "model_probability_score": (100 - model_probability_score),
            "combined_score": (100 - combined_score)
        }

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

'''
-----------------------------------------
All the methods for predicting
whether the domain entered is
phishing or not
-----------------------------------------
'''
@app.route('/tickNotTick', methods=['POST'])
def tickNotTick():
    try:
        data = request.json
        url = data['url']

        domain = getDomain(url)
        ip = havingIP(domain)
        at = haveAtSign(url)
        length = getLength(url)
        depth = getDepth(url)
        redirect = redirection(url)
        https_domain = httpDomain(url)
        tiny_url = tinyURL(url)
        phishing_count = sum([ip, at, length, depth > 4, redirect, https_domain == 0, tiny_url])

        dom = get_domain_age(url)
        redr = check_iframe_redirection(url)
        mo = mouseOver(url)
        disright = disablerightClick(url)
        fwd = forwarding(url)
        extracted_anchors = extract_anchor_tags(url)
        phishing_count_html = sum([redr, mo, disright, fwd])

        total_triggers = sum([phishing_count, phishing_count_html, dom])
        result_conclusion = ''
        if total_triggers > 7:
            result_conclusion = "Website may be suspicious"
        else:
            result_conclusion = "Website may be safe"

        domain_info = whois.whois(domain)
        response_data = {
            "message": "Analysis complete",
            "result_conclusion": result_conclusion,
            "domain": domain,  # Include domain
            "ip": ip,  # Include IP presence
            "at_sign": at,  # Include @ presence
            "url_length": length,  # Include URL length
            "url_depth": depth,  # Include URL depth
            "redirection": redirect,  # Include redirection presence
            "https_domain": https_domain,  # Include HTTPS in domain presence
            "tiny_url": tiny_url,  # Include tiny URL presence
            "iframe_redirection": redr,  # Include iframe redirection
            "mouse_over_effect": mo,  # Include mouse over effect
            "right_click_disabled": disright,  # Include right-click disabled
            "url_forwarding": fwd,  # Include URL forwarding
            "whois_data": domain_info, # who is data alll
            "extracted_anchors":extracted_anchors, #acnhor tag
            "triggers": {
                "feature_extraction_triggers": phishing_count,
                "whois_triggers": dom,
                "html_js_triggers": phishing_count_html,
                "total_triggers": total_triggers
            },
        }
        print(response_data)
        return jsonify(response_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True)

# with open('gradient_boosting_model.pkl', 'rb') as model_file:
#     loaded_model = pickle.load(model_file)    
# feature_extractor = FeatureExtraction(url)
# features = feature_extractor.getFeaturesList()    
# # Display all the features and their values
# feature_names = [
#     "UsingIp", "longUrl", "shortUrl", "symbol", "redirecting",
#     "prefixSuffix", "SubDomains", "Hppts", "DomainRegLen", "Favicon",
#     "NonStdPort", "HTTPSDomainURL", "RequestURL", "AnchorURL",
#     "LinksInScriptTags", "ServerFormHandler", "InfoEmail", "AbnormalURL",
#     "WebsiteForwarding", "StatusBarCust", "DisableRightClick",
#     "UsingPopupWindow", "IframeRedirection", "AgeofDomain", "DNSRecording",
#     "WebsiteTraffic", "PageRank", "GoogleIndex", "LinksPointingToPage", "StatsReport"
# ]

# print("Feature Extraction Results:")
# for feature_name, feature_value in zip(feature_names, features):
#     print(f"{feature_name}: {feature_value}")

# suspicious_flags_count = sum(1 for feature in features if feature == -1)
# print("\nSuspicious Flags Count:", suspicious_flags_count)

# prediction_score = (suspicious_flags_count / len(feature_names)) * 100
# print("Prediction Score (Custom Features):", prediction_score, "%")

# # Use the loaded model to get the probability score
# model_probability_score = loaded_model.predict_proba([features])[0][1]  # Assuming the probability for the "malicious" class is at index 1

# print("Model Probability Score:", model_probability_score)

# # Combine the scores (you can adjust the weights as needed)
# combined_score = (0.8 * prediction_score) + (0.2 * model_probability_score)

# print("Combined Prediction Score:", combined_score)

# # Make the final prediction based on the combined score
# if combined_score >= 50:
#     print("The website is suspicious.")
# else:
#     print("The website is safe.")

# # Check if the number of suspicious flags is in the range [17, 18]
# if suspicious_flags_count >= 17:
#     print("Caution! Suspicious website detected")
# else:
#     print("We guess it is a safe website")
