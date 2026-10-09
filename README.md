# Computer and Network Security Project (COMP 5370/6370)
*Lanie Louque, Grayson Morgan, Laura Joy Simpson, Courtney Lin*

## Project Overview
**Secure File Sharing System**

*A file sharing app that works over a Local Area Network connection.*

---

### Deliverable 1 
We aimed to create the main database and established that the basic file transfer functions worked.

Right now, our app has these features:

- File Uploads/Downloads
- SHA256 File Checksums
- Audit Log Entries
- File Validation Logic

We are still working on these features:

- Identity and Access Control:
    - User account creation/deletion
    - Account login functions
    - Account password changing
    - Sharing file access with other users

The topography of our app looks like this so far:

```text
File_Share/
├── database_files/
│   ├── ___init___.py
│   ├── db_main.py
│   └── db_operations.py
├── uploaded_files/
│   └── (Files uploaded to app)
├── downloaded_files/
│   └── (Files downloaded from app over LAN)
├── main.py
├── validation.py
└── README.md
```

---