from flask import Flask, render_template, request, redirect, url_for
import random

app = Flask(__name__)

users = []

def generate_lotto_numbers():
    return sorted(random.sample(range(1, 46), 6))

def check_match(winning_numbers, user_numbers):
    return set(winning_numbers) == set(user_numbers)

def simulate_lotto(users):
    attempts = {user['username']: 0 for user in users}
    winning_numbers = generate_lotto_numbers()
    winners = []

    while not winners:
        for user in users:
            attempts[user['username']] += 1
            if check_match(winning_numbers, user['numbers']):
                winners.append(user['username'])
        if not winners:
            winning_numbers = generate_lotto_numbers()

    return attempts, winning_numbers, winners

@app.route('/')
def index():
    return render_template('index.html', users=users)

@app.route('/add_user', methods=['POST'])
def add_user():
    username = request.form['username']
    numbers = list(map(int, request.form['numbers'].split(',')))
    users.append({'username': username, 'numbers': numbers})
    return redirect(url_for('index'))

@app.route('/simulate')
def simulate():
    attempts, winning_numbers, winners = simulate_lotto(users)
    return render_template('results.html', attempts=attempts, winning_numbers=winning_numbers, winners=winners)

if __name__ == '__main__':
    app.run(debug=True)
