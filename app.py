import streamlit as st
import os
import json
from datetime import datetime
import time
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities import *


# File paths
USERS_FILE = "config.yaml"
POSTS_DIR = "posts"
UPLOADS_DIR = "uploads"

# Ensure necessary directories exist
os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Load users from file
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as file:
            config = yaml.load(file, Loader=SafeLoader)
    return config

# Load session from file
def load_session():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            return json.load(f)
    return {}

# Save session to file
def save_session(username):
    with open(SESSION_FILE, "w") as f:
        json.dump({"username": username}, f)

# Clear session
def clear_session():
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

# Authenticate user
def authenticate(username, password):
    users = load_users()
    if username in users and users[username] == password:
        return True
    return False

# Load posts from files
def load_posts():
    posts = []
    for filename in os.listdir(POSTS_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(POSTS_DIR, filename), "r") as f:
                post = json.load(f)
                posts.append(post)
    return sorted(posts, key=lambda x: x["timestamp"], reverse=True)

# Save a post to a file
def save_post(post):
    filename = f"{post['id']}.json"
    with open(os.path.join(POSTS_DIR, filename), "w") as f:
        json.dump(post, f)

# Delete a post and its associated image
def delete_post(post_id):
    post_file = os.path.join(POSTS_DIR, f"{post_id}.json")
    if os.path.exists(post_file):
        os.remove(post_file)
    image_file = os.path.join(UPLOADS_DIR, f"{post_id}.png")
    if os.path.exists(image_file):
        os.remove(image_file)

# Generate a unique post ID
def generate_post_id():
    return str(int(datetime.now().timestamp()))

# Filter posts by label
def filter_posts_by_label(posts, label):
    return [post for post in posts if label in post["labels"]]

# Filter posts by search text
def filter_posts_by_search(posts, search_text):
    search_text = search_text.lower()
    return [
        post
        for post in posts
        if search_text in post["title"].lower() or search_text in post["content"].lower()
    ]

# Get all unique labels from posts
def get_all_labels(posts):
    labels = set()
    for post in posts:
        labels.update(post["labels"])
    return sorted(labels)

# Main app
def main():
    st.title("CMS as a Blog")

    # Load session
    # session = load_session()
    # if "username" in session:
    #     st.session_state.username = session["username"]

    # Load users
    config = load_users()

    # Creating the authenticator object
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )

    # Initialize selected label in session state
    if "selected_label" not in st.session_state:
        st.session_state.selected_label = None

    # Initialize search text in session state
    if "search_text" not in st.session_state:
        st.session_state.search_text = ""

    # Handle label filtering from URL query parameters
    if hasattr(st, "query_params"):
        query_params = st.query_params
        if "label" in query_params:
            st.session_state.selected_label = query_params["label"]
            st.rerun()

    # Load posts
    posts = load_posts()

    with st.sidebar:
        try:
            authenticator.login()
        except LoginError as e:
            st.error(e)

        # Authenticating user
        if st.session_state['authentication_status']:
            authenticator.logout()
            if st.session_state.username:
                st.write(f'Welcome *{st.session_state["name"]}*')
        elif st.session_state['authentication_status'] is False:
            st.error('Username/password is incorrect')
        elif st.session_state['authentication_status'] is None:
            st.warning('Please enter your username and password')

        # Saving config file
        with open('../config.yaml', 'w', encoding='utf-8') as file:
            yaml.dump(config, file, default_flow_style=False, allow_unicode=True)


    

    # Free text search input in the sidebar
    st.sidebar.header("Search Posts")
    search_text = st.sidebar.text_input("Search by title or content", value=st.session_state.search_text)
    if search_text != st.session_state.search_text:
        st.session_state.search_text = search_text
        st.rerun()

    # Display all labels in the sidebar
    st.sidebar.header("Labels")
    all_labels = get_all_labels(posts)
    for label in all_labels:
        if st.sidebar.button(label, key=f"label_{label}"):
            st.session_state.selected_label = label
            st.session_state.search_text = ""  # Clear search text when a label is clicked
            st.rerun()

    # Clear label filter button
    if st.session_state.selected_label or st.session_state.search_text:
        if st.sidebar.button("Clear Filters"):
            st.session_state.selected_label = None
            st.session_state.search_text = ""  # Clear search text
            st.rerun()

    # Post creation form
    if st.session_state.username:
        with st.expander("Create New Post"):
            title = st.text_input("Title")
            content = st.text_area("Content (Markdown supported)")
            labels = st.text_input("Labels (comma-separated)")
            image = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg"], key="create_image")
            if st.button("Publish"):
                if title and content:
                    post_id = generate_post_id()
                    post = {
                        "id": post_id,
                        "title": title,
                        "content": content,
                        "labels": [label.strip() for label in labels.split(",")],
                        "author": st.session_state.username,
                        "timestamp": datetime.now().isoformat(),
                    }
                    save_post(post)
                    if image:
                        with open(os.path.join(UPLOADS_DIR, f"{post_id}.png"), "wb") as f:
                            f.write(image.getbuffer())
                    st.success("Post published!")
                    st.rerun()
                else:
                    st.error("Title and content are required")

    # Filter posts by label or search text
    if st.session_state.selected_label:
        posts = filter_posts_by_label(posts, st.session_state.selected_label)
        st.write(f"Showing posts with label: **{st.session_state.selected_label}**")
    elif st.session_state.search_text:
        posts = filter_posts_by_search(posts, st.session_state.search_text)
        st.write(f"Showing posts containing: **{st.session_state.search_text}**")

    # Display posts
    for post in posts:
        st.markdown(f"### {post['title']}")
        st.caption(f"By {post['author']} on {post['timestamp']}")
        if os.path.exists(os.path.join(UPLOADS_DIR, f"{post['id']}.png")):
            st.image(os.path.join(UPLOADS_DIR, f"{post['id']}.png"))
        st.markdown(post["content"])

        # Display clickable labels
        labels_html = " ".join(
            f'<span style="border: 1px solid #ccc; padding: 5px; margin: 2px; border-radius: 5px; cursor: pointer;" onclick="window.location.href=\'?label={label}\'">{label}</span>'
            for label in post["labels"]
        )
        st.markdown(labels_html, unsafe_allow_html=True)

        # Edit and delete options for the author
        if post["author"] == st.session_state.username:
            with st.expander("Edit Post"):
                new_title = st.text_input("Title", value=post["title"], key=f"title_{post['id']}")
                new_content = st.text_area("Content", value=post["content"], key=f"content_{post['id']}")
                new_labels = st.text_input("Labels", value=",".join(post["labels"]), key=f"labels_{post['id']}")
                new_image = st.file_uploader("Upload New Image", type=["png", "jpg", "jpeg"], key=f"image_{post['id']}")
                if st.button("Update Post", key=f"update_{post['id']}"):
                    post["title"] = new_title
                    post["content"] = new_content
                    post["labels"] = [label.strip() for label in new_labels.split(",")]
                    save_post(post)
                    if new_image:
                        with open(os.path.join(UPLOADS_DIR, f"{post['id']}.png"), "wb") as f:
                            f.write(new_image.getbuffer())
                    st.success("Post updated!")
                    st.rerun()
            popover = st.popover("Delete Post")
            iamsure = popover.checkbox("Are you sure to want to delete this post?", False, key=f"sure_{post['id']}")
            if iamsure:
                delete_post(post["id"])
                st.success("Post deleted!")
                st.rerun()

if __name__ == "__main__":
    main()