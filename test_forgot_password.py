import requests

def test_forgot_password():
    url = "https://ems-w82z.onrender.com/api/users/forgot-password/"
    data = {"email": "chihajihed3@gmail.com"}
    
    try:
        print(f"Calling {url} for {data['email']}...")
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_forgot_password()
