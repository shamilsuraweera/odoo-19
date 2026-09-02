# Odoo 19 Development Environment Setup

Quick setup guide for running **Odoo 19 (Community + Enterprise)** on your local machine.

---

## 1. Folder Structure & Git Setup

To match the existing `.gitignore` configuration without any modifications, clone or extract the repositories directly into the designated folder names:

| Folder | Description |
| :--- | :--- |
| `odoo-c/` | Odoo 19 Community Edition source code |
| `odoo-e/` | Odoo 19 Enterprise Edition source code |
| `source-code/` | Archived source packages / tarballs |
| `backups/` | Pre-built database backup archives |
| `.venv/` | Python virtual environment |

### Cloning the Repositories
```bash
# Clone Odoo Community into 'odoo-c'
git clone https://github.com/odoo/odoo.git --depth 1 --branch 19.0 odoo-c

# Clone Odoo Enterprise into 'odoo-e' (requires access permissions)
git clone https://github.com/odoo/enterprise.git --depth 1 --branch 19.0 odoo-e
```

> **Note:** If you downloaded ZIP/tarball sources, extract and rename their root folders to `odoo-c` and `odoo-e` respectively.

---

## 2. Python Environment & Dependencies

1. **Create and activate a virtual environment:**
   - **Windows (PowerShell):**
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

2. **Install required dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r odoo-c/requirements.txt
   pip install -r odoo-e/requirements.txt
   ```

---

## 3. PostgreSQL Database Setup

1. Start your local PostgreSQL service.
2. Open `psql` or **pgAdmin Query Tool** and execute the queries from [`sql_queries.sql`](file:///c:/Users/shamil/Documents/odoo-19/sql_queries.sql):

```sql
-- Create odoo user with password
CREATE USER odoo WITH PASSWORD 'odoo';

-- Grant permission to create databases
ALTER USER odoo WITH CREATEDB;
```

---

## 4. Running Odoo

Run the server using the command in [`commands.txt`](file:///c:/Users/shamil/Documents/odoo-19/commands.txt):

```powershell
python odoo-c/odoo-bin -c odoo.conf
```

Once started, access Odoo at: [http://localhost:8069](http://localhost:8069)

---

## 5. Restoring Included Database Backups

Navigate to the Database Manager in your browser:  
👉 [http://localhost:8069/web/database/manager](http://localhost:8069/web/database/manager)

Click **Restore Database**, enter the **Master Password** (see [`passwords.txt`](file:///c:/Users/shamil/Documents/odoo-19/passwords.txt)), and upload one of the 3 pre-packaged backup files from the [`backups/`](file:///c:/Users/shamil/Documents/odoo-19/backups) folder:

1. **No Apps, No Data** (Clean base installation)  
   📁 `backups/odoo19_2026-07-13_22-13-23-no-apps.zip`
2. **All Apps, No Data** (All enterprise & community apps installed without dummy records)  
   📁 `backups/odoo19db_2026-08-11_10-40-28-all-apps-no-data.zip`
3. **All Apps, All Data** (Full installation with complete demo data)  
   📁 `backups/odoo19db_2026-08-11_11-05-27-all-apps-all-data.zip`

---

## 6. Helper Files Reference

- **[`passwords.txt`](../odoo-19/passwords.txt)**: Contains master passwords, superadmin credentials, and database user passwords.
- **[`sql_queries.sql`](../odoo-19/sql_queries.sql)**: Pre-written SQL statements to create/drop the `odoo` user and databases.
- **[`commands.txt`](../odoo-19/commands.txt)**: Startup command shortcut.
- **[`odoo.conf`](../odoo-19/odoo.conf)**: Central server configuration file (addons paths, DB credentials, dev modes, port settings).
