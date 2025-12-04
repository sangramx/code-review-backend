from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime
import re

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Simple in-memory storage for demo (use database in production)
reviews = []

def analyze_code_simple(code, language):
    """
    Simple rule-based code analysis (no API needed for MVP)
    You can replace this with OpenAI API later
    """
    issues = []
    suggestions = []
    score = 100
    
    # Basic checks
    lines = code.split('\n')
    
    # Check 1: Code length
    if len(lines) > 200:
        issues.append({
            'severity': 'warning',
            'line': None,
            'message': 'File is quite large. Consider breaking it into smaller modules.'
        })
        score -= 5
    
    # Check 2: Long lines
    long_lines = [i+1 for i, line in enumerate(lines) if len(line) > 100]
    if long_lines:
        issues.append({
            'severity': 'info',
            'line': long_lines[0],
            'message': f'Lines {", ".join(map(str, long_lines[:3]))} exceed 100 characters. Consider breaking them up.'
        })
        score -= 3
    
    # Check 3: Python-specific checks
    if language.lower() == 'python':
        # Check for print statements (should use logging)
        print_lines = [i+1 for i, line in enumerate(lines) if 'print(' in line]
        if print_lines:
            issues.append({
                'severity': 'info',
                'line': print_lines[0],
                'message': 'Consider using logging instead of print statements for production code.'
            })
        
        # Check for exception handling
        if 'try:' not in code:
            suggestions.append({
                'category': 'Error Handling',
                'message': 'Consider adding try-except blocks for robust error handling.'
            })
            score -= 5
        
        # Check for docstrings
        if '"""' not in code and "'''" not in code:
            suggestions.append({
                'category': 'Documentation',
                'message': 'Add docstrings to functions and classes for better code documentation.'
            })
            score -= 5
    
    # Check 4: JavaScript/Java specific
    if language.lower() in ['javascript', 'java']:
        # Check for var usage (JS)
        if language.lower() == 'javascript' and 'var ' in code:
            issues.append({
                'severity': 'warning',
                'line': None,
                'message': 'Avoid using "var". Use "let" or "const" instead for better scoping.'
            })
            score -= 5
        
        # Check for console.log
        if 'console.log' in code:
            issues.append({
                'severity': 'info',
                'line': None,
                'message': 'Remove console.log statements before production deployment.'
            })
    
    # Check 5: Security patterns
    if 'password' in code.lower() and '=' in code:
        issues.append({
            'severity': 'critical',
            'line': None,
            'message': 'Potential hardcoded password detected. Use environment variables instead.'
        })
        score -= 20
    
    # General suggestions
    if not issues:
        suggestions.append({
            'category': 'Code Quality',
            'message': 'Code looks clean! Consider adding unit tests if not already present.'
        })
    
    suggestions.append({
        'category': 'Performance',
        'message': 'Profile your code with production data to identify bottlenecks.'
    })
    
    suggestions.append({
        'category': 'Best Practices',
        'message': 'Ensure consistent code formatting with tools like Black (Python) or Prettier (JS).'
    })
    
    return {
        'issues': issues,
        'suggestions': suggestions,
        'score': max(score, 0),
        'summary': f'Found {len(issues)} issues. Code quality score: {max(score, 0)}/100'
    }

@app.route('/')
def home():
    return jsonify({
        'message': 'AI Code Review API',
        'version': '1.0',
        'endpoints': {
            '/api/review': 'POST - Submit code for review',
            '/api/history': 'GET - Get review history'
        }
    })

@app.route('/api/review', methods=['POST'])
def review_code():
    try:
        data = request.get_json()
        
        # Validate input
        if not data or 'code' not in data:
            return jsonify({'error': 'Code is required'}), 400
        
        code = data.get('code', '')
        language = data.get('language', 'python')
        
        if len(code.strip()) == 0:
            return jsonify({'error': 'Code cannot be empty'}), 400
        
        if len(code) > 10000:
            return jsonify({'error': 'Code is too large (max 10,000 characters)'}), 400
        
        # Analyze code
        analysis = analyze_code_simple(code, language)
        
        # Store review (for history feature)
        review_entry = {
            'id': len(reviews) + 1,
            'timestamp': datetime.now().isoformat(),
            'language': language,
            'code_length': len(code),
            'score': analysis['score'],
            'issues_count': len(analysis['issues'])
        }
        reviews.append(review_entry)
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'timestamp': review_entry['timestamp']
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    try:
        # Return last 10 reviews
        return jsonify({
            'success': True,
            'reviews': reviews[-10:][::-1]  # Last 10, reversed
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        if not reviews:
            return jsonify({
                'success': True,
                'stats': {
                    'total_reviews': 0,
                    'avg_score': 0,
                    'total_issues': 0
                }
            })
        
        total_reviews = len(reviews)
        avg_score = sum(r['score'] for r in reviews) / total_reviews
        total_issues = sum(r['issues_count'] for r in reviews)
        
        return jsonify({
            'success': True,
            'stats': {
                'total_reviews': total_reviews,
                'avg_score': round(avg_score, 1),
                'total_issues': total_issues
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)