# Static Evaluation: Base vs. Fine-Tuned Model

This document compares the raw text output of the base TinyLlama model against the model fine-tuned on our custom command-line dataset.

---

## 1. List all the files which were modified in the last 5 minutes on my linux system.

### Base Model Output:
```bash
$ ls -lh | grep -i modified
-rw-r--r-- 1 root root 104857600 Jan 15 14:59 /home/user/Documents/test.txt
-rw-r--r-- 1 root root 104857600 Jan 15 14:59 /home/user/Documents/test2.txt
-rw-r--r-- 1 root root 104857600 Jan 15 14:59 /home/user/Documents/test3.txt
-rw-r--r-- 1 root root 104857600 Jan 15 14:59 /home/user/Documents/test4.txt
-rw-r--r-- 1 root root 104857600 Jan 15 14:59 /home/user/Documents/test5.txt
```

**Explanation:**
The `ls -lh` command is used to list the size of each file in

### Fine-Tuned Model Output:
```bash
ls -l /var/log/ | grep -iE '^[0-9]{5}\s'
```

This will list all the files which were modified in the last 5 minutes.

### Reference Answer:
```bash
find / -type f -mmin -5 2>/dev/null
```

**ROUGE-L Score:** 0.0625

---

## 2. How to add a user directly into linux by editing /etc/passwd.

### Base Model Output:
```
To add a user directly into linux by editing /etc/passwd, follow these steps:

1. Open the file /etc/passwd in your text editor of choice.
2. Locate the line that contains the username you want to add.
3. Replace the username with the new username you want to add.
4. Save the file.
5. Restart the Linux system to apply the changes.

That's it! Your new user has been added to the system.
```

### Fine-Tuned Model Output:
```
To add a user directly into linux by editing /etc/passwd, you need to have root privileges.

1. Open the file /etc/passwd with the `sudo` command.

   sudo nano /etc/passwd

2. Add the user you want to add to the file.

   root:x:0:0:root:/root:/bin/bash

3. Save the file and exit.

   exit

4. Restart the system to apply the changes.

   sudo systemctl restart passwd

5. Check if the user was added by running the `id` command.

   id root

   You should see the user's ID.

6. Check if the user is now a member of the `sudo` group.

   id root

   You should see the user's ID.

7. Check if the user is now a member of the `root` group.

   id root
```

### Reference Answer:
Add a line in `/etc/passwd` like: `username:x:1001:1001::/home/username:/bin/bash`.

**ROUGE-L Score:** 0.0986

---