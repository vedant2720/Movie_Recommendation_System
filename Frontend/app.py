import streamlit as st
import requests
import os
from config import occupation_map

API_URL = "http://127.0.0.1:5000"

# --- Page Config ---
st.set_page_config(page_title="Netflix AI", layout="wide", initial_sidebar_state="collapsed")

# --- Precision CSS for No Gaps ---
st.markdown("""
    <style>
    /* 1. Remove Streamlit's default top padding */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }
    header {visibility: hidden;}
    
    .stApp { background-color: #111; color: white; }
    
    /* 2. Vertically align the Logo and Buttons */
    [data-testid="column"] {
        display: flex;
        align-items: center; /* Vertical centering within the row */
    }

    /* Movie Poster Styling */
    img {
        width: 100% !important;
        height: 300px !important;
        object-fit: cover !important;
        border-radius: 4px;
    }

    .movie-title { 
        font-size: 13px; font-weight: 500; margin-top: 5px; 
        color: #fff; text-align: left;
    }
    
    /* Netflix Red Button */
    div.stButton > button {
        background-color: #e50914 !important;
        color: white !important;
        border: none !important;
        height: 40px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Session State ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_data" not in st.session_state:
    st.session_state.user_data = None
if "active_page" not in st.session_state:
    st.session_state.active_page = "Home"

def set_page(page_name):
    st.session_state.active_page = page_name

# --- Helper: Grid ---

def display_movie_grid(movies, header_text):
    st.write(f"### {header_text}")
    if not movies:
        st.info("No movies found.")
        return

    for i in range(0, len(movies), 5):
        cols = st.columns(5)
        chunk = movies[i : i + 5]

        for idx, m in enumerate(chunk):
            with cols[idx]:
                poster = m.get("poster_url")

                if poster and os.path.exists(poster):
                    st.image(poster)
                else:
                    st.image("https://via.placeholder.com/300x450/222222/eeeeee?text=No+Poster")

                st.markdown(
                    f"<p class='movie-title'>{m['title']}</p>",
                    unsafe_allow_html=True
                )


# --- Header Row (Everything in line) ---
# We use st.columns to keep the logo and button on the same horizontal plane
header_col1, header_col2, header_col3 = st.columns([2, 5, 2])

with header_col1:
    # Logo stays flush left
    st.markdown("<h1 style='color: #e50914; margin:0; padding:0; line-height:1;'>NETFLIX</h1>", unsafe_allow_html=True)

with header_col3:
    # Auth items stay flush right
    if not st.session_state.logged_in:
        if st.session_state.active_page == "Home":
            if st.button("Sign In", use_container_width=True):
                set_page("Login")
                st.rerun()
        else:
            if st.button("Home", use_container_width=True):
                set_page("Home")
                st.rerun()
    else:
        # Show username and logout in a tight layout
        col_user, col_logout = st.columns([1, 1])
        col_user.write(f"👤 {st.session_state.user_data['username']}")
        if col_logout.button("Sign Out"):
            st.session_state.logged_in = False
            st.session_state.user_data = None
            set_page("Home")
            st.rerun()

st.markdown("---") # Visual separator

# --- Logic: Routing ---
if st.session_state.active_page == "Login":
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.subheader("Sign In")
        with st.form("login_form"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In", use_container_width=True):
                res = requests.post(f"{API_URL}/login", json={"username": u, "password": p})
                if res.status_code == 200:
                    st.session_state.logged_in = True
                    st.session_state.user_data = res.json()
                    set_page("Home")
                    st.rerun()
                else: st.error("Invalid Login")
        if st.button("Create an account"):
            set_page("Signup")
            st.rerun()

elif st.session_state.active_page == "Signup":
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.subheader("Join Netflix")
        with st.form("signup_form"):
            nu = st.text_input("Username")
            ne = st.text_input("Email")
            np = st.text_input("Password", type="password")
            gen = st.selectbox("Gender", ["M", "F"])
            age = st.number_input("Age", 18, 100, 25)
            occ_label = st.selectbox("Occupation", options=list(occupation_map.values()))
            if st.form_submit_button("Start Membership", use_container_width=True):
                occ_id = next(k for k, v in occupation_map.items() if v == occ_label)
                payload = {"username": nu, "email": ne, "password": np, "gender": 1 if gen=="M" else 0, "age": age, "occupation": occ_id}
                res = requests.post(f"{API_URL}/signup", json=payload)
                if res.status_code == 201:
                    set_page("Login")
                    st.rerun()

else: # Home Page
    if st.session_state.logged_in:
        user = st.session_state.user_data
        try:
            res = requests.post(f"{API_URL}/recommend/{user['user_id']}", json=user)
            if res.status_code == 200:
                display_movie_grid(res.json().get("movies", []), f"Recommended for {user['username']}")
        except: pass
    
    # Trending Section
    try:
        resp = requests.get(f"{API_URL}/random_movies")
        if resp.status_code == 200:
            display_movie_grid(resp.json(), "Trending Now")
    except:
        st.error("Backend is offline.")