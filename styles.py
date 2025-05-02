"""
CSS styles for the waste management application.
Contains all the styling used across the app components.
"""

# Main application CSS
main_css = """
<style>
.header {
    padding: 1.5rem;
    background: linear-gradient(135deg, #4CAF50, #2196F3);
    border-radius: 10px;
    color: white;
    text-align: center;
    margin-bottom: 1.5rem;
}
.admin-card {
    padding: 15px;
    margin-bottom: 15px;
    border-radius: 5px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    background-color: #f9f9f9;
}
.admin-card h4 {
    color: #333;
    margin-top: 0;
}
.stTabs [data-baseweb="tab-list"] > [role="tab"]:first-child [data-testid="stMarkdownContainer"] p {
    font-size: 1.2em;
    font-weight: bold;
    color: green;
}
.stTabs [data-baseweb="tab-list"] > [role="tab"]:nth-child(2) [data-testid="stMarkdownContainer"] p {
    font-size: 1.2em;
    font-weight: bold;
    color: orange;
}
.stTabs [data-baseweb="tab-list"] > [role="tab"]:nth-child(3) [data-testid="stMarkdownContainer"] p {
    font-size: 1.2em;
    font-weight: bold;
    color: red;
}

.waste-report-card {
    background-color: #f9f9f9;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 15px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.waste-report-title {
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 5px;
}
.waste-report-location {
    color: #666;
    font-size: 14px;
    margin-bottom: 5px;
}
.waste-report-metadata {
    display: flex;
    gap: 15px;
    margin-bottom: 10px;
    font-size: 14px;
    color: #555;
}
.waste-report-description {
    margin-bottom: 10px;
}
.waste-report-actions {
    display: flex;
    gap: 10px;
}
.bbmp-tag {
    background-color: #FFC107;
    color: #000;
    font-size: 12px;
    padding: 2px 8px;
    border-radius: 4px;
    margin-right: 10px;
}
.resolved-tag {
    background-color: #4CAF50;
    color: white;
    font-size: 12px;
    padding: 2px 8px;
    border-radius: 4px;
}
.comment-box {
    background-color: #f1f1f1;
    padding: 10px;
    border-radius: 5px;
    margin-top: 5px;
    margin-bottom: 10px;
}
.city-card {
    background-color: #fff;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    transition: transform 0.3s;
}
.city-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 5px 15px rgba(0,0,0,0.15);
}
.city-name {
    font-size: 22px;
    font-weight: bold;
    margin-bottom: 10px;
    color: #333;
}
.waste-index {
    font-size: 16px;
    margin-bottom: 15px;
}
.city-stats {
    display: flex;
    justify-content: space-between;
}
.stat-item {
    text-align: center;
}
.stat-value {
    font-size: 24px;
    font-weight: bold;
    color: #2196F3;
}
.stat-label {
    font-size: 14px;
    color: #666;
}
.vote-button {
    width: 100%;
    background-color: #4CAF50;
    color: white;
    border: none;
    padding: 10px;
    border-radius: 5px;
    cursor: pointer;
    margin-top: 10px;
    font-size: 16px;
    transition: background-color 0.3s;
}
.vote-button:hover {
    background-color: #388E3C;
}
.voted {
    background-color: #81C784;
}
</style>
"""

# Admin panel CSS
admin_css = """
<style>
.admin-container {
    padding: 20px;
    border: 1px solid #e1e4e8;
    border-radius: 5px;
    margin-top: 20px;
    background-color: #f6f8fa;
}
.admin-header {
    color: #24292e;
    margin-bottom: 15px;
}
.admin-button {
    background-color: #28a745;
    color: white;
    border: none;
    padding: 10px 15px;
    border-radius: 5px;
    cursor: pointer;
    text-align: center;
    display: inline-block;
    text-decoration: none;
    font-size: 16px;
}
.admin-button:hover {
    background-color: #22863a;
}
.admin-form {
    margin-bottom: 20px;
    padding: 15px;
    border: 1px solid #d1d5da;
    border-radius: 5px;
    background-color: white;
}
.admin-form label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
}
.admin-form input[type="text"],
.admin-form input[type="password"],
.admin-form input[type="number"],
.admin-form select {
    width: 100%;
    padding: 8px;
    margin-bottom: 10px;
    border: 1px solid #d1d5da;
    border-radius: 3px;
    box-sizing: border-box;
}
.admin-message.success {
    color: green;
    margin-top: 10px;
}
.admin-message.error {
    color: red;
    margin-top: 10px;
}
.report-actions button {
    background-color: #007bff;
    color: white;
    border: none;
    padding: 5px 10px;
    border-radius: 3px;
    cursor: pointer;
    margin-right: 5px;
    font-size: 14px;
}
.report-actions button:hover {
    background-color: #0056b3;
}
.report-actions .resolve {
    background-color: #28a745;
}
.report-actions .resolve:hover {
    background-color: #1e7e34;
}
.report-actions .bbmp {
    background-color: #ffc107;
    color: #212529;
}
.report-actions .bbmp:hover {
    background-color: #e0a800;
}
.report-actions .delete {
    background-color: #dc3545;
}
.report-actions .delete:hover {
    background-color: #c82333;
}
</style>
"""

# Public waste reports CSS
public_reports_css = """
<style>
.report-card {
    background-color: #f8f9fa;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 20px;
    border-left: 5px solid #4CAF50;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}
.report-title {
    font-size: 20px;
    font-weight: bold;
    color: #2c3e50;
    margin-bottom: 8px;
}
.report-location {
    color: #34495e;
    font-size: 16px;
    margin-bottom: 10px;
}
.report-metadata {
    display: flex;
    flex-wrap: wrap;
    gap: 15px;
    margin-bottom: 15px;
    font-size: 14px;
    color: #555;
}
.report-description {
    background-color: white;
    padding: 15px;
    border-radius: 5px;
    margin-bottom: 15px;
    border-left: 3px solid #ddd;
}
.tag {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 15px;
    font-size: 12px;
    font-weight: bold;
    margin-right: 8px;
}
.bbmp-tag {
    background-color: #3498db;
    color: white;
}
.resolved-tag {
    background-color: #2ecc71;
    color: white;
}
.pending-tag {
    background-color: #f39c12;
    color: white;
}
.severity-indicator {
    display: inline-flex;
    align-items: center;
}
.severity-dot {
    height: 10px;
    width: 10px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 3px;
}
.upvote-btn {
    background-color: #f1f1f1;
    border: none;
    border-radius: 20px;
    padding: 5px 15px;
    cursor: pointer;
    transition: background-color 0.3s;
}
.upvote-btn:hover {
    background-color: #e1e1e1;
}
.comment-box {
    background-color: #f1f1f1;
    padding: 10px 15px;
    border-radius: 8px;
    margin-bottom: 10px;
}
.filter-container {
    background-color: white;
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.section-header {
    margin-top: 30px;
    margin-bottom: 20px;
    color: #2c3e50;
    border-bottom: 2px solid #4CAF50;
    padding-bottom: 10px;
}
</style>
"""