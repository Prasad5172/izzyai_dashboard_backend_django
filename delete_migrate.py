import os
import shutil

def delete_migrations():
    project_root = os.path.dirname(os.path.abspath(__file__))  # Get the project root
    target_apps = ["adminer", "authentication", "clinic", "slp","notification","payment","sales_director","sales_person"]  # List of apps to target

    # Walk through the directories
    for root, dirs, files in os.walk(project_root):
        # Check if the folder is a part of one of the target apps and contains a migrations folder
        if any(app in root.split(os.sep) for app in target_apps) and "migrations" in dirs:
            migrations_path = os.path.join(root, "migrations")
            shutil.rmtree(migrations_path)
            print(f"Deleted: {migrations_path}")

if __name__ == "__main__":
    delete_migrations()
