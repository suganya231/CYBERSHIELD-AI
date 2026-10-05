import re
import math
import random
import string

COMMON_PASSWORDS = {
    "123456","password","qwerty","admin","letmein",
    "welcome","abc123","password123","123456789"
}

KEYBOARD_PATTERNS = [
    "123456","123456789","qwerty","asdfgh",
    "zxcvbn","qwertyuiop","asdf"
]

SPECIAL = "!@#$%^&*()_+-=[]{}<>?"

def generate_password(length=16):
    chars = string.ascii_letters + string.digits + SPECIAL

    while True:
        pwd = ''.join(random.choice(chars) for _ in range(length))

        if (re.search(r"[A-Z]", pwd)
            and re.search(r"[a-z]", pwd)
            and re.search(r"[0-9]", pwd)
            and re.search(r"[!@#$%^&*()_+\-=\[\]{}<>?]", pwd)):
            return pwd


def calculate_entropy(password):

    charset = 0

    if re.search(r"[a-z]", password):
        charset += 26

    if re.search(r"[A-Z]", password):
        charset += 26

    if re.search(r"[0-9]", password):
        charset += 10

    if re.search(r"[!@#$%^&*()_+\-=\[\]{}<>?]", password):
        charset += len(SPECIAL)

    if charset == 0:
        return 0

    return round(len(password) * math.log2(charset),2)


def crack_time(entropy):

    if entropy < 30:
        return "Instant"

    elif entropy < 45:
        return "Few Minutes"

    elif entropy < 60:
        return "Few Days"

    elif entropy < 80:
        return "Several Years"

    else:
        return "Millions of Years"


def analyze_password(password, username=""):

    score = 0
    suggestions = []
    issues = []

    if len(password) >= 14:
        score += 25
    elif len(password) >= 10:
        score += 18
    elif len(password) >= 8:
        score += 10
    else:
        suggestions.append("Increase password length.")

    if re.search(r"[A-Z]", password):
        score += 15
    else:
        suggestions.append("Add uppercase letter.")

    if re.search(r"[a-z]", password):
        score += 15
    else:
        suggestions.append("Add lowercase letter.")

    if re.search(r"[0-9]", password):
        score += 15
    else:
        suggestions.append("Add numbers.")

    if re.search(r"[!@#$%^&*()_+\-=\[\]{}<>?]", password):
        score += 20
    else:
        suggestions.append("Add special characters.")

    lower = password.lower()

    if lower in COMMON_PASSWORDS:
        issues.append("Common Password")
        score -= 40

    for p in KEYBOARD_PATTERNS:
        if p in lower:
            issues.append("Keyboard Pattern")
            score -= 20
            break

    if re.search(r"(.)\1\1", password):
        issues.append("Repeated Characters")
        score -= 15

    if username and username.lower() in lower:
        issues.append("Contains Username")
        score -= 20

    score = max(0,min(100,score))

    entropy = calculate_entropy(password)

    if score < 40:
        strength = "WEAK"
        risk = "HIGH"

    elif score < 75:
        strength = "MEDIUM"
        risk = "MEDIUM"

    else:
        strength = "STRONG"
        risk = "LOW"

    return {

        "strength":strength,
        "risk":risk,
        "score":score,
        "entropy":entropy,
        "crack_time":crack_time(entropy),
        "issues":issues,
        "suggestions":suggestions,
        "generated_password":generate_password()

    }


if __name__=="__main__":

    result = analyze_password("Abi123","abi")

    for k,v in result.items():
        print(k,":",v)