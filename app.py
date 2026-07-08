import os
import sqlite3
import uuid
from datetime import datetime, timezone
from flask import Flask, jsonify, request, render_template_string, current_app, has_app_context, session
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.environ.get("DATABASE", "tickets.db")


def get_db_connection():
    database_path = DB_PATH
    if has_app_context():
        database_path = current_app.config.get("DATABASE", DB_PATH)
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_id TEXT NOT NULL UNIQUE,
            school_name TEXT NOT NULL,
            requestor_designation TEXT NOT NULL,
            issue_category TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            consent_given INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.commit()
    conn.close()


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=DB_PATH,
        TESTING=False,
        SECRET_KEY=os.environ.get("SECRET_KEY", "it-department-secret"),
    )
    if test_config:
        app.config.update(test_config)

    def is_it_department_user():
        return session.get("department") == "IT"

    @app.route("/")
    def index():
        return render_template_string("""
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>ICT Ticketing System</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; background: #f4f7fb; color: #1d2939; font-size: 18px; }
                .container { max-width: 1200px; margin: 0 auto; padding: 24px; }
                .card { background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 8px 24px rgba(0,0,0,0.06); }
                form { display: grid; gap: 14px; }
                label { font-weight: 600; }
                input, select, textarea, button { font-size: 15px; padding: 10px; border-radius: 8px; border: 1px solid #ccd7e2; }
                button { background: #2563eb; color: white; border: none; cursor: pointer; }
                table { width: 100%; border-collapse: collapse; }
                th, td { border-bottom: 1px solid #e5e7eb; padding: 10px; text-align: left; }
                .status { font-weight: 700; }
                .status.pending { color: #b45309; }
                .status.in-progress { color: #1d4ed8; }
                .status.resolved { color: #15803d; }
                .toolbar { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 12px; }
                .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }
                .metric { background: #eff6ff; padding: 16px; border-radius: 10px; }
                .pill { display: inline-block; padding: 6px 10px; border-radius: 999px; background: #dbeafe; }
                .brand { display: flex; align-items: center; gap: 14px; margin-bottom: 12px; }
                .brand-logo { width: 64px; height: 64px; border-radius: 12px; object-fit: cover; box-shadow: 0 4px 12px rgba(0,0,0,0.12); background: #dbeafe; border: 2px dashed #2563eb; display: flex; align-items: center; justify-content: center; color: #2563eb; font-size: 12px; font-weight: 700; text-align: center; line-height: 1.2; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="card">
                    <div class="brand">
                        <img class="brand-logo" src="/static/deped city of naga logo.png" alt="DepEd City of Naga logo">
                        <div>
                            <h2 style="margin:0;">DepEd City of Naga</h2>
                            <h1 style="margin:4px 0 0;">ICT Support Hub</h1>
                            <p style="margin:6px 0 0;">Fast. Reliable. Digital Support for Schools.</p>
                        </div>
                    </div>
                </div>
                <div class="card">
                    <h2>Ticket Information Portal</h2>
                    <form id="ticket-form">
                        <label>School Name</label>
                        <input name="school_name" required>
                        <label>Requestor Designation</label>
                        <select name="requestor_designation" required>
                            <option value="Teacher">Teacher</option>
                            <option value="School Head">School Head</option>
                        </select>
                        <label>Issue Category</label>
                        <select name="issue_category" required>
                            <option value="Internet/Connectivity">Internet/Connectivity</option>
                            <option value="Hardware Repair">Hardware Repair</option>
                            <option value="Learning Resource Platform">Learning Resource Platform</option>
                            <option value="System Account Reset">System Account Reset</option>
                        </select>
                        <label>Description</label>
                        <textarea name="description" rows="4" required></textarea>
                        <label><input type="checkbox" name="consent" value="true"> I consent to the storage and handling of this ticket for IT support purposes.</label>
                        <button type="submit">Submit Ticket</button>
                    </form>
                    <div id="form-message" style="margin-top:12px;"></div>
                </div>
                <div class="card">
                    <h2>IT Department Access</h2>
                    <form id="login-form">
                        <label>Username</label>
                        <input name="username" required>
                        <label>Password</label>
                        <input type="password" name="password" required>
                        <button type="submit">Access Dashboard</button>
                    </form>
                    <div id="access-message" style="margin-top:12px;"></div>
                </div>
                <div class="card" id="dashboard-section" style="display:none;">
                    <h2>IT Dashboard</h2>
                    <div class="toolbar">
                        <input id="filter-school" placeholder="Filter by school">
                        <select id="filter-category">
                            <option value="">All categories</option>
                            <option value="Internet/Connectivity">Internet/Connectivity</option>
                            <option value="Hardware Repair">Hardware Repair</option>
                            <option value="Learning Resource Platform">Learning Resource Platform</option>
                            <option value="System Account Reset">System Account Reset</option>
                        </select>
                    </div>
                    <table>
                        <thead>
                            <tr>
                                <th>Tracking ID</th>
                                <th>School</th>
                                <th>Category</th>
                                <th>Status</th>
                                <th>Updated</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody id="ticket-table"></tbody>
                    </table>
                </div>
                <div class="card">
                    <h2>M&E Analytics</h2>
                    <div class="summary" id="analytics-summary"></div>
                </div>
            </div>
            <script>
                const state = { tickets: [] };
                const form = document.getElementById('ticket-form');
                const loginForm = document.getElementById('login-form');
                const tableBody = document.getElementById('ticket-table');
                const analyticsSummary = document.getElementById('analytics-summary');
                const schoolFilter = document.getElementById('filter-school');
                const categoryFilter = document.getElementById('filter-category');
                const formMessage = document.getElementById('form-message');
                const accessMessage = document.getElementById('access-message');
                const dashboardSection = document.getElementById('dashboard-section');

                async function loadTickets() {
                    const res = await fetch('/api/tickets');
                    if (!res.ok) {
                        return;
                    }
                    const data = await res.json();
                    state.tickets = data;
                    render();
                }

                async function loadAnalytics() {
                    const res = await fetch('/api/analytics');
                    if (!res.ok) {
                        return;
                    }
                    const data = await res.json();
                    analyticsSummary.innerHTML = `
                        <div class="metric"><strong>Total Tickets Received</strong><div>${data.total_tickets}</div></div>
                        <div class="metric"><strong>Resolution Rate</strong><div>${data.resolution_rate}%</div></div>
                        <div class="metric"><strong>High-Volume Risk Indicator</strong><div>${data.risk_indicator}</div></div>
                    `;
                }

                function render() {
                    const schoolQuery = schoolFilter.value.toLowerCase();
                    const categoryQuery = categoryFilter.value;
                    const filtered = state.tickets.filter(ticket => {
                        const matchesSchool = ticket.school_name.toLowerCase().includes(schoolQuery);
                        const matchesCategory = !categoryQuery || ticket.issue_category === categoryQuery;
                        return matchesSchool && matchesCategory;
                    });
                    tableBody.innerHTML = filtered.map(ticket => `
                        <tr>
                            <td>${ticket.tracking_id}</td>
                            <td>${ticket.school_name}</td>
                            <td>${ticket.issue_category}</td>
                            <td class="status ${ticket.status.toLowerCase().replace(/\\s+/g, '-')}">${ticket.status}</td>
                            <td>${ticket.updated_at}</td>
                            <td>
                                <select data-id="${ticket.id}" class="status-select">
                                    <option value="Pending" ${ticket.status === 'Pending' ? 'selected' : ''}>Pending</option>
                                    <option value="In Progress" ${ticket.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
                                    <option value="Resolved" ${ticket.status === 'Resolved' ? 'selected' : ''}>Resolved</option>
                                </select>
                            </td>
                        </tr>
                    `).join('');
                }

                form.addEventListener('submit', async (event) => {
                    event.preventDefault();
                    const formData = new FormData(form);
                    const payload = Object.fromEntries(formData.entries());
                    const res = await fetch('/api/tickets', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                    const data = await res.json();
                    formMessage.innerHTML = `<span class="pill">Ticket ${data.tracking_id} saved successfully.</span>`;
                    form.reset();
                });

                loginForm.addEventListener('submit', async (event) => {
                    event.preventDefault();
                    const formData = new FormData(loginForm);
                    const payload = new URLSearchParams(formData);
                    const res = await fetch('/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                        body: payload
                    });
                    if (res.ok) {
                        loginForm.style.display = 'none';
                        dashboardSection.style.display = 'block';
                        accessMessage.innerHTML = '<span class="pill">IT Dashboard unlocked.</span>';
                        await loadTickets();
                        await loadAnalytics();
                    } else {
                        dashboardSection.style.display = 'none';
                        accessMessage.innerHTML = '<span class="pill">Invalid IT Department credentials.</span>';
                    }
                });

                tableBody.addEventListener('change', async (event) => {
                    if (event.target.classList.contains('status-select')) {
                        const id = event.target.dataset.id;
                        const status = event.target.value;
                        await fetch(`/api/tickets/${id}/status`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ status })
                        });
                        await loadTickets();
                        await loadAnalytics();
                    }
                });

                [schoolFilter, categoryFilter].forEach(element => element.addEventListener('input', render));
                [schoolFilter, categoryFilter].forEach(element => element.addEventListener('change', render));
            </script>
        </body>
        </html>
        """)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()
            stored_hash = generate_password_hash("ITDept2026!")
            if username == "itdepartment" and check_password_hash(stored_hash, password):
                session["department"] = "IT"
                session["username"] = username
                return jsonify({"message": "IT Dashboard access granted"}), 200
            return jsonify({"error": "Invalid IT Department credentials"}), 401
        return jsonify({"message": "Use the IT Department login form"}), 200

    @app.route("/api/tickets", methods=["GET", "POST"])
    def tickets():
        if request.method == "GET":
            if not is_it_department_user():
                return jsonify({"error": "IT Department access required"}), 403
            conn = get_db_connection()
            rows = conn.execute(
                "SELECT id, tracking_id, school_name, issue_category, status, updated_at FROM tickets ORDER BY created_at DESC"
            ).fetchall()
            conn.close()
            return jsonify([dict(row) for row in rows])

        payload = request.get_json(silent=True) or {}
        required_fields = ["school_name", "requestor_designation", "issue_category", "description"]
        for field in required_fields:
            if not payload.get(field, "").strip():
                return jsonify({"error": f"{field} is required"}), 400
        if payload.get("consent") is not True and payload.get("consent") != "true":
            return jsonify({"error": "consent is required to submit a ticket"}), 400

        tracking_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc).isoformat()
        conn = get_db_connection()
        cursor = conn.execute(
            """
            INSERT INTO tickets (
                tracking_id, school_name, requestor_designation, issue_category, description, created_at, updated_at, consent_given
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (tracking_id, payload["school_name"].strip(), payload["requestor_designation"].strip(), payload["issue_category"].strip(), payload["description"].strip(), now, now, 1),
        )
        conn.commit()
        ticket_id = cursor.lastrowid
        conn.close()
        return jsonify({"ticket_id": ticket_id, "tracking_id": tracking_id, "status": "Pending"}), 201

    @app.route("/api/tickets/<int:ticket_id>/status", methods=["POST"])
    def update_status(ticket_id):
        if not is_it_department_user():
            return jsonify({"error": "IT Department access required"}), 403
        payload = request.get_json(silent=True) or {}
        status = payload.get("status", "Pending")
        if status not in {"Pending", "In Progress", "Resolved"}:
            return jsonify({"error": "Invalid status"}), 400
        now = datetime.now(timezone.utc).isoformat()
        conn = get_db_connection()
        cursor = conn.execute(
            "UPDATE tickets SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, ticket_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        conn.close()
        if row is None:
            return jsonify({"error": "Ticket not found"}), 404
        return jsonify(dict(row))

    @app.route("/api/analytics")
    def analytics():
        if not is_it_department_user():
            return jsonify({"error": "IT Department access required"}), 403
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM tickets").fetchall()
        conn.close()

        total_tickets = len(rows)
        resolved_tickets = sum(1 for row in rows if row["status"] == "Resolved")
        resolution_rate = round((resolved_tickets / total_tickets) * 100, 2) if total_tickets else 0.0

        category_counts = {}
        school_counts = {}
        for row in rows:
            category_counts[row["issue_category"]] = category_counts.get(row["issue_category"], 0) + 1
            school_counts[row["school_name"]] = school_counts.get(row["school_name"], 0) + 1

        risk_source = "No tickets yet"
        if rows:
            most_common = None
            if category_counts and sum(category_counts.values()) >= sum(school_counts.values()):
                most_common = max(category_counts.items(), key=lambda item: item[1])
                risk_source = f"Category: {most_common[0]} ({most_common[1]} tickets)"
            else:
                most_common = max(school_counts.items(), key=lambda item: item[1])
                risk_source = f"School: {most_common[0]} ({most_common[1]} tickets)"

        return jsonify({
            "total_tickets": total_tickets,
            "resolved_tickets": resolved_tickets,
            "resolution_rate": resolution_rate,
            "risk_indicator": risk_source,
        })

    @app.before_request
    def ensure_db():
        init_db()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
