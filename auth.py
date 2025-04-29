import streamlit as st
import bcrypt
from database import init_database, register_user, get_user, update_user_password, add_security_question, verify_security_question

def auth_page():
    st.title("Waste Exchange Platform")
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if not st.session_state.logged_in:
        # Improved tabs with custom styling
        st.markdown("""
            <style>
            .stTabs [data-baseweb="tab-list"] {
                gap: 2rem;
                border-radius: 10px;
                background-color: #f0f8f3;
                padding: 0.5rem;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            }
            .stTabs [data-baseweb="tab"] {
                padding: 0.75rem 1.5rem;
                border-radius: 8px;
                color: #1a5d1a;
                font-weight: 500;
            }
            .stTabs [aria-selected="true"] {
                background-color: #2ecc71 !important;
                color: white !important;
                font-weight: 600;
            }
            </style>
        """, unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["Login", "Register", "Forgot Password"])
        
        with tab1:
            st.header("Login")
            with st.container():
                # Add a subtle card effect for the login form
                st.markdown("""
                    <style>
                    .login-container {
                        background: green;
                        
                        border-radius: 12px;
                        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                        margin-bottom: 15px;
                    }
                    </style>
                """, unsafe_allow_html=True)
                
                st.markdown('<div class="login-container">', unsafe_allow_html=True)
                login_email = st.text_input("Email", key="login_email", 
                                           placeholder="Enter your email")
                login_password = st.text_input("Password", type="password", key="login_password",
                                             placeholder="Enter your password")
                
                login_col1, login_col2 = st.columns([1, 1])
                with login_col1:
                    remember_me = st.checkbox("Remember me")
                
                login_btn = st.button("Login", type="primary", use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                if login_btn:
                    with st.spinner("Authenticating..."):
                        user = get_user(login_email)
                        if user and bcrypt.checkpw(login_password.encode('utf-8'), user['password']):
                            st.session_state.logged_in = True
                            st.session_state.username = user['username']
                            st.session_state.user_id = str(user['_id'])
                            st.success("Login successful! Redirecting...")
                            st.rerun()
                        else:
                            st.error("Invalid email or password")
        
        with tab2:
            st.header("Register")
            with st.container():
                # Add styled container for registration form
                st.markdown("""
                    <style>
                    .register-container {
                        background: white;
                        
                        border-radius: 12px;
                        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                        margin-bottom: 15px;
                    }
                    .password-requirements {
                        font-size: 0.8rem;
                        color: #6c757d;
                        background: #f8f9fa;
                        padding: 10px;
                        border-radius: 5px;
                        margin-top: 5px;
                    }
                    </style>
                """, unsafe_allow_html=True)
                
                st.markdown('<div class="register-container">', unsafe_allow_html=True)
                reg_username = st.text_input("Username", key="reg_username", 
                                           placeholder="Choose a username")
                reg_email = st.text_input("Email", key="reg_email", 
                                        placeholder="Enter your email")
                
                reg_col1, reg_col2 = st.columns(2)
                with reg_col1:
                    reg_password = st.text_input("Password", type="password", key="reg_password", 
                                               placeholder="Create a password")
                with reg_col2:
                    reg_confirm_password = st.text_input("Confirm Password", type="password", 
                                                       key="reg_confirm_password", 
                                                       placeholder="Confirm your password")
                
                # Password strength indicator
                if reg_password:
                    strength = 0
                    suggestions = []
                    
                    if len(reg_password) >= 8:
                        strength += 1
                    else:
                        suggestions.append("Password should be at least 8 characters long")
                        
                    if any(c.isdigit() for c in reg_password):
                        strength += 1
                    else:
                        suggestions.append("Include at least one number")
                        
                    if any(c.isupper() for c in reg_password):
                        strength += 1
                    else:
                        suggestions.append("Include at least one uppercase letter")
                        
                    if any(not c.isalnum() for c in reg_password):
                        strength += 1
                    else:
                        suggestions.append("Include at least one special character")
                    
                    # Display strength
                    strength_text = ["Weak", "Fair", "Good", "Strong"]
                    strength_color = ["#dc3545", "#ffc107", "#6c757d", "#28a745"]
                    progress_val = (strength / 4) * 100
                    
                    st.progress(progress_val/100, text=f"Password Strength: {strength_text[strength-1] if strength > 0 else 'Very Weak'}")
                    
                    if suggestions:
                        st.markdown(f"""
                            <div class="password-requirements">
                                <b>Password Requirements:</b><br>
                                {"<br>".join(f"• {s}" for s in suggestions)}
                            </div>
                        """, unsafe_allow_html=True)

                # Security question for password recovery
                sec_question = st.selectbox(
                    "Choose a security question",
                    [
                        "What is your favorite food?",
                        "What was your first pet's name?",
                        "What is your mother's maiden name?",
                        "What city were you born in?",
                        "What was the name of your first school?"
                    ],
                    key="sec_question"
                )
                sec_answer = st.text_input("Your answer", key="sec_answer", 
                                         placeholder="Answer to security question")
                
                reg_terms = st.checkbox("I agree to the Terms and Conditions")
                
                register_btn = st.button("Register", type="primary", use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                if register_btn:
                    if not reg_terms:
                        st.error("You must agree to the Terms and Conditions")
                    elif not reg_username or not reg_email or not reg_password or not sec_answer:
                        st.error("All fields are required")
                    elif reg_password != reg_confirm_password:
                        st.error("Passwords do not match")
                    elif strength < 2:
                        st.error("Please create a stronger password")
                    else:
                        with st.spinner("Creating your account..."):
                            hashed = bcrypt.hashpw(reg_password.encode('utf-8'), bcrypt.gensalt())
                            success, message = register_user(reg_username, reg_email, hashed)
                            
                            if success:
                                # Add security question
                                user = get_user(reg_email)
                                if user:
                                    add_security_question(str(user['_id']), sec_question, sec_answer)
                                    st.success("Registration successful! You can now log in.")
                                else:
                                    st.error("User created but security question could not be saved.")
                            else:
                                st.error(message)
        
        with tab3:
            st.header("Forgot Password")
            with st.container():
                # Add styled container for password recovery
                st.markdown("""
                    <style>
                    .recovery-container {
                        background: red;
                        
                        border-radius: 12px;
                        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                        margin-bottom: 15px;
                    }
                    </style>
                """, unsafe_allow_html=True)
                
                st.markdown('<div class="recovery-container">', unsafe_allow_html=True)
                recovery_step = st.session_state.get('recovery_step', 1)
                
                if recovery_step == 1:
                    recovery_email = st.text_input("Email", key="recovery_email", 
                                                 placeholder="Enter your email")
                    verify_email_btn = st.button("Verify Email", type="primary", use_container_width=True)
                    
                    if verify_email_btn:
                        user = get_user(recovery_email)
                        if user:
                            st.session_state.recovery_user = user
                            st.session_state.recovery_step = 2
                            st.rerun()
                        else:
                            st.error("Email not found in our records")
                
                elif recovery_step == 2:
                    st.info(f"Please answer your security question")
                    user = st.session_state.recovery_user
                    
                    # Get security question from user record
                    security_question = user.get('security_question', "What is your favorite food?")
                    st.write(f"**Question:** {security_question}")
                    
                    security_answer = st.text_input("Your answer", key="recovery_answer", 
                                                  placeholder="Enter your answer", type="password")
                    verify_answer_btn = st.button("Verify Answer", type="primary", use_container_width=True)
                    
                    if verify_answer_btn:
                        if verify_security_question(str(user['_id']), security_answer):
                            st.session_state.recovery_step = 3
                            st.rerun()
                        else:
                            st.error("Incorrect answer")
                
                elif recovery_step == 3:
                    st.success("Identity verified! Create a new password.")
                    
                    new_password = st.text_input("New Password", type="password", key="new_password", 
                                               placeholder="Enter new password")
                    confirm_new_password = st.text_input("Confirm New Password", type="password", 
                                                       key="confirm_new_password", 
                                                       placeholder="Confirm new password")
                    
                    # Password strength indicator (reusing code from registration section)
                    if new_password:
                        strength = 0
                        suggestions = []
                        
                        if len(new_password) >= 8:
                            strength += 1
                        else:
                            suggestions.append("Password should be at least 8 characters long")
                            
                        if any(c.isdigit() for c in new_password):
                            strength += 1
                        else:
                            suggestions.append("Include at least one number")
                            
                        if any(c.isupper() for c in new_password):
                            strength += 1
                        else:
                            suggestions.append("Include at least one uppercase letter")
                            
                        if any(not c.isalnum() for c in new_password):
                            strength += 1
                        else:
                            suggestions.append("Include at least one special character")
                        
                        # Display strength
                        strength_text = ["Weak", "Fair", "Good", "Strong"]
                        strength_color = ["#dc3545", "#ffc107", "#6c757d", "#28a745"]
                        progress_val = (strength / 4) * 100
                        
                        st.progress(progress_val/100, text=f"Password Strength: {strength_text[strength-1] if strength > 0 else 'Very Weak'}")
                        
                        if suggestions:
                            st.markdown(f"""
                                <div class="password-requirements">
                                    <b>Password Requirements:</b><br>
                                    {"<br>".join(f"• {s}" for s in suggestions)}
                                </div>
                            """, unsafe_allow_html=True)
                    
                    reset_password_btn = st.button("Reset Password", type="primary", use_container_width=True)
                    
                    if reset_password_btn:
                        if not new_password or not confirm_new_password:
                            st.error("Please enter and confirm your new password")
                        elif new_password != confirm_new_password:
                            st.error("Passwords do not match")
                        elif strength < 2:
                            st.error("Please create a stronger password")
                        else:
                            with st.spinner("Resetting your password..."):
                                user = st.session_state.recovery_user
                                hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                                success, message = update_user_password(str(user['_id']), hashed)
                                
                                if success:
                                    st.success("Password reset successful! You can now log in with your new password.")
                                    # Reset recovery state
                                    for key in ['recovery_step', 'recovery_user']:
                                        if key in st.session_state:
                                            del st.session_state[key]
                                else:
                                    st.error(f"Error resetting password: {message}")
                
                # Add back button for the recovery process
                if recovery_step > 1:
                    if st.button("← Back", key="recovery_back"):
                        st.session_state.recovery_step = recovery_step - 1
                        st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Add footer with a hint to switch between tabs
        st.markdown("""
            <div style="text-align: center; margin-top: 30px; color: #6c757d; font-size: 0.9rem;">
                Use the tabs above to login, register, or recover your password
            </div>
        """, unsafe_allow_html=True)
        
        return False
    
    return True