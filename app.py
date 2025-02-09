import streamlit as st
import sqlite3
import os
import random
from bcrypt import hashpw, gensalt, checkpw


# Initialize Database
def setup_database():
    if not os.path.exists("logs.db"):
        conn = sqlite3.connect("logs.db")
        cursor = conn.cursor()

        # Create Users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
        """)

        # Create Logs table with username column
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            action TEXT,
            platform TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Add default admin user
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            admin_password = hashpw("password".encode(), gensalt()).decode("utf-8")
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("admin", admin_password))

        conn.commit()
        conn.close()


# Mock Backend APIs
def create_vm_openstack(name, flavor, image):
    return {"status": "success", "vm_id": "os123", "name": name, "flavor": flavor, "image": image}


def list_vms_openstack():
    return [{"vm_id": "os123", "name": "OpenStack_VM", "status": "active"}]


def create_instance_aws(name, instance_type):
    return {"status": "success", "instance_id": "aws123", "name": name, "type": instance_type}


def list_instances_aws():
    return [{"instance_id": "aws123", "name": "AWS_Instance", "status": "running"}]


def create_instance_gcp(name, machine_type):
    return {"status": "success", "instance_id": "gcp123", "name": name, "type": machine_type}


def list_instances_gcp():
    return [{"instance_id": "gcp123", "name": "GCP_Instance", "status": "running"}]


def create_instance_azure(name, size):
    return {"status": "success", "instance_id": "azure123", "name": name, "size": size}


def list_instances_azure():
    return [{"instance_id": "azure123", "name": "Azure_Instance", "status": "running"}]


def generate_mock_metrics():
    return {
        "CPU Usage (%)": random.randint(10, 90),
        "Memory Usage (%)": random.randint(20, 80),
        "Disk Usage (%)": random.randint(5, 70),
    }


# Log Actions
def log_action(username, action, platform):
    conn = sqlite3.connect("logs.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO logs (username, action, platform, timestamp) VALUES (?, ?, ?, datetime('now'))",
        (username, action, platform)
    )
    conn.commit()
    conn.close()


# User Authentication Functions
def register_user(username, password):
    conn = sqlite3.connect("logs.db")
    cursor = conn.cursor()
    try:
        hashed_password = hashpw(password.encode(), gensalt()).decode("utf-8")
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        st.success("User registered successfully! You can now log in.")
    except sqlite3.IntegrityError:
        st.error("Username already exists. Please choose another.")
    conn.close()


def validate_user(username, password):
    conn = sqlite3.connect("logs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user:
        stored_password = user[2]
        return checkpw(password.encode("utf-8"), stored_password.encode("utf-8"))
    return False


# Main Streamlit App
def main():
    st.title("Self-Service Cloud APIs")

    # Sidebar for Authentication
    st.sidebar.header("Authentication")
    auth_mode = st.sidebar.radio("Choose an option", ["Login", "Register"])

    if auth_mode == "Register":
        # Registration Form
        st.sidebar.subheader("Register a New Account")
        new_username = st.sidebar.text_input("New Username")
        new_password = st.sidebar.text_input("New Password", type="password")
        if st.sidebar.button("Register"):
            if new_username and new_password:
                register_user(new_username, new_password)
            else:
                st.sidebar.error("Please fill in all fields.")

    elif auth_mode == "Login":
        # Login Form
        st.sidebar.subheader("Login to Your Account")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        login_button = st.sidebar.button("Login")

        if login_button:
            if validate_user(username, password):
                st.sidebar.success(f"Welcome, {username}!")
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
            else:
                st.sidebar.error("Invalid username or password.")

    # Main Dashboard (Accessible After Login)
    if "logged_in" in st.session_state and st.session_state["logged_in"]:
        username = st.session_state["username"]

        # Select Platform
        st.sidebar.header("Select Platform")
        platform = st.sidebar.radio("Platform", ["AWS", "OpenStack", "GCP", "Azure"])

        if platform == "AWS":
            st.header("AWS Operations")

            if st.button("Create Instance"):
                result = create_instance_aws("AWS_Test_Instance", "t2.micro")
                log_action(username, "Create Instance", "AWS")
                st.success(result)

            if st.button("List Instances"):
                result = list_instances_aws()
                st.write(result)

        elif platform == "OpenStack":
            st.header("OpenStack Operations")

            if st.button("Create VM"):
                result = create_vm_openstack("OpenStack_Test_VM", "m1.small", "Ubuntu")
                log_action(username, "Create VM", "OpenStack")
                st.success(result)

            if st.button("List VMs"):
                result = list_vms_openstack()
                st.write(result)

        elif platform == "GCP":
            st.header("GCP Operations")

            if st.button("Create Instance"):
                result = create_instance_gcp("GCP_Test_Instance", "n1-standard-1")
                log_action(username, "Create Instance", "GCP")
                st.success(result)

            if st.button("List Instances"):
                result = list_instances_gcp()
                st.write(result)

        elif platform == "Azure":
            st.header("Azure Operations")

            if st.button("Create Instance"):
                result = create_instance_azure("Azure_Test_Instance", "Standard_DS1_v2")
                log_action(username, "Create Instance", "Azure")
                st.success(result)

            if st.button("List Instances"):
                result = list_instances_azure()
                st.write(result)

        # Monitoring
        st.write("**Resource Monitoring**")
        metrics = generate_mock_metrics()
        st.metric(label="CPU Usage", value=f"{metrics['CPU Usage (%)']}%")
        st.metric(label="Memory Usage", value=f"{metrics['Memory Usage (%)']}%")
        st.metric(label="Disk Usage", value=f"{metrics['Disk Usage (%)']}%")

        # Logs
        st.sidebar.header("Logs")
        if st.sidebar.button("View Logs"):
            conn = sqlite3.connect("logs.db")
            cursor = conn.cursor()
            logs = cursor.execute("SELECT * FROM logs").fetchall()
            conn.close()
            st.sidebar.write(logs)

    else:
        st.warning("Please log in to access the platform.")


# Run Database Setup
setup_database()

# Run the App
if __name__ == "__main__":
    main()
