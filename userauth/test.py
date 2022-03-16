import bcrypt

def hashingPw(pw):
    pw = pw.encode('utf-8')
    salt = bcrypt.gensalt()
    hash = bcrypt.hashpw(pw, salt)
    
    return hash
print("on")
print(bcrypt.checkpw(("abcd").encode('utf-8'), hashingPw("abcd")))