import bcrypt

passwords = {
    "admin": "Chazz@26",
    "analyst": "Onneile_nkwe02",
    "viewer": "Lolly_02"
}

print("Use hashes on dashboard.py")
for user, pw in passwords.items():
    hash_code = bcrypt.hashpw(pw.encode(), bcrypt.gensalt())
    print(f'"{user}": {hash_code},')


#"admin": b'$2b$12$ZFR/dT0gq6NwZL2xissa2envUuQAGiFDR4aW.EJEo7fD425ZoKIhe',
#"analyst": b'$2b$12$KrhHzshMOzDhoB4TBRpJ1.SKT217LJuUQEpAFQ55xovI2fUzRqXTO',
#"viewer": b'$2b$12$Zk.yY.tJRQls1rE0i4pUVO8KmnzIt/8O87PzhSUVd4HpwRcskt6Ya',